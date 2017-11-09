import sqlite3
import pygame
from opensimplex import OpenSimplex
from .constants import CHUNK_SIZE, TILE_SIZE

_db = None
_noise = None


# def initGame(db, seed, x, y):
#     load_area(x, y)
#     chunk = (int(x / CHUNK_SIZE), int(y / CHUNK_SIZE))


def gameLoop():
    pygame.init()
    sizex = 800
    sizey = 800
    screen = pygame.display.set_mode((sizex, sizey), pygame.RESIZABLE)
    done = False

    clock = pygame.time.Clock()
    mx = 0
    my = 0
    vx = 0
    vy = 0

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.VIDEORESIZE:
                sizex = event.w
                sizey = event.h
                screen = pygame.display.set_mode((sizex,sizey),pygame.RESIZABLE)


            # if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            #     is_blue = not is_blue

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_UP]:
            vy -= 0.1
        if pressed[pygame.K_DOWN]:
            vy += 0.1
        if pressed[pygame.K_LEFT]:
            vx -= 0.1
        if pressed[pygame.K_RIGHT]:
            vx += 0.1

        if abs(vx) < 0.02:
            vx = 0
        elif vx > 0:
            vx -= 0.05
        else:
            vx += 0.05

        if abs(vy) < 0.02:
            vy = 0
        elif vy > 0:
            vy -= 0.05
        else:
            vy += 0.05

        mx += vx
        my += vy

        halfX = int(0.6 * sizex / TILE_SIZE)
        halfY = int(0.6 * sizey / TILE_SIZE)
        nearestX = round(mx)
        nearestY = round(my)

        for x in range(-halfX, halfX + 1):
            for y in range(-halfY, halfY + 1):
                n = _noise.noise2d(x=(nearestX + x)/10, y=(nearestY + y)/10)
                color = [50, 200, 50]
                # color = [50, 50, 50] if n < 0 else [50, 200, 50]
                delta = int(20 * _noise.noise2d(x=(nearestX + x)/5, y=(nearestY + y)/5))
                color[0] += delta
                color[1] += delta
                color[2] += delta
                pygame.draw.rect(
                    screen, color,
                    pygame.Rect(
                        (nearestX + x - mx)*TILE_SIZE + sizex / 2,
                        (nearestY + y - my)*TILE_SIZE + sizey / 2,
                        TILE_SIZE, TILE_SIZE))

        # (mx, my) is at (sizex / 2, sizey / 2)
        # (nearestX, nearestY) is at ((nearestX - mx)*TILE_SIZE + sizex / 2, ?)

        pygame.display.flip()
        clock.tick(60)


def startGame(world, seed):
    global _db
    global _noise

    dbName = world + '.db'
    _db = sqlite3.connect(dbName)
    c = _db.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS settings
        (name VARCHAR PRIMARY KEY, val VARCHAR)''')
    _db.commit()
    c.execute('SELECT val FROM settings WHERE name = "seed"')
    s = c.fetchone()
    if s:
        seed = int(s[0])
    else:
        c.execute('INSERT INTO settings VALUES ("seed",?)', (str(seed),))
        _db.commit()
    _noise = OpenSimplex(seed=seed)
    print(seed)
    gameLoop()
