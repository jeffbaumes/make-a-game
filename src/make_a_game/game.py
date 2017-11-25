import os
import pygame
class Game:
    server = None
    protocol = None
    deferred = None
    username = None
    host = None
    port = 0
    mx = 0.0
    my = 0.0
    vx = 0.0
    vy = 0.0
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
    fly = False
    tileSize = 32
game = Game()
class images:
    bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imgs', 'backrounds')
    button_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imgs', 'buttons')
    bg_images = {
    "start_bg" : pygame.image.load(os.path.join(bg_path, 'start_bg.png')),
    "lan_bg" : pygame.image.load(os.path.join(bg_path, 'lan_bg.png'))
    }
    button_images = {
    "play_button" : pygame.image.load(os.path.join(button_path, 'play_button.png')),
    "play_button_pressed" : pygame.image.load(os.path.join(button_path, 'play_button_pressed.png')),
    "multiplayer_button": pygame.image.load(os.path.join(button_path, 'multiplayer_button.png')),
    "multiplayer_button_pressed" : pygame.image.load(os.path.join(button_path, 'multiplayer_button_pressed.png'))
    }
