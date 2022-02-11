import pygame
import random

class skyBox:
    class skyBoxCloud:
        def __init__(self):
            # NOTE: left = 0 | right = 1
            self.surface = None
            self.position = [0, 0]
            self.speed = 0
            self.direction = 0
    
    def __init__(self, viewport):
        """skyBox: setup the skybox."""
        # => setup the viewport.
        self.viewport           = viewport

        # => setup the skybox variables.
        self.background   = [115, 179, 191]
        self.cloudColor   = [255, 255, 255]
        self.enabled      = True
        self.clouds       = []
        self.cloudMax     = 25
        self.cloudTickTime= 0.2
        self.tickTiming   = 0

    def newCloud(self):
        """skyBoxNewCloud: spawn some clouds!"""
        _CW     = 256 * 2
        _CH     = 64 * 2
        _NPX    = 200

        # NOTE: cloud is a class!
        protoCloud = self.skyBoxCloud()
        protoCloud.surface = pygame.Surface((_CW, _CH), pygame.SRCALPHA)
        protoCloud.surface.fill((0, 0, 0, 0))

        # Load the position & direction.
        protoCloud.position = [
            random.randint(0, self.viewport.get_width()  - _CW),
            random.randint(0, self.viewport.get_height() - _CH)
        ]
        protoCloud.direction = random.randint(1, 2) - 1
        
        # NOTE: use a simple algorithm to generate the cloud pattern!
        _R = self.cloudColor[0]
        _G = self.cloudColor[1]
        _B = self.cloudColor[2]
        _A = 255
        for _ in range(0, _NPX + 1):
            radiusSize = random.randint(10, 30)
            centerSurX = protoCloud.surface.get_width()    // 2 - radiusSize
            centerSurY = protoCloud.surface.get_height()   // 2 - radiusSize
            randomXPos = random.randint(centerSurX, centerSurX + 220)
            randomXPos = -(randomXPos) if random.randint(1, 8) in (2, 4) else randomXPos
            randomYPos = random.randint(centerSurY, centerSurY + 50)
            randomYPos = -(randomYPos) if random.randint(1, 8) in (2, 4) else randomYPos
            pygame.draw.circle(protoCloud.surface,(_R, _G, _B, _A),(randomXPos, randomYPos),radiusSize)
            _A = _A - 1 if _A > 0 else _A
        
        # insert the cloud!
        self.clouds.append(protoCloud)
    
    def tick(self):
        """skyBoxTick: process the cloud moviments."""
        if self.enabled:
            if pygame.time.get_ticks() > self.tickTiming:
                if len(self.clouds) <= self.cloudMax:
                    self.newCloud()
                for cloud in self.clouds:
                    if (cloud.position[0] + cloud.surface.get_width() < 0 or 
                        cloud.position[0] - cloud.surface.get_width() > self.viewport.get_width()):
                        self.clouds.remove(cloud)
                    else:
                        cloud.position[0] += -1 if cloud.direction == 0 else 1
                self.tickTiming = pygame.time.get_ticks() + (0.1 * 1000)

    def draw(self):
        """skyBoxDraw: draw the skybox."""
        if self.enabled:
            self.viewport.fill(self.background)
            for cloud in self.clouds:
                self.viewport.blit(
                    cloud.surface,
                    cloud.position
                )
        
    def deleteClouds(self):
        self.clouds = []