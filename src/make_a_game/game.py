

class Game:
    server = None
    protocol = None
    deferred = None
    username = None
    host = None
    port = 0
    mx = 0
    my = 0
    vx = 0
    vy = 0
    font = None
    sizex = 800
    sizey = 800
    screen = None
    worldName = None
    world = None
    playerPositions = {}
    screen_number = 0
    startScreenLoop = None
    slotMaterial = 1

game = Game()
