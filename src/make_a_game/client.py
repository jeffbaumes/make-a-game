import pygame
import math
from .game import game
from .blocks import (
    GRASS,
    STONE,
    BEDROCK
)
from .constants import (
    CHUNK_SIZE,
    DESIRED_FPS,
    USER_SIZE,
    TILE_SIZE,
    MAX_SPEED,
    MAX_SPRINT
)
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.protocols import amp
from twisted.internet.task import LoopingCall
from .commands import (
    GetChunk,
    UpdateMaterial,
    UpdateUserPosition
)
import jsonpickle


class MulticastPingClient(DatagramProtocol):

    def startProtocol(self):
        # Join the multicast address, so we can receive replies:
        self.transport.joinGroup("228.0.0.5")
        # Send to 228.0.0.5:8005 - all listeners on the multicast address
        # (including us) will receive this message.
        self.transport.write(b'Client: Ping', ("228.0.0.5", 8005))

    def datagramReceived(self, datagram, address):
        print("Datagram %s received from %s" % (repr(datagram), repr(address)))


class GameClient(amp.AMP):
    def updateMaterial(self, x, y, material):
        game.world.setMaterial(x, y, material)
        return {'result': True}
    UpdateMaterial.responder(updateMaterial)

    def updateUserPosition(self, user, x, y):
        game.playerPositions[user] = (x, y)
        return {'result': True}
    UpdateUserPosition.responder(updateUserPosition)


class WorldCache:
    def __init__(self):
        self.chunks = {}

    def chunk(self, x, y):
        cx = math.floor(x / CHUNK_SIZE)
        cy = math.floor(y / CHUNK_SIZE)
        if not self.chunks.get(cx):
            self.chunks[cx] = {}
        if not self.chunks[cx].get(cy) or self.chunks[cx][cy] == 'pending':
            if not self.chunks[cx].get(cy):

                def receivedChunk(result):
                    self.chunks[cx][cy] = jsonpickle.decode(result['chunk'])
                d = game.protocol.callRemote(GetChunk, x=x, y=y)
                d.addCallback(receivedChunk)
                self.chunks[cx][cy] = 'pending'

            return None
        return self.chunks[cx][cy]

    def cell(self, x, y):
        c = self.chunk(x, y)
        if c:
            return c.cell(x, y)
        return (1, 0)

    def updateMaterial(self, x, y, m):
        if self.cell(x, y)[0] == m:
            return
        self.setMaterial(x, y, m)

        def updatedMaterial(result):
            pass
        d = game.protocol.callRemote(
            UpdateMaterial, x=x, y=y, material=m)
        d.addCallback(updatedMaterial)

    def setMaterial(self, x, y, m):
        c = self.chunk(x, y)
        if c:
            c.setMaterial(x, y, m)


def createScreen(x, y):
    return pygame.display.set_mode((x, y), pygame.RESIZABLE)


def pixelToGame(pt):
    x = (pt[0] - game.sizex / 2.0) / TILE_SIZE + game.mx
    y = (pt[1] - game.sizey / 2.0) / TILE_SIZE + game.my
    return (x, y)


def gameToPixel(pt):
    x = (pt[0] - game.mx) * TILE_SIZE + game.sizex / 2.0
    y = (pt[1] - game.my) * TILE_SIZE + game.sizey / 2.0
    return (x, y)


def play():
    game.startScreenLoop.stop()
    if game.host == '__builtin__':
        # Start a server as a subprocess
        import subprocess
        import time
        import sys
        serverProc = subprocess.Popen([
            'make-a-game-server',
            '--world', game.worldName,
            '--seed', str(game.seed),
            '--port', str(game.port)
        ], stdout=sys.stdout, stderr=sys.stderr)
        time.sleep(1)

        import atexit
        def doExit():
            print('Stopping server...')
            serverProc.terminate()
        atexit.register(doExit)

    #pygame.event.set_grab(True)
    #pygame.mouse.set_visible(False)
    game.font = pygame.font.SysFont('Comic Sans MS', 30)
    game.screen = createScreen(game.sizex, game.sizey)
    game.world = WorldCache()
    if game.host == '__builtin__':
        connectionHost = 'localhost'
    else:
        connectionHost = game.host
    game.server = TCP4ClientEndpoint(reactor, connectionHost, game.port)

    def connected(ampProto):
        game.protocol = ampProto
        # Set up a looping call every 1/30th of a second to run your game tick
        tick = LoopingCall(gameTick)
        tick.start(1.0 / DESIRED_FPS)
    connectProtocol(game.server, GameClient()).addCallback(connected)


def gamestart():
    import sys
    import os
    game.screen = createScreen(game.sizex, game.sizey)
    mouse = pygame.mouse.get_pos()
    clicked = False
    #grab = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            reactor.stop()
        if event.type == pygame.VIDEORESIZE:
            game.sizex = event.w
            game.sizey = event.h
            game.screen = createScreen(game.sizex, game.sizey)
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked = True
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imgs')
    if game.screen_number == 0:
        multiplayer_pressedImg = pygame.image.load(os.path.join(path, 'multiplayer_pressed.png'))
        multiplayerImg = pygame.image.load(os.path.join(path, 'multiplayer.png'))
        bg = pygame.image.load(os.path.join(path, 'backround.png'))
        playImg = pygame.image.load(os.path.join(path, 'PLAY.png'))
        playpressedImg = pygame.image.load(path, 'PLAY_pressed.png'))
        game.screen.blit(pygame.transform.scale(bg, (game.sizex, game.sizey)), (0, 0))
        button1Rect = pygame.Rect((0, 0), playImg.get_size())
        button2Rect = pygame.Rect((0, 0), multiplayerImg.get_size())
        button1Rect.center = (game.sizex/2, game.sizey/2)
        button2Rect.center = (game.sizex/2, game.sizey/2+70)
        if button1Rect.collidepoint(mouse):
            game.screen.blit(playpressedImg, button1Rect.topleft)
            if clicked:
                game.screen_number = "singlplayer"
                play()
        else:
            game.screen.blit(playImg, button1Rect.topleft)
        if button2Rect.collidepoint(mouse):
            game.screen.blit(multiplayer_pressedImg, button2Rect.topleft)
            if clicked:
                game.screen_number = "multiplayer"
        else:
            game.screen.blit(multiplayerImg, button2Rect.topleft)
    elif game.screen_number == "multiplayer":
        lan_bg = pygame.image.load(os.path.join(path, 'lan_backround.png'))
        game.screen.blit(pygame.transform.scale(lan_bg, (game.sizex, game.sizey)), (0, 0))

        # for name in lan_games:
        #     pass


    elif game.screen_number == "singlplayer":
        pass
    pygame.display.flip()

def gameTick():
    #grab = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            reactor.stop()
        if event.type == pygame.VIDEORESIZE:
            game.sizex = event.w
            game.sizey = event.h
            game.screen = createScreen(game.sizex, game.sizey)
        # if event.type == pygame.MOUSEBUTTONDOWN:
        #     pygame.event.set_grab(True)
        #     pygame.mouse.set_visible(False)
        #     grab = True
    pressed = pygame.key.get_pressed()
    speedlimit = MAX_SPEED
    if pressed[pygame.K_LSHIFT]:
        speedlimit = MAX_SPRINT

    if pressed[pygame.K_w]:
        if game.vy >= -speedlimit:
            game.vy -= 0.02
    if pressed[pygame.K_s]:
        if game.vy <= speedlimit:
            game.vy += 0.02
    if pressed[pygame.K_a]:
        if game.vx >= -speedlimit:
            game.vx -= 0.02
    if pressed[pygame.K_d]:
        if game.vx <= speedlimit:
            game.vx += 0.02
    # if pressed[pygame.K_ESCAPE]:
    #     pygame.event.set_grab(False)
    #     pygame.mouse.set_visible(True)
    #     grab = False
    if abs(game.vx) < 0.02:
        game.vx = 0
    if game.vx < -speedlimit:
        game.vx = -speedlimit
    if game.vx > speedlimit:
        game.vx = speedlimit
    if game.vx > 0 and not pressed[pygame.K_d]:
        game.vx -= 0.02
    if game.vx < 0 and not pressed[pygame.K_a]:
        game.vx += 0.02

    if abs(game.vy) < 0.02:
        game.vy = 0
    if game.vy < -speedlimit:
        game.vy = -speedlimit
    if game.vy > speedlimit:
        game.vy = speedlimit
    if game.vy > 0 and not pressed[pygame.K_s]:
        game.vy -= 0.02
    if game.vy < 0 and not pressed[pygame.K_w]:
        game.vy += 0.02

    userSize = float(USER_SIZE) / TILE_SIZE

    nx = math.floor(game.mx)
    ny = math.floor(game.my)

    minX = game.mx - 1
    maxX = game.mx + 1
    minY = game.my - 1
    maxY = game.my + 1
    if (game.world.cell(nx - 1, ny)[0] or
            game.my - ny < userSize / 2 and game.world.cell(nx - 1, ny - 1)[0] or
            game.my - ny > 1 - userSize / 2 and game.world.cell(nx - 1, ny + 1)[0]):
        minX = nx + userSize / 2
    if (game.world.cell(nx + 1, ny)[0] or
            game.my - ny < userSize / 2 and game.world.cell(nx + 1, ny - 1)[0] or
            game.my - ny > 1 - userSize / 2 and game.world.cell(nx + 1, ny + 1)[0]):
        maxX = nx + 1 - userSize / 2

    if (game.world.cell(nx, ny - 1)[0] or
            game.mx - nx < userSize / 2 and game.world.cell(nx - 1, ny - 1)[0] or
            game.mx - nx > 1 - userSize / 2 and game.world.cell(nx + 1, ny - 1)[0]):
        minY = ny + userSize / 2
    if (game.world.cell(nx, ny + 1)[0] or
            game.mx - nx < userSize / 2 and game.world.cell(nx - 1, ny + 1)[0] or
            game.mx - nx > 1 - userSize / 2 and game.world.cell(nx + 1, ny + 1)[0]):
        maxY = ny + 1 - userSize / 2

    game.mx += game.vx
    game.my += game.vy

    game.mx = min(maxX, max(minX, game.mx))
    game.my = min(maxY, max(minY, game.my))

    game.protocol.callRemote(UpdateUserPosition, user=game.username, x=game.mx, y=game.my)

    halfX = math.floor(0.6 * game.sizex / TILE_SIZE)
    halfY = math.floor(0.6 * game.sizey / TILE_SIZE)

    px, py = pygame.mouse.get_pos()
    px = max(px, game.sizex / 2.0 - 3.0 * TILE_SIZE)
    px = min(px, game.sizex / 2.0 + 3.0 * TILE_SIZE)
    py = max(py, game.sizey / 2.0 - 3.0 * TILE_SIZE)
    py = min(py, game.sizey / 2.0 + 3.0 * TILE_SIZE)
    if pygame.event.get_grab():
        pygame.mouse.set_pos((px, py))
    oxRaw, oyRaw = pixelToGame((px, py))
    ox = math.floor(oxRaw)
    oy = math.floor(oyRaw)
    if pressed[pygame.K_1]:
        game.slotMaterial = 1
    if pressed[pygame.K_2]:
        game.slotMaterial = 2

    if pressed[pygame.K_SPACE]:
        game.world.updateMaterial(ox, oy, game.slotMaterial)

    if pressed[pygame.K_b]:
        game.world.updateMaterial(ox, oy, 0)

    for x in range(-halfX, halfX + 1):
        for y in range(-halfY, halfY + 1):
            (material, delta) = game.world.cell(nx + x, ny + y)
            if material == 0:
                color = list(GRASS)
            elif material == 1:
                color = list(STONE)
            elif material == 2:
                color = list(BEDROCK)
            for i in range(3):
                color[i] += delta
                color[i] = min(255, max(0, color[i]))
            tx, ty = gameToPixel((nx + x, ny + y))
            pygame.draw.rect(
                game.screen, color,
                pygame.Rect(tx, ty, TILE_SIZE, TILE_SIZE))
    ux, uy = gameToPixel((game.mx, game.my))
    pygame.draw.rect(
        game.screen, (0, 0, 0),
        pygame.Rect(
            ux - USER_SIZE / 2.0,
            uy - USER_SIZE / 2.0,
            USER_SIZE, USER_SIZE))

    for user, pos in game.playerPositions.items():
        if user != game.username:
            playerX, playerY = gameToPixel(pos)
            pygame.draw.rect(
                game.screen, (200, 0, 0),
                pygame.Rect(
                    playerX - USER_SIZE / 2,
                    playerY - USER_SIZE / 2,
                    USER_SIZE, USER_SIZE))
    boxX, boxY = gameToPixel((ox, oy))
    pygame.draw.rect(
        game.screen, (0, 0, 0),
        pygame.Rect(
            boxX, boxY,
            TILE_SIZE, TILE_SIZE
        ), 1)
    pygame.draw.line(
        game.screen, (0, 0, 0),
        (px - 4, py),
        (px + 4, py))
    pygame.draw.line(
        game.screen, (0, 0, 0),
        (px, py - 4),
        (px, py + 4))

    x = game.font.render(str(round(game.mx)), False, (0, 0, 0))
    y = game.font.render(str(round(game.my)), False, (0, 0, 0))
    x2 = game.font.render("X:", False, (0, 0, 0))
    y2 = game.font.render("Y:", False, (0, 0, 0))

    game.screen.blit(x, (35, 0))
    game.screen.blit(x2, (0, 0))
    game.screen.blit(y, (35, 25))
    game.screen.blit(y2, (0, 25))
    pygame.display.flip()


def startGame(username, host, port, world, seed):
    from twisted.python.log import startLogging
    from sys import stdout

    startLogging(stdout)

    game.username = username
    game.host = host
    game.port = port
    game.worldName = world
    game.seed = seed

    pygame.init()
    pygame.font.init()
    game.sizex = 500
    game.sizey = 500
    game.startScreenLoop = LoopingCall(gamestart)
    game.startScreenLoop.start(1.0 / DESIRED_FPS)

    reactor.listenMulticast(8005, MulticastPingClient(), listenMultiple=True)
    reactor.run()
