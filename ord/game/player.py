from ord.utils import randomRGBColor
import pygame

# player elements here.
PLAYER_LOOKING_UP   = 1
PLAYER_LOOKING_DOWN = 2
PLAYER_LOOKING_LEFT = 3
PLAYER_LOOKING_RIGHT= 4

class player:
    # NOTE: name = allows spaces and everything
    # generic = don't allows spaces or strange symbols.
    name = 'Pixel'
    generic = 'pixel'
    size = [32, 32]

    # NOTE: the position of the player is fixed on the
    # center of the screen.
    rect = None
    textures = []
    
    # NOTE: looking at is initialized at the bottom, always.
    # the texture index is only updated on the walking event.
    # the texture index time is updated also, when walking.
    lookingAt = PLAYER_LOOKING_DOWN
    textureIndex = 0
    textureIndexTime = 0
    textureTimeUpdate = 0.2

    # NOTE: the player health is used on some games.
    health      = 100
    maxHealth   = 100
    experience  = 0
    level       = 0
    speed       = 4

    # NOTE: the player inventory.
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
