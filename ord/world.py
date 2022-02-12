import pygame
import os
import random

#
# import modules from the project.
#

from .core import core
from .utils import *
from .gui import *
from .game import *

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

    # collision boxes and draw positions
    drawRect = None
    collisionRect = None
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
        self.infoData = None
        self.cameraRect = pygame.Rect((0, 0), (0, 0))
        self.elements = []
        self.skyboxData = None
        self.name = None

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
        self.viewport = pygame.Surface(self.core.window.surface.get_size(), pygame.SRCALPHA)
        self.viewportPosition = [0, 0]

        # world storage
        self.world = None

        # NOTE: the skybox properties.
        self.skyBox = skyBox(self.viewport)        

        # Some debug functions!
        self.hideWorld = False
        self.hidePlayer = False
        self.debugHitboxes = True

    def dmsg(self, string: str):
        self.debug.write(string, location=__name__)
    
    def crash(self, reason: str):
        """
        crash: show the error screen and try to save the game.
        """
        
        # => adjust the elements <=
        self.mainError.setText('"%s"' % str(reason))
        self.mainStatus.setText("You can safely close the window...")
        self.panicFrame.visible = True
        insideCrash = True

        # => create a crash loop <=
        while insideCrash:
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    insideCrash = False
            
            # => clean the viewport <=
            self.cleanViewport()

            self.coreDisplay.tick(events)
            self.coreDisplay.draw()

            self.updateViewport()
            pygame.display.flip()
        
        # quit the program due instable envirolment.
        exit(-1)
    
    def makeSure(self, condition, atError: str):
        """makeSure: automatically crash the program."""
        if not condition:
            self.crash(atError)
    
    #
    # init functions
    #

    def loadWorldByName(self, name, format=".json"):
        """loadWorldByName: load the world by it's name."""

        extractTarget = self.core.baseDir + "map" + os.sep + name + format
        self.makeSure(os.path.isfile(extractTarget), "File not found: %s" % extractTarget)

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
        self.skyBox.background = world.skyboxData.get("backgroundColor")
        self.makeSure(
            self.skyBox.background and isinstance(self.skyBox.background, list),
            "invalid skybox background color."
        )
        self.skyBox.enabledClouds = world.skyboxData.get("enableClouds")
        world.cameraRect = pygame.Rect((0, 0), world.background.get_size())

    def loadWorldByData(self, data):
        """loadWorldByData: load the world by the json (aka. dict) information."""
        protoWorld                  = wStore()
        protoWorld.backgroundData   = data.get("background")
        protoWorld.elementData      = data.get("elements")
        protoWorld.playerData       = data.get("player")
        protoWorld.skyboxData       = data.get("skybox")
        protoWorld.infoData         = data.get("info")

        self.makeSure(protoWorld.backgroundData != None,    "background not defined.")
        self.makeSure(protoWorld.elementData != None,       "element not defined.")
        self.makeSure(protoWorld.playerData != None,        "player not defined.")
        self.makeSure(protoWorld.skyboxData != None,        "skybox not defined.")
        self.makeSure(protoWorld.infoData != None,          "info not defined.")

        protoWorld.name             = protoWorld.infoData.get("name")
        self.makeSure(protoWorld.name != None, "World has no name set up!")

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
        self.makeSure(generationInstruction != None, "not defined background generation instruction!")
        
        seedUsing = generationInstruction.get("seed") or 1

        # !! INIT RANDOM & SIZES !!
        __randomGenerator = random.Random()
        __randomGenerator.seed(seedUsing)

        _W  = world.backgroundData.get("size")[0]       ; _H = world.backgroundData.get("size")[1]
        _TW = world.backgroundData.get("tileSize")[0]   ; _TH = world.backgroundData.get("tileSize")[1]

        self.makeSure(_W != None and isinstance(_W, int), "Background width was not set or invalid value!")
        self.makeSure(_H != None and isinstance(_H, int), "Background height was not set or invalid value!")
        self.makeSure(_TW != None and isinstance(_TW, int), "Background tiles width was set or invalid value!")
        self.makeSure(_TH != None and isinstance(_TH, int), "Background tiles height was not set or invalid value!")

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
                        if len(textureAdquired) <= 1:
                            texture = textureAdquired[0]
                        else:
                            texture = __randomGenerator.choice(textureAdquired)
                    
                    world.background.blit(
                        texture,
                        (xIndex * _TW, yIndex * _TH)
                    )
        else:
            self.crash("Unknown background generation method: '%s' in '%s' level." % (generationInstruction.get("method"), world.name))
    
    def __getRandomMessage(self):
        __messages = [
            "I don't know english!",
            "Oh goodbye, the night and day...",
            "I didn't expect this!",
            "Sakura one of the culprits!",
            "I was sleeping when this happened.",
            "Sorry! I didn't mean to!",
            "Pixel, was it your fault?",
            "A bug just sit...",
            "Creepy Creeper?",
            "Thanks for watching!",
            "Underwater",
            "I have nothing to say!",
            "Buso Renkin!",
            "Strange noises came from [...]",
            "Nothing to see here!",
            "A little empty around here.",
            "This message was loaded in the init.",
            "Imagine reading the source code to gather the secret?",
            "Windows96",
            "Linux is cool, IMARITHE?",
            "ごめんバカ",
            "You know this font supports japanese?",
            "Look behind you...",
            "Look front you...",
            "I'm a alien! don't you see?",
            "Strange project.",
            "Project Overlord? more like overload my memory!"
        ]
        return random.choice(__messages)

    def __initPanicDisplay(self):
        # => build the panic frame <=
        self.panicFrame = frame(self.coreDisplay)
        self.panicFrame.background = pygame.Surface(self.viewport.get_size())
        self.panicFrame.background.fill((255, 255, 255))
        self.panicFrame.visible = False

        hugeFont    = self.core.storage.getFont("normal", 24)
        littleFont  = self.core.storage.getFont("normal", 14)
        mediumFont  = self.core.storage.getFont("normal", 16)
        
        # => use 50% and 30% for the center, but Y above a bit..
        self.mainInformativeText = label(self.coreDisplay, hugeFont, "The game has crashed!")
        self.mainInformativeText.fixedPosition = True
        self.mainInformativeText.position = [50, 30]

        self.errorMessage = label(self.coreDisplay, mediumFont, self.__getRandomMessage())
        self.errorMessage.fixedPosition = True
        self.errorMessage.position = [50, 35]

        self.mainErrorLabel = label(self.coreDisplay, hugeFont, "Error")
        self.mainErrorLabel.fixedPosition = True
        self.mainErrorLabel.position = [50, 60]

        self.mainError = label(self.coreDisplay, littleFont, "Not collected yet.")
        self.mainError.fixedPosition = True
        self.mainError.position = [50, 65]

        self.mainStatus = label(self.coreDisplay, littleFont, "N/A...")
        self.mainStatus.fixedPosition = True
        self.mainStatus.position = [1 , 99]

        # => append all the elements <=
        self.panicFrame.addElement(self.mainInformativeText)
        self.panicFrame.addElement(self.mainError)
        self.panicFrame.addElement(self.mainStatus)
        self.panicFrame.addElement(self.mainErrorLabel)
        self.panicFrame.addElement(self.errorMessage)
        self.coreDisplay.addElement(self.panicFrame)

    def initDisplayComponents(self):
        """initDisplayComponents: init all the display components."""
        # => init the core display <=
        self.coreDisplay = display(self.viewport)
        
        # => init the panic display <=
        self.__initPanicDisplay()

    def init(self):
        """init: init the player and the world."""
        # init the display!
        self.initDisplayComponents()

        # player init!
        self.player.playerTextureGenerate()
        self.player.centerPlayer(self.viewport.get_width(), self.viewport.get_height())

        self.dmsg("loading temporary map...")
        self.loadWorldByName("initial-room")

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
        protoElement.textureType        = ELEMENT_TEX_IMAGE if textureInfo.get("type")=='image' else ELEMENT_TEX_SPRITE
        protoElement.textureUpdateTime  = element.get("textureUpdateTime") or 0.5
        protoElement.texture            = self.core.storage.getContentByRequest(textureInfo)

        protoElement.position           = elementPos
        protoElement.size               = elementSize

        # => load the collision rectangle <=
        # NOTE: this can be described inside the rectangle itself.
        xDrawPosition = tileSize[0] * elementPos[0]
        yDrawPosition = tileSize[1] * elementPos[1]

        collisionData = element.get("collision")
        protoElement.collide = collisionData.get("enabled") or False

        if protoElement.collide:
            # NOTE: case you want to collide.
            if collisionData.get("use") == "fill":
                # => just set the normality <=
                xSize = tileSize[0]
                ySize = tileSize[1]
                xPosition = xDrawPosition
                yPosition = yDrawPosition
            elif collisionData.get("use") == "modified":
                # => load the mods <=
                xSize = collisionData.get("xSize")
                ySize = collisionData.get("ySize")
                xPos  = collisionData.get("xPos")
                yPos  = collisionData.get("yPos")

                # NOTE: the offset is made from the (0, 0) position.
                xPosition = xDrawPosition + xPos
                yPosition = yDrawPosition + yPos
            else:
                # TODO: crash here.
                return

            # build the rect here.
            protoElement.collisionRect = pygame.Rect((xPosition, yPosition), (xSize, ySize))

        # => load the drawing rectangle <=
        protoElement.drawRect = pygame.Rect(
            (
                xDrawPosition,
                yDrawPosition,
            ),
            elementSize
        )

        # !! SAVE ELEMENT !! ##
        world.elements.append(protoElement)

    def moveWorld(self, world: wStore, xDir: int, yDir: int):
        """moveWorld: to move the world objects.""" 
        for element in world.elements:
            # update it's position!
            element.drawRect.x += xDir
            element.drawRect.y += yDir

            # NOTE: case this sprite has collision.
            if element.collisionRect:
                element.collisionRect.x += xDir
                element.collisionRect.y += yDir

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
            if playerCollisionTest.colliderect(element.collisionRect):
                return
        
        # !! move the camera !!
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
    
    def cursorWalkEvent(self):
        """cursorWalkEvent: you can walk using the mouse clicks."""
        # TODO: implement such feature.
        pass

    def resetHides(self):
        """resetHides: reset everything."""
        # reset the clouds
        self.dmsg("reseting draw...")
        self.skyBox.deleteClouds()

        # hide the player.
        self.hidePlayer = False
        self.hideWorld  = False

    def tick(self, events):
        """tick: process all the game events."""
        for event in events:
            if event.type == pygame.QUIT:
                self.core.running = False
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                # NOTE: if enabled, this functionality allows the player to walk
                # using the mouse clicks (left button)
                if event.button == pygame.BUTTON_LEFT:
                    self.cursorWalkEvent()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    self.hidePlayer = not self.hidePlayer
                if event.key == pygame.K_F2:
                    self.hideWorld = not self.hideWorld
                if event.key == pygame.K_F3:
                    self.skyBox.enabled = not self.skyBox.enabled
                if event.key == pygame.K_F4:
                    self.resetHides()
                if event.key == pygame.K_F5:
                    self.debugHitboxes = not self.debugHitboxes
                if event.key == pygame.K_F6:
                    self.crash("I triggered this error! I'm very dumb!")
                    
        # NOTE: the clouds are processed before everything 
        # since they only appear on the background.
        self.skyBox.tick()

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
                    element.drawRect
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
    
    def __showHitboxes(self, world: wStore):
        for element in world.elements:
            # NOTE: draw the hitbox.
            hitbox = pygame.Surface((element.collisionRect.w, element.collisionRect.h), pygame.SRCALPHA)
            hitbox.fill((0, 0, 0, 100))
            self.viewport.blit(
                hitbox,
                element.collisionRect
            )

    def draw(self):
        """draw: draw the game elements."""
        if self.core.running:
            # cleanScreen -> cleanViewport [clean stage]
            self.cleanScreen()
            self.cleanViewport()

            # NOTE: draw the skybox.
            self.skyBox.draw()

            # drawWorld (case loaded.) -> drawPlayer
            if self.world:
                self.drawWorld(self.world)
                self.drawPlayer()

            # debug the hitboxes, case enabled.
            if self.debugHitboxes:
                self.__showHitboxes(self.world)

            # NOTE: draw the GUI's case enabled
            self.coreDisplay.draw()

            # updateViewport -> updateScreen
            self.updateViewport()
            self.updateScreen()