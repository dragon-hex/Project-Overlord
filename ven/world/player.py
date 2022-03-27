from ven.utils import *
import pygame

# player elements here.
PLAYER_LOOKING_UP   = 0
PLAYER_LOOKING_DOWN = 1
PLAYER_LOOKING_LEFT = 2
PLAYER_LOOKING_RIGHT= 3

class player:
    # player name.
    name    = 'Pixel'
    generic = 'pixel'

    # direction the player is facing off.
    size        = [32, 32]
    rect        = None
    lookingAt   = PLAYER_LOOKING_DOWN
    
    # textures
    textures = []
    textureIndex = 0
    textureIndexTime = 0
    textureTimeUpdate = 0.2

    # player health
    health      = 100
    maxHealth   = 100
    experience  = 0
    level       = 0
    speed       = 4

    # player controls
    playerReady = False
    busy = False

    # player inventory
    inventory   = []

    def setDirection(self, direction):
        """setDirection: setup the main direction."""
        if self.lookingAt == direction:
            if pygame.time.get_ticks() > self.textureIndexTime:
                self.textureIndex = 0 if self.textureIndex + 1 > len(self.textures[self.lookingAt]) else self.textureIndex + 1
                self.textureIndexTime = pygame.time.get_ticks() + (self.textureTimeUpdate * 1000)
        else:
            self.textureIndex = 0

    def playerTextureGenerate(self):
        """playerTextureGenerate: make some blocks for player texture."""
        block = pygame.Surface(self.size)
        block.fill(randomRGBColor())
        self.textures = [
            [block.copy(), block.copy()],
            [block.copy(), block.copy()],
            [block.copy(), block.copy()],
            [block.copy(), block.copy()]
        ]
    
    def centerPlayer(self, swidth, sheight):
        """centerPlayer: set the player on the center of the screen."""
        self.rect = pygame.Rect(
            # center of the screen axis - size of the sprite.
            (
                swidth  // 2 - self.size[0] // 2, 
                sheight // 2 - self.size[1] // 2
            ),
            # rect size = size!
            self.size
        )
