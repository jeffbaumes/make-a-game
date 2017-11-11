import pickle
import sqlite3
import pygame
import math
from opensimplex import OpenSimplex
from .constants import (
    CHUNK_SIZE,
    TILE_SIZE,
    MAX_SPEED,
    MAX_SPRINT,
    NOISE_SCALE,
    MATERIAL_SCALE
)

_db = None
_noise = None
_username = None


class Chunk:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy

        self.material = []
        for x in range(CHUNK_SIZE):
            row = []
            for y in range(CHUNK_SIZE):
                nx = (CHUNK_SIZE * cx + x) / MATERIAL_SCALE
                ny = (CHUNK_SIZE * cy + y) / MATERIAL_SCALE
                value = 1 if _noise.noise2d(x=nx, y=ny) > 0.5 else 0
                row.append(value)
            self.material.append(row)

        self.noise = []
        for x in range(CHUNK_SIZE):
            row = []
            for y in range(CHUNK_SIZE):
                nx = (CHUNK_SIZE * cx + x) / NOISE_SCALE
                ny = (CHUNK_SIZE * cy + y) / NOISE_SCALE
                value = math.floor(20 * _noise.noise2d(x=nx, y=ny))
                row.append(value)
            self.noise.append(row)

    def cell(self, x, y):
        cellx = x % CHUNK_SIZE
        celly = y % CHUNK_SIZE
        return (self.material[cellx][celly], self.noise[cellx][celly])

    def setMaterial(self, x, y, m):
        cellx = x % CHUNK_SIZE
        celly = y % CHUNK_SIZE
        self.material[cellx][celly] = m


class World:
    def __init__(self):
        pass

    def chunk(self, x, y):
        cx = math.floor(x / CHUNK_SIZE)
        cy = math.floor(y / CHUNK_SIZE)
        cur = _db.cursor()
        cq = cur.execute(
            'SELECT data FROM chunk WHERE x = ? AND y = ?', (cx, cy))
        cdata = cq.fetchone()
        if cdata:
            return pickle.loads(bytes(cdata[0]))
        ch = Chunk(cx, cy)
        self.saveChunk(ch)
        return ch

    def saveChunk(self, c):
        cdata = pickle.dumps(c, pickle.HIGHEST_PROTOCOL)
        cur = _db.cursor()
        cur.execute(
            'INSERT INTO chunk (x, y, data) VALUES (?, ?, ?)',
            (c.cx, c.cy, sqlite3.Binary(cdata)))
        _db.commit()

    def updateChunk(self, c):
        cdata = pickle.dumps(c, pickle.HIGHEST_PROTOCOL)
        cur = _db.cursor()
        cur.execute(
            'UPDATE chunk SET data = ? WHERE x = ? AND y = ?',
            (sqlite3.Binary(cdata), c.cx, c.cy))
        _db.commit()


class WorldCache:
    def __init__(self, world):
        self.world = world
        self.chunks = {}

    def chunk(self, x, y):
        cx = math.floor(x / CHUNK_SIZE)
        cy = math.floor(y / CHUNK_SIZE)
        if not self.chunks.get(cx):
            self.chunks[cx] = {}
        if not self.chunks[cx].get(cy):
            self.chunks[cx][cy] = self.world.chunk(cx, cy)
        return self.chunks[cx][cy]

    def cell(self, x, y):
        return self.chunk(x, y).cell(x, y)

    def setMaterial(self, x, y, m):
        c = self.chunk(x, y)
        c.setMaterial(x, y, m)
        self.world.updateChunk(c)


def createScreen(x, y):
    return pygame.display.set_mode((x, y), pygame.RESIZABLE)


def gameLoop():
    pygame.init()
    pygame.font.init()
    myfont = pygame.font.SysFont('Comic Sans MS', 30)
    sizex = 800
    sizey = 800
    screen = None
    done = False
    screen = createScreen(sizex, sizey)
    w = World()
    world = WorldCache(w)

    clock = pygame.time.Clock()

    mx = 0
    my = 0
    c = _db.cursor()
    c.execute('SELECT * FROM user WHERE name = ?', (_username,))
    s = c.fetchone()
    if s:
        mx = s['x']
        my = s['y']
    else:
        c.execute(
            'INSERT INTO user (name, x, y) VALUES (?,?,?)',
            (_username, 0, 0))
        _db.commit()

    vx = 0
    vy = 0

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                c.execute(
                    'UPDATE user SET x = ?, y = ? WHERE name = ?',
                    (mx, my, _username))
                _db.commit()
                done = True
            if event.type == pygame.VIDEORESIZE:
                sizex = event.w
                sizey = event.h
                screen = createScreen(sizex, sizey)

        pressed = pygame.key.get_pressed()
        speedlimit = MAX_SPEED
        if pressed[pygame.K_LSHIFT]:
            speedlimit = MAX_SPRINT

        if pressed[pygame.K_UP]:
            if vy >= -speedlimit:
                vy -= 0.02
        if pressed[pygame.K_DOWN]:
            if vy <= speedlimit:
                vy += 0.02
        if pressed[pygame.K_LEFT]:
            if vx >= -speedlimit:
                vx -= 0.02
        if pressed[pygame.K_RIGHT]:
            if vx <= speedlimit:
                vx += 0.02

        if abs(vx) < 0.02:
            vx = 0
        if vx < -speedlimit:
            vx = -speedlimit
        if vx > speedlimit:
            vx = speedlimit
        if vx > 0 and not pressed[pygame.K_RIGHT]:
            vx -= 0.02
        if vx < 0 and not pressed[pygame.K_LEFT]:
            vx += 0.02

        if abs(vy) < 0.02:
            vy = 0
        if vy < -speedlimit:
            vy = -speedlimit
        if vy > speedlimit:
            vy = speedlimit
        if vy > 0 and not pressed[pygame.K_DOWN]:
            vy -= 0.02
        if vy < 0 and not pressed[pygame.K_UP]:
            vy += 0.02

        mx += vx
        my += vy

        halfX = math.floor(0.6 * sizex / TILE_SIZE)
        halfY = math.floor(0.6 * sizey / TILE_SIZE)
        nearestX = round(mx - 0.5)
        nearestY = round(my - 0.5)

        if pressed[pygame.K_SPACE]:
            world.setMaterial(nearestX, nearestY, 1)

        for x in range(-halfX, halfX + 1):
            for y in range(-halfY, halfY + 1):
                (material, delta) = world.cell(nearestX + x, nearestY + y)
                color = [180, 180, 180] if material else [50, 200, 50]
                color[0] += delta
                color[1] += delta
                color[2] += delta
                # If mx is at sizex / 2,
                # nearestX is at (nearestX - mx)*TILE_SIZE + sizex / 2.
                pygame.draw.rect(
                    screen, color,
                    pygame.Rect(
                        (nearestX + x - mx)*TILE_SIZE + sizex / 2,
                        (nearestY + y - my)*TILE_SIZE + sizey / 2,
                        TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(
            screen, (0, 0, 0),
            pygame.Rect(
                sizex / 2 - TILE_SIZE / 4,
                sizey / 2 - TILE_SIZE / 4,
                TILE_SIZE / 2, TILE_SIZE / 2))
        x = myfont.render(str(round(mx)), False, (0, 0, 0))
        y = myfont.render(str(round(my)), False, (0, 0, 0))
        x2 = myfont.render("X:", False, (0, 0, 0))
        y2 = myfont.render("Y:", False, (0, 0, 0))

        screen.blit(x, (35, 0))
        screen.blit(x2, (0, 0))
        screen.blit(y, (35, 25))
        screen.blit(y2, (0, 25))
        pygame.display.flip()
        clock.tick(60)


def startGame(world, seed, username):
    global _db
    global _noise
    global _username

    _username = username

    dbName = world + '.db'
    _db = sqlite3.connect(dbName)
    _db.row_factory = sqlite3.Row

    c = _db.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS setting
        (name TEXT PRIMARY KEY, val TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chunk
        (x INT, y INT, data TEXT, PRIMARY KEY (x, y))''')
    c.execute('''CREATE TABLE IF NOT EXISTS user
        (name TEXT PRIMARY KEY, x REAL, y REAL)''')
    _db.commit()

    c.execute('SELECT val FROM setting WHERE name = "seed"')
    s = c.fetchone()
    if s:
        seed = int(s[0])
    else:
        c.execute('INSERT INTO setting VALUES ("seed",?)', (str(seed),))
        _db.commit()

    _noise = OpenSimplex(seed=seed)
    gameLoop()
