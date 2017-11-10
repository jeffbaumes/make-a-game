import sqlite3
import pygame
from opensimplex import OpenSimplex
from .constants import CHUNK_SIZE, TILE_SIZE, MAX_SPEED, MAX_SPRINT

_db = None
_noise = None



# def initGame(db, seed, x, y):
#     load_area(x, y)
#     chunk = (int(x / CHUNK_SIZE), int(y / CHUNK_SIZE))


def gameLoop():
    pygame.init()
    pygame.font.init()
    myfont = pygame.font.SysFont('Comic Sans MS', 30)
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

        x = myfont.render(str(round(mx)), False, (0, 0, 0))
        y = myfont.render(str(round(my)), False, (0, 0, 0))
        x2 = myfont.render("X:", False, (0, 0, 0))
        y2= myfont.render("Y:", False, (0, 0, 0))

        # (mx, my) is at (sizex / 2, sizey / 2)
        # (nearestX, nearestY) is at ((nearestX - mx)*TILE_SIZE + sizex / 2, ?)
        screen.blit(x,(35,0))
        screen.blit(x2,(0,0))
        screen.blit(y,(35,25))
        screen.blit(y2,(0,25))
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
