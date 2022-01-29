import pygame
import os
import random

#
# import modules from the project.
#

from .core import core
from .utils import *
from .gui import *

#
# constants.
#

PLAYER_LOOKING_UP   = 1
PLAYER_LOOKING_DOWN = 2
PLAYER_LOOKING_LEFT = 3
PLAYER_LOOKING_RIGHT= 4

#
# item: items.
#

class item:
    # NOTE: the item name.
    name = 'item'
    generic = 'item00'

#
# player: store the player.
#

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

#
# wElement: world element.
#

ELEMENT_TEX_IMAGE   = 0
ELEMENT_TEX_SPRITE  = 1

class wElement:

    # names and etc
    name = None
    genericName = None

    size = None
    rect = None
    position = None

    # NOTE: textureData is used for re-spawn the element texture
    # because when the world is changed, the texture is unloaded
    # from the memory.
    textureData = None
    texture = None
    textureType = None
    textureIndex = 0
    textureTiming = 0
    textureUpdateTime = 0

    # other properties.
    collide = None

#
# wStore: world storage.
#

class wStore:
    def __init__(self):
        """wStore: store the current world or room.""" 
        self.background = None
        self.backgroundData = None
        self.playerData = None
        self.elementData = None
        self.cameraRect = pygame.Rect((0, 0), (0, 0))
        self.elements = []

#
# world: main functions.
#

class world:
    def __init__(self, core: core, debug=False):
        """world: render out the world and everything."""
        # load all the generic stuff.
        self.core = core
        self.player = player()
        self.debug = debugReporter(debug)
        self.debug.write("Hello! You enabled debug!",location=__name__)
        
        # viewport and drawing stuff.
        self.viewport = pygame.Surface(self.core.window.surface.get_size())
        self.viewportPosition = [0, 0]

        # world storage
        self.world = None

        # NOTE: the skybox properties.
        self.skyBoxBackground   = [115, 179, 191]
        self.skyBoxCloudColor   = [255, 255, 255]
        self.skyBoxEnabled      = True
        self.skyBoxClouds       = []
        self.skyBoxCloudMax     = 25
        self.skyBoxCloudTickTime= 0.2
        self.skyBoxTickTiming   = 0

        # Some debug functions!
        self.hideWorld = False
        self.hideSkyBox = False
        self.hidePlayer = False

    def dmsg(self, string: str):
        self.debug.write(string, location=__name__)
    
    #
    # Sky Box Functions
    #
    class skyBoxCloud:
        def __init__(self):
            # NOTE: left = 0 | right = 1
            self.surface = None
            self.position = [0, 0]
            self.speed = 0
            self.direction = 0

    def skyBoxNewCloud(self):
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
        _R = self.skyBoxCloudColor[0]
        _G = self.skyBoxCloudColor[1]
        _B = self.skyBoxCloudColor[2]
        _A = 255
        for pixelCounter in range(0, _NPX):
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
        self.skyBoxClouds.append(protoCloud)
    
    def skyBoxTick(self):
        """skyBoxTick: process the cloud moviments."""
        if pygame.time.get_ticks() > self.skyBoxTickTiming:
            if len(self.skyBoxClouds) <= self.skyBoxCloudMax:
                self.dmsg("spawning clouds in background: [%d/ %d]" % (len(self.skyBoxClouds), self.skyBoxCloudMax))
                self.skyBoxNewCloud()
            for cloud in self.skyBoxClouds:
                if (cloud.position[0] + cloud.surface.get_width() < 0 or 
                    cloud.position[0] - cloud.surface.get_width() > self.viewport.get_width()):
                    self.skyBoxClouds.remove(cloud)
                else:
                    cloud.position[0] += -1 if cloud.direction == 0 else 1
            self.skyBoxTickTiming = pygame.time.get_ticks() + (0.1 * 1000)

    def skyBoxDraw(self):
        """skyBoxDraw: draw the skybox."""
        self.viewport.fill(self.skyBoxBackground)
        for cloud in self.skyBoxClouds:
            self.viewport.blit(
                cloud.surface,
                cloud.position
            )
        
    def skyBoxCleanup(self):
        self.skyBoxClouds = []

    #
    # init functions
    #

    def loadWorldByName(self, name, format=".json"):
        """loadWorldByName: load the world by it's name."""
        extractTarget = self.core.baseDir + "map" + os.sep + name + format
        self.dmsg("loading map file: %s" % extractTarget)
        extractedInfo = jsonLoad(extractTarget)
        self.loadWorldByData(extractedInfo)
    
    def loadPlayerSpawn(self, world: wStore):
        # TODO: this function.
        pass

    def spawnElements(self, world: wStore):
        """spawnElements: load all the world elements."""
        self.dmsg("there are %d elements to load." % len(world.elementData))
        for element in world.elementData:
            self.newElement(world, element)
        
    def finalize(self, world: wStore):
        """finalize: do some final stuff to the world.""" 
        world.cameraRect = pygame.Rect((0, 0), world.background.get_size())

    def loadWorldByData(self, data):
        """loadWorldByData: load the world by the json (aka. dict) information."""
        protoWorld                  = wStore()
        protoWorld.backgroundData   = data.get("background")
        protoWorld.elementData      = data.get("elements")
        protoWorld.playerData       = data.get("player")

        # -- init the world loading process! --
        # generateBackground() -> spawnElements() -> finalize()
        self.generateBackground(protoWorld)
        self.dmsg("loaded background!")
        self.spawnElements(protoWorld)
        self.dmsg("loaded elements!")
        self.finalize(protoWorld)
        self.dmsg("finalized loading.")

        # -- init the player! --
        # loadPlayerSprites() -> loadPlayerSpawn()
        self.loadPlayerSpawn(protoWorld)
        self.dmsg("loading player spawn...")

        # set the current world as the proto one.
        self.world = protoWorld

    def generateBackground(self, world: wStore):
        """generateBackground: generate the world."""
        # TODO: assert the elements on the next release!
        texturesLoad = self.core.storage.getContentByRequest(world.backgroundData.get("texture"))
        generationInstruction = world.backgroundData.get("generate")
        
        # !! INIT RANDOM & SIZES !!
        __randomGenerator = random.Random()
        __randomGenerator.seed(generationInstruction.get("seed"))
        _W  = world.backgroundData.get("size")[0]       ; _H = world.backgroundData.get("size")[1]
        _TW = world.backgroundData.get("tileSize")[0]   ; _TH = world.backgroundData.get("tileSize")[1]

        # TODO: implement the other ways to generate the world!
        if generationInstruction.get("method") == "random":
            # TODO: this way of rendering the tiles are not very good
            # in games that have a large map, so on the next versions
            # implement the chunk rendering system!
            self.dmsg("background is using the random generation.")
            world.background = pygame.Surface(((_W + 1) * _TW, (_H + 1) * _TH))
            for yIndex in range(0, _H+1):
                for xIndex in range(0, _W+1):
                    textureChoice = __randomGenerator.choice(texturesLoad)
                    world.background.blit( 
                        textureChoice,
                        (
                            _TW * xIndex,
                            _TH * yIndex
                        )
                    )
        elif generationInstruction.get("method") == "mapped":
            # NOTE: load the blocks texture.
            self.dmsg("background is using the mapped generation.")
            blockDict = {}
            blocks = generationInstruction.get("blocks")
            for blockKey in blocks.keys():
                blockDict[blockKey] = self.core.storage.getContentByRequest(blocks[blockKey])
            # !! BEGIN BUILDING THE BACKGROUND !!
            matrix = generationInstruction.get("matrix")
            world.background = pygame.Surface(((_W) * _TW, (_H) * _TH))
            for yIndex in range(0, _H + 1):
                # NOTE: prevent from errors.
                # BUG: this is a bug, the generation should index from 0 -> x.
                if yIndex >= len(matrix):
                    self.dmsg("yLine has finished before expected: %d -> %d" % (yIndex, len(matrix)))
                    break
                for xIndex in range(0, _W + 1):
                    # NOTE: prevent from errors.
                    if xIndex >= len(matrix[yIndex]):
                        self.dmsg("xLine has finished before expected: %d -> %d" % (xIndex, len(matrix[yIndex])))
                        break
                    blockRequest = matrix[yIndex][xIndex]
                    textureAdquired = blockDict[blockRequest]
                    if isinstance(textureAdquired, list):
                        texture = __randomGenerator.choice(textureAdquired)
                        world.background.blit(
                            texture,
                            (xIndex * _TW, yIndex * _TH)
                        )

    def initDisplayComponents(self):
        """initDisplayComponents: init all the display components."""
        pass

    def init(self):
        """init: init the player and the world."""
        # init the display!
        self.coreDisplay = display(self.viewport)
        self.initDisplayComponents()

        # player init!
        self.player.playerTextureGenerate()
        self.player.centerPlayer(self.viewport.get_width(), self.viewport.get_height())

        self.dmsg("loading temporary map...")
        self.loadWorldByName("01-world")

    #
    # tick functions
    #

    def newElement(self, world: wStore, element: dict):
        ## !! EXTRACT INFO !! ##
        textureInfo = element.get("texture")
        elementSize = element.get("size")
        elementPos  = element.get("position")
        tileSize    = world.backgroundData.get("tileSize")

        self.dmsg("new element spawned: " + element.get("name"))

        ## !! BEGIN TO BUILD THE ELEMENT !! ##
        protoElement = wElement()
        protoElement.textureType = ELEMENT_TEX_IMAGE if textureInfo.get("type")=='image' else ELEMENT_TEX_SPRITE
        protoElement.textureUpdateTime = element.get("textureUpdateTime")
        protoElement.texture = self.core.storage.getContentByRequest(textureInfo)

        protoElement.position = elementPos
        protoElement.size = elementSize
        protoElement.collide = element.get("collide")

        protoElement.rect = pygame.Rect(
            (
                tileSize[0] * elementPos[0],
                tileSize[1] * elementPos[1],
            ),
            elementSize
        )

        # !! SAVE ELEMENT !! ##
        world.elements.append(protoElement)

    def moveWorld(self, world: wStore, xDir: int, yDir: int):
        """moveWorld: to move the world objects.""" 
        for element in world.elements:
            element.rect.x += xDir
            element.rect.y += yDir

    def walk(self, world: wStore, xDir: int, yDir: int):
        """walk: this function will check for collisions."""
        # !! INIT THE WALK PRINCIPLE !! ##

        # check if the new position will collide in something.
        playerCollisionTest = self.player.rect.copy()
        playerCollisionTest.x -= xDir
        playerCollisionTest.y -= yDir
        
        # TODO: this is not a fancy way to check if the player is
        # going outside, but for now, keep as it.
        if not world.cameraRect.contains(playerCollisionTest):
            return
        
        # !! CHECK FOR ELEMENTS !! ##
        for element in world.elements:
            if playerCollisionTest.colliderect(element.rect):
                return
        world.cameraRect.x += xDir
        world.cameraRect.y += yDir
        self.moveWorld(world, xDir, yDir)
    
    def updatePlayerStats(self):
        """updatePlayerStats: the player stats are shown on the top."""
        pass

    def tickWorldElements(self, world: wStore):
        """tickWorldElements: update their textures and etc."""
        for element in world.elements:
            if element.textureType == ELEMENT_TEX_SPRITE:
                if pygame.time.get_ticks() > element.textureTiming:
                    element.textureIndex = 0 if element.textureIndex + 1 >= len(element.texture) else element.textureIndex + 1
                    element.textureTiming = pygame.time.get_ticks() + (element.textureUpdateTime * 1000)

    def tick(self, events):
        """tick: process all the game events."""
        for event in events:
            if event.type == pygame.QUIT:
                self.core.running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    self.dmsg("hiding player...")
                    self.hidePlayer = not self.hidePlayer
                if event.key == pygame.K_F2:
                    self.dmsg("hiding world...")
                    self.hideWorld = not self.hideWorld
                if event.key == pygame.K_F3:
                    self.dmsg("hiding skybox...")
                    self.hideSkyBox = not self.hideSkyBox
                if event.key == pygame.K_F4:
                    self.dmsg("reseting draw...")
                    self.skyBoxCleanup()
                    self.hideSkyBox = False
                    self.hidePlayer = False
                    self.hideWorld = False

        # NOTE: the clouds are processed before everything 
        # since they only appear on the background.
        self.skyBoxTick()

        # load the continuous keypresses!
        # TODO: implement key maps!
        keyPress = pygame.key.get_pressed()
        if   keyPress[pygame.K_UP] or keyPress[pygame.K_w]:
            self.walk(self.world, 0, self.player.speed)
        elif keyPress[pygame.K_DOWN] or keyPress[pygame.K_s]:
            self.walk(self.world, 0,-self.player.speed)
        elif keyPress[pygame.K_RIGHT] or keyPress[pygame.K_d]:
            self.walk(self.world, -self.player.speed,0)
        elif keyPress[pygame.K_LEFT] or keyPress[pygame.K_a]:
            self.walk(self.world, self.player.speed, 0)
        
        # NOTE: tick all the guis!
        self.coreDisplay.tick(events)
        self.tickWorldElements(self.world)

    #
    # draw functions
    #

    def updateScreen(self):
        """updateScreen: update the screen."""
        pygame.display.flip()
    
    def updateViewport(self):
        """updateViewport: update the viewport."""
        self.core.window.surface.blit(
            self.viewport,
            self.viewportPosition
        )
    
    def cleanScreen(self):
        """cleanScreen: clean the screen."""
        self.core.window.surface.fill((0, 0, 0))
    
    def cleanViewport(self):
        """cleanViewport: clean the viewport."""
        self.viewport.fill((0, 0, 0))
    
    def drawPlayer(self):
        """drawPlayer: draw the player."""
        # NOTE: are you hiding the player?
        if not self.hidePlayer:
            playerLookingAt = self.player.lookingAt
            playerTextureIndex = self.player.textureIndex
            self.viewport.blit(
                self.player.textures[playerLookingAt][playerTextureIndex],
                self.player.rect
            )
    
    def drawWorldElements(self, world: wStore):
        """drawWorldElements: draw the world elements.""" 
        for element in world.elements:
            # NOTE: select the method to draw.
            if element.textureType == ELEMENT_TEX_SPRITE:
                self.viewport.blit(
                    element.texture[element.textureIndex],
                    element.rect
                )

    def drawWorld(self, world: wStore):
        """drawWorld: draw the player."""
        if not self.hideWorld:
            self.viewport.blit(
                world.background,
                world.cameraRect
            )
            self.drawWorldElements(self.world)

    def drawGuis(self):
        """drawGuis: basically draw all the GUI's"""
        self.coreDisplay.draw()

    def draw(self):
        """draw: draw the game elements."""
        if self.core.running:
            # cleanScreen -> cleanViewport [clean stage]
            self.cleanScreen()
            self.cleanViewport()
            # NOTE: draw the skybox.
            if not self.hideSkyBox:
                self.skyBoxDraw()
            # drawWorld (case loaded.) -> drawPlayer
            if self.world:
                self.drawWorld(self.world)
                self.drawPlayer()
            # NOTE: draw the GUI's case enabled
            self.coreDisplay.draw()
            # updateViewport -> updateScreen
            self.updateViewport()
            self.updateScreen()