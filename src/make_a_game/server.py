from twisted.protocols import amp
from twisted.python.log import startLogging
import sqlite3
from opensimplex import OpenSimplex
import jsonpickle
import math
from .constants import (
    CHUNK_SIZE,
    NOISE_SCALE,
    MATERIAL_SCALE
)
from sys import stdout

_db = None
_noise = None
_world = None


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


class Sum(amp.Command):
    arguments = [(b'a', amp.Integer()),
                 (b'b', amp.Integer())]
    response = [(b'total', amp.Integer())]


class Divide(amp.Command):
    arguments = [(b'numerator', amp.Integer()),
                 (b'denominator', amp.Integer())]
    response = [(b'result', amp.Float())]
    errors = {ZeroDivisionError: b'ZERO_DIVISION'}


class Math(amp.AMP):
    def sum(self, a, b):
        total = a + b
        print('Did a sum: {} + {} = {}'.format(a, b, total))
        return {'total': total}
    Sum.responder(sum)

    def divide(self, numerator, denominator):
        result = float(numerator) / denominator
        print('Divided: {} / {} = {}'.format(numerator, denominator, result))
        return {'result': result}
    Divide.responder(divide)


class GetChunk(amp.Command):
    arguments = [(b'x', amp.Integer()),
                 (b'y', amp.Integer())]
    response = [(b'chunk', amp.Unicode())]


class UpdateChunk(amp.Command):
    arguments = [(b'chunk', amp.Unicode())]
    response = [(b'result', amp.Boolean())]


class Game(amp.AMP):
    def getChunk(self, x, y):
        return {'chunk': jsonpickle.encode(_world.chunk(x, y))}
    GetChunk.responder(getChunk)

    def updateChunk(self, chunk):
        _world.updateChunk(jsonpickle.decode(chunk))
        return {'result': True}
    UpdateChunk.responder(updateChunk)


def startServer(world, seed, port):
    from twisted.internet import reactor
    from twisted.internet.protocol import Factory

    startLogging(stdout)

    pf = Factory()
    pf.protocol = Game
    reactor.listenTCP(port, pf)

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

    print('started on ', port)
    reactor.run()
