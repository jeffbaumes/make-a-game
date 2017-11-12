import pygame
import math
from .constants import (
    CHUNK_SIZE,
    USER_SIZE,
    TILE_SIZE,
    MAX_SPEED,
    MAX_SPRINT
)
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.protocols import amp
from twisted.internet.task import LoopingCall
from .commands import (
    GetChunk,
    UpdateMaterial
)
import jsonpickle


_server = None
_protocol = None
_deferred = None
_username = None
_mx = 0
_my = 0
_vx = 0
_vy = 0
_myfont = None
_sizex = 800
_sizey = 800
_screen = None
_world = None


class GameClient(amp.AMP):
    def updateMaterial(self, x, y, material):
        _world.setMaterial(x, y, material)
        return {'result': True}
    UpdateMaterial.responder(updateMaterial)


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
                d = _protocol.callRemote(GetChunk, x=x, y=y)
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
        def updatedMaterial(result):
            pass
        d = _protocol.callRemote(
            UpdateMaterial, x=x, y=y, material=m)
        d.addCallback(updatedMaterial)

    def setMaterial(self, x, y, m):
        c = self.chunk(x, y)
        if c:
            c.setMaterial(x, y, m)


def createScreen(x, y):
    return pygame.display.set_mode((x, y), pygame.RESIZABLE)


def gameTick():
    global _mx
    global _my
    global _vx
    global _vy
    global _world
    global _sizex
    global _sizey
    global _screen

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            reactor.stop()
            # c.execute(
            #     'UPDATE user SET x = ?, y = ? WHERE name = ?',
            #     (_mx, _my, _username))
            # _db.commit()
        if event.type == pygame.VIDEORESIZE:
            _sizex = event.w
            _sizey = event.h
            _screen = createScreen(_sizex, _sizey)

    pressed = pygame.key.get_pressed()
    speedlimit = MAX_SPEED
    if pressed[pygame.K_LSHIFT]:
        speedlimit = MAX_SPRINT

    if pressed[pygame.K_UP]:
        if _vy >= -speedlimit:
            _vy -= 0.02
    if pressed[pygame.K_DOWN]:
        if _vy <= speedlimit:
            _vy += 0.02
    if pressed[pygame.K_LEFT]:
        if _vx >= -speedlimit:
            _vx -= 0.02
    if pressed[pygame.K_RIGHT]:
        if _vx <= speedlimit:
            _vx += 0.02

    if abs(_vx) < 0.02:
        _vx = 0
    if _vx < -speedlimit:
        _vx = -speedlimit
    if _vx > speedlimit:
        _vx = speedlimit
    if _vx > 0 and not pressed[pygame.K_RIGHT]:
        _vx -= 0.02
    if _vx < 0 and not pressed[pygame.K_LEFT]:
        _vx += 0.02

    if abs(_vy) < 0.02:
        _vy = 0
    if _vy < -speedlimit:
        _vy = -speedlimit
    if _vy > speedlimit:
        _vy = speedlimit
    if _vy > 0 and not pressed[pygame.K_DOWN]:
        _vy -= 0.02
    if _vy < 0 and not pressed[pygame.K_UP]:
        _vy += 0.02

    userSize = float(USER_SIZE) / TILE_SIZE

    nx = math.floor(_mx)
    ny = math.floor(_my)

    minX = _mx - 1
    maxX = _mx + 1
    minY = _my - 1
    maxY = _my + 1
    if (_world.cell(nx - 1, ny)[0] or
            _my - ny < userSize / 2 and _world.cell(nx - 1, ny - 1)[0] or
            _my - ny > 1 - userSize / 2 and _world.cell(nx - 1, ny + 1)[0]):
        minX = nx + userSize / 2
    if (_world.cell(nx + 1, ny)[0] or
            _my - ny < userSize / 2 and _world.cell(nx + 1, ny - 1)[0] or
            _my - ny > 1 - userSize / 2 and _world.cell(nx + 1, ny + 1)[0]):
        maxX = nx + 1 - userSize / 2

    if (_world.cell(nx, ny - 1)[0] or
            _mx - nx < userSize / 2 and _world.cell(nx - 1, ny - 1)[0] or
            _mx - nx > 1 - userSize / 2 and _world.cell(nx + 1, ny - 1)[0]):
        minY = ny + userSize / 2
    if (_world.cell(nx, ny + 1)[0] or
            _mx - nx < userSize / 2 and _world.cell(nx - 1, ny + 1)[0] or
            _mx - nx > 1 - userSize / 2 and _world.cell(nx + 1, ny + 1)[0]):
        maxY = ny + 1 - userSize / 2

    _mx += _vx
    _my += _vy

    _mx = min(maxX, max(minX, _mx))
    _my = min(maxY, max(minY, _my))

    halfX = math.floor(0.6 * _sizex / TILE_SIZE)
    halfY = math.floor(0.6 * _sizey / TILE_SIZE)

    if pressed[pygame.K_SPACE]:
        _world.updateMaterial(nx, ny, 1)

    if pressed[pygame.K_b]:
        _world.updateMaterial(nx, ny, 0)

    for x in range(-halfX, halfX + 1):
        for y in range(-halfY, halfY + 1):
            (material, delta) = _world.cell(nx + x, ny + y)
            color = [180, 180, 180] if material else [50, 200, 50]
            color[0] += delta
            color[1] += delta
            color[2] += delta
            # If _mx is at _sizex / 2,
            # nx is at (nx - _mx)*TILE_SIZE + _sizex / 2.
            pygame.draw.rect(
                _screen, color,
                pygame.Rect(
                    (nx + x - _mx)*TILE_SIZE + _sizex / 2,
                    (ny + y - _my)*TILE_SIZE + _sizey / 2,
                    TILE_SIZE, TILE_SIZE))
    pygame.draw.rect(
        _screen, (0, 0, 0),
        pygame.Rect(
            _sizex / 2 - USER_SIZE / 2,
            _sizey / 2 - USER_SIZE / 2,
            USER_SIZE, USER_SIZE))
    x = _myfont.render(str(round(_mx)), False, (0, 0, 0))
    y = _myfont.render(str(round(_my)), False, (0, 0, 0))
    x2 = _myfont.render("X:", False, (0, 0, 0))
    y2 = _myfont.render("Y:", False, (0, 0, 0))

    _screen.blit(x, (35, 0))
    _screen.blit(x2, (0, 0))
    _screen.blit(y, (35, 25))
    _screen.blit(y2, (0, 25))
    pygame.display.flip()


def startGame(username, port):
    from twisted.python.log import startLogging
    from sys import stdout

    startLogging(stdout)

    global _username
    global _server
    global _protocol
    global _deferred
    global _myfont
    global _screen
    global _world

    DESIRED_FPS = 30.0  # 30 frames per second

    pygame.init()
    pygame.font.init()
    _myfont = pygame.font.SysFont('Comic Sans MS', 30)
    _screen = createScreen(_sizex, _sizey)
    _world = WorldCache()

    # c = _db.cursor()
    # c.execute('SELECT * FROM user WHERE name = ?', (_username,))
    # s = c.fetchone()
    # if s:
    #     _mx = s['x']
    #     _my = s['y']
    # else:
    #     c.execute(
    #         'INSERT INTO user (name, x, y) VALUES (?,?,?)',
    #         (_username, 0, 0))
    #     _db.commit()

    _username = username
    _server = TCP4ClientEndpoint(reactor, '127.0.0.1', port)

    def connected(ampProto):
        global _protocol
        _protocol = ampProto
        # Set up a looping call every 1/30th of a second to run your game tick
        tick = LoopingCall(gameTick)
        tick.start(1.0 / DESIRED_FPS)
    connectProtocol(_server, GameClient()).addCallback(connected)

    reactor.run()
