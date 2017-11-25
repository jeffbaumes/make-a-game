from twisted.internet.protocol import DatagramProtocol
from twisted.protocols import amp
from twisted.python.log import startLogging
from twisted.internet import reactor
from twisted.internet.protocol import Factory
import sqlite3
from opensimplex import OpenSimplex
import jsonpickle
import math
from random import randint
from .constants import (
    BIOME_SCALE,
    CHUNK_SIZE,
    NOISE_SCALE,
    MATERIAL_SCALE,
    Biomes
)
from .commands import (
    GetChunk,
    UpdateChunk,
    UpdateMaterial,
    UpdateUserPosition
)
from sys import stdout

_db = None
_noise = None
_world = None


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


class MulticastPingPong(DatagramProtocol):

    def startProtocol(self):
        """
        Called after protocol has started listening.
        """
        # Set the TTL>1 so multicast will cross router hops:
        self.transport.setTTL(5)
        # Join a specific multicast group:
        self.transport.joinGroup("228.0.0.5")

    def datagramReceived(self, datagram, address):
        print("Datagram %s received from %s" % (repr(datagram), repr(address)))
        if datagram == b"Client: Ping":
            # Rather than replying to the group multicast address, we send the
            # reply directly (unicast) to the originating port:
            self.transport.write(b"Server: Pong", ("228.0.0.5", 8005))
            self.transport.write(b"Server: Pong", ("228.0.0.5", 8005))
class Chunk:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy

        nx = cx / BIOME_SCALE
        ny = cy / BIOME_SCALE
        biome = Biomes.MAZE if _noise.noise2d(x=nx, y=ny) > 0.2 else Biomes.GRASS

        if biome == Biomes.MAZE:
            self.material = []
            px = randint(0, (CHUNK_SIZE - 1 - 3)/2)*2 + 1
            py = randint(0, (CHUNK_SIZE - 1 - 3)/2)*2 + 1
            for x in range(CHUNK_SIZE):
                row = []
                for y in range(CHUNK_SIZE):
                    if x == 0 and y != py:
                        row.append(1)
                    elif y == 0 and x != px:
                        row.append(1)
                    else:
                        row.append(0)
                self.material.append(row)
            self.divideMaze(1, 1, CHUNK_SIZE - 1, CHUNK_SIZE - 1, self.chooseMazeOrientation(CHUNK_SIZE, CHUNK_SIZE))

        else:
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

    def chooseMazeOrientation(self, width, height):
        if width < height:
            return 0
        if height < width:
            return 1
        return randint(0, 1)

    def divideMaze(self, x, y, width, height, orientation):
        if width < 3 or height < 3:
            return

        horizontal = orientation == 0

        # where will the wall be drawn from?
        wx = x + (0 if horizontal else randint(0, (width-3)/2)*2 + 1)
        wy = y + (randint(0, (height-3)/2)*2 + 1 if horizontal else 0)

        # where will the passage through the wall exist?
        px = wx + (randint(0, (width-1)/2)*2 if horizontal else 0)
        py = wy + (0 if horizontal else randint(0, (height-1)/2)*2)

        # what direction will the wall be drawn?
        dx = 1 if horizontal else 0
        dy = 0 if horizontal else 1

        # how long will the wall be?
        length = width if horizontal else height

        for _ in range(length):
            if wx != px or wy != py:
                self.material[wy][wx] = 1
            wx += dx
            wy += dy

        nx, ny = x, y
        w, h =  [width, wy-y] if horizontal else [wx-x, height]
        self.divideMaze(nx, ny, w, h, self.chooseMazeOrientation(w, h))

        nx, ny = [x, wy+1] if horizontal else [wx+1, y]
        w, h =  [width, y+height-wy-1] if horizontal else [x+width-wx-1, height]
        self.divideMaze(nx, ny, w, h, self.chooseMazeOrientation(w, h))

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
            return jsonpickle.decode(cdata[0])
        ch = Chunk(cx, cy)
        self.saveChunk(ch)
        return ch

    def saveChunk(self, c):
        cdata = jsonpickle.encode(c)
        cur = _db.cursor()
        cur.execute(
            'INSERT INTO chunk (x, y, data) VALUES (?, ?, ?)',
            (c.cx, c.cy, cdata))
        _db.commit()

    def updateChunk(self, c):
        cdata = jsonpickle.encode(c)
        cur = _db.cursor()
        cur.execute(
            'UPDATE chunk SET data = ? WHERE x = ? AND y = ?',
            (cdata, c.cx, c.cy))
        _db.commit()

    def setMaterial(self, x, y, m):
        c = self.chunk(x, y)
        c.setMaterial(x, y, m)
        self.updateChunk(c)


_clients = []


class Game(amp.AMP):

    def getChunk(self, x, y):
        return {'chunk': jsonpickle.encode(_world.chunk(x, y))}
    GetChunk.responder(getChunk)

    def updateChunk(self, chunk):
        _world.updateChunk(jsonpickle.decode(chunk))
        return {'result': True}
    UpdateChunk.responder(updateChunk)

    def updateMaterial(self, x, y, material):
        _world.setMaterial(x, y, material)
        for client in _clients:
            client.callRemote(UpdateMaterial, x=x, y=y, material=material)
        return {'result': True}
    UpdateMaterial.responder(updateMaterial)

    def updateUserPosition(self, user, x, y):
        for client in _clients:
            client.callRemote(UpdateUserPosition, user=user, x=x, y=y)
        return {'result': True}
    UpdateUserPosition.responder(updateUserPosition)

    def connectionMade(self):
        super().connectionMade()
        _clients.append(self)
        print('connection made!')

    def connectionLost(self, reason):
        super().connectionLost(reason)
        _clients.remove(self)
        print('connection lost!')


def startServer(world, seed, port):
    startLogging(stdout)

    factory = Factory()
    factory.protocol = Game
    reactor.listenTCP(port, factory)

    global _db
    global _noise
    global _world

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
    _world = World()
    reactor.listenMulticast(8005, MulticastPingPong(),
                        listenMultiple=True)
    # tick = LoopingCall(gameTick)
    # tick.start(1.0 / DESIRED_FPS)
    reactor.run()
