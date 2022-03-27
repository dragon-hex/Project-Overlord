# import the pygame module.
import pygame

# import this DIR module.
from .skybox import     skyBox
from .scripts import    scriptManager
from .entity import     *
from .item import       *
from .player import     *
from .elements import   *
from .cmd import        *

# import project functions
from ven.utils import   *

# import some python modules.
import random, time, os

##########################
# wStore: world storage. #
##########################

class wStore:
    def __init__(self):
        """wStore: store the current world or room.""" 
        # data stores.
        self.backgroundData = None
        self.elementData = None
        self.playerData = None
        self.skyboxData = None
        self.scriptData = None
        self.infoData = None
        self.poolData = None

        # it's background
        self.background = None

        # view & camera system
        self.cameraRect = pygame.Rect((0, 0), (0, 0))

        # elements
        self.elements = []

        # world information
        self.name = None

#
# world: main functions.
#

class world:
    def __init__(self, viewport: pygame.Surface, sharedCore: any, debug=False):
        """world: render out the world and everything."""
        # load the core functions
        self.core           = sharedCore
        self.scriptManager  = scriptManager(self, debug)
        self.cmd            = cmd(self, debug=debug)
        self.player         = player()
        self.viewport       = viewport
        self.skyBox         = skyBox(self.viewport)

        self.debug          = debugReporter(debug)
        self.debug.location = "world"
        self.debug.write("Hello World!")
        self.scriptOutput   = None
        self.hideWorld      = False
        self.hidePlayer     = False
        self.debugHitboxes  = False
        self.inputLocked    = False

        # world storage
        self.world          = None

        # shared events with the engine.
        self.crash          = None
        self.makeSure       = None
        self.makeDialog     = None

    ##################
    # init functions #
    ##################

    def loadWorldByName(self, name, format=".json"):
        """loadWorldByName: load the world by it's name."""
        extractTarget = self.core.baseDir + "map" + os.sep + name + format
        self.makeSure(os.path.isfile(extractTarget), "File not found: %s" % extractTarget)
        self.debug.write("loading map file: %s" % extractTarget)
        # begin to load -
        extractedInfo = jsonLoad(extractTarget)
        self.loadWorldByData(extractedInfo)
    
    def loadPlayerSpawn(self, world: wStore):
        # TODO: this function.
        pass

    def spawnElements(self, world: wStore):
        """spawnElements: load all the world elements."""
        self.debug.write("there are %d elements to load." % len(world.elementData))
        for element in world.elementData:   self.newElement(world, element)
        
    def finalize(self, world: wStore):
        """finalize: do some final stuff to the world.""" 
        self.skyBox.background = world.skyboxData.get("backgroundColor")
        self.makeSure(self.skyBox.background and isinstance(self.skyBox.background, list), "invalid skybox background color.")
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
        protoWorld.scriptData       = data.get("scripts")
        protoWorld.poolData         = data.get("pool")

        self.makeSure(protoWorld.backgroundData     != None,    "Background not defined.")
        self.makeSure(protoWorld.elementData        != None,       "Element not defined.")
        self.makeSure(protoWorld.playerData         != None,        "Player not defined.")
        self.makeSure(protoWorld.skyboxData         != None,        "Skybox not defined.")
        self.makeSure(protoWorld.infoData           != None,          "Info not defined.")
        self.makeSure(protoWorld.scriptData         != None,        "Script not defined.")
        self.makeSure(protoWorld.poolData           != None,          "Pool not defined.")

        protoWorld.name = protoWorld.infoData.get("name")
        self.makeSure(protoWorld.name != None, "World has no name set up!")

        # -- init the world loading process! --
        self.generateBackground(protoWorld) ;   self.debug.write("loaded background!")
        self.spawnElements(protoWorld)      ;   self.debug.write("loaded elements!")
        self.finalize(protoWorld)           ;   self.debug.write("finalized loading.")

        # -- init the player! --
        self.loadPlayerSpawn(protoWorld)    ;   self.debug.write("loading player spawn...")
        self.scriptManager.initWorldScripts(protoWorld) ; self.debug.write("loading the scripts...")

        # save current world.
        self.world = protoWorld

    def generateBackground(self, world: wStore):
        """generateBackground: generate the world."""
        # TODO: assert the elements on the next release!
        texturesLoad            = self.core.storage.getContentByRequest(world.backgroundData.get("texture"))
        generationInstruction   = world.backgroundData.get("generate")
        self.makeSure(generationInstruction != None, "not defined background generation instruction!")
        seedUsing = generationInstruction.get("seed") or 1

        # init random sizes.
        __randomGenerator = random.Random(seedUsing)
        _W  = world.backgroundData.get("size")[0]       ; _H = world.backgroundData.get("size")[1]
        _TW = world.backgroundData.get("tileSize")[0]   ; _TH = world.backgroundData.get("tileSize")[1]
        self.makeSure(_W  != None and isinstance(_W, int)   ,  "Background width was not set or invalid value!")
        self.makeSure(_H  != None and isinstance(_H, int)   ,  "Background height was not set or invalid value!")
        self.makeSure(_TW != None and isinstance(_TW, int)  , "Background tiles width was set or invalid value!")
        self.makeSure(_TH != None and isinstance(_TH, int)  , "Background tiles height was not set or invalid value!")
        # generate the world using the desired method.
        if generationInstruction.get("method") == "random":
            self.debug.write("background is using the random generation.")
            world.background = pygame.Surface(((_W + 1) * _TW, (_H + 1) * _TH))
            for yIndex in range(0, _H+1):
                for xIndex in range(0, _W+1):
                    textureChoice = __randomGenerator.choice(texturesLoad)
                    world.background.blit(textureChoice, (_TW * xIndex, _TH * yIndex))
        elif generationInstruction.get("method") == "mapped":
            # !! LOAD THE TEXTURES !!
            self.debug.write("background is using the mapped generation.")
            blockDict, blocks = {}, generationInstruction.get("blocks")
            for blockKey in blocks.keys(): blockDict[blockKey] = self.core.storage.getContentByRequest(blocks[blockKey])
            # !! BEGIN BUILDING THE BACKGROUND !!
            matrix = generationInstruction.get("matrix")
            world.background = pygame.Surface(((_W) * _TW, (_H) * _TH))
            for yIndex in range(0, _H):
                if yIndex >= len(matrix):
                    self.debug.write("yLine has finished before expected: %d -> %d" % (yIndex, len(matrix)))    ;   break
                for xIndex in range(0, _W):
                    # NOTE: prevent from errors.
                    if xIndex >= len(matrix[yIndex]):
                        self.debug.write("xLine has finished before expected: %d -> %d" % (xIndex, len(matrix[yIndex])))    ;   break
                    blockRequest = matrix[yIndex][xIndex]   ;   textureAdquired = blockDict[blockRequest]
                    if isinstance(textureAdquired, list):
                        if len(textureAdquired) <= 1:   texture = textureAdquired[0]
                        else:                           texture = __randomGenerator.choice(textureAdquired)
                    world.background.blit(texture, (xIndex * _TW, yIndex * _TH))
        else:
            self.crash("Unknown background generation method: '%s' in '%s' level." %  (generationInstruction.get("method"), world.name))
    
    def init(self):
        """init: init the player and the world."""
        self.player.playerTextureGenerate() ;   self.player.centerPlayer(self.viewport.get_width(), self.viewport.get_height())
        self.debug.write("loading temporary map...")
        self.loadWorldByName("initial-room")

    #####################
    # utility functions #
    # ###################

    def getInWorldPosition(self) -> list:
        # return the player relative to world position.
        if self.world:
            playerX = 0 + self.world.cameraRect.x
            playerX = abs(playerX - self.player.rect.x)
            playerY = 0 + self.world.cameraRect.y
            playerY = abs(playerY - self.player.rect.y)
            return (playerX, playerY)
        else:
            return (0, 0)

    def newElement(self, world: wStore, element: dict):
        """
        newElement: generates a new element.

        ARGS:
        world:          set the world.
        element:        the element recipe.
        """
        protoElement = wElement()
        protoElement.loadElementData(world, self, element)
        world.elements.append(protoElement)

    ##################
    # tick functions #
    ##################

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
    
    def __checkElementCollisions(self, world: wStore, rect: pygame.Rect):
        for element in world.elements:
            if rect.colliderect(element.collisionRect):
                return True
        return False

    def walk(self, world: wStore, xDir: int, yDir: int):
        """preciseWalk: basically, the walk but with more precion."""
        walkX, walkY = 0, 0
        if xDir != 0:
            maxWalkX, xWalk    = 0, abs(xDir)
            for xTest in range(0, xWalk):
                playerCollisionTest     = self.player.rect.copy()
                playerCollisionTest.x  -= xTest if xDir > 0 else -(xTest)
                if not world.cameraRect.contains(playerCollisionTest):          break
                if self.__checkElementCollisions(world, playerCollisionTest):   break
                maxWalkX = xTest
            walkX = -(maxWalkX) if xDir <= 0 else maxWalkX
        if yDir != 0:
            maxWalkY, yWalk    = 0, abs(yDir)
            for yTest in range(0, yWalk):
                playerCollisionTest     = self.player.rect.copy()
                playerCollisionTest.y  -= yTest if yDir > 0 else -(yTest)
                if not world.cameraRect.contains(playerCollisionTest):          break
                if self.__checkElementCollisions(world, playerCollisionTest):   break
                maxWalkY = yTest
            walkY = -(maxWalkY) if yDir <= 0 else maxWalkY
        world.cameraRect.x += walkX
        world.cameraRect.y += walkY
        self.moveWorld(world, walkX, walkY)
    
    def updatePlayerStats(self):
        """updatePlayerStats: the player stats are shown on the top."""
        pass

    def tickElementsActions(self, world: wStore):
        if self.player.busy:    return
        for element in world.elements:
            if element.inAction:
                if element.actionIndex + 1 > len(element.action):
                    self.debug.write("finishing the element action: %s" % element.name)
                    self.player.busy, element.inAction = False, False
                    element.actionIndex    = 0
                else:
                    self.debug.write("executing command: %s in element: %s" % (element.action[element.actionIndex], element.name), isWarn=True)
                    self.cmd.run(element.action[element.actionIndex])
                    element.actionIndex += 1

    def __checkElementTriggers(self, world: wStore, rect: pygame.Rect):
        TEST_REGION = 1
        rectTest=rect.copy()
        if self.player.playerReady:
            for element in world.elements:
                # TODO: optimize this code.
                if self.player.lookingAt == PLAYER_LOOKING_UP:          rectTest.y -= TEST_REGION
                elif self.player.lookingAt == PLAYER_LOOKING_DOWN:      rectTest.y += TEST_REGION
                elif self.player.lookingAt == PLAYER_LOOKING_RIGHT:     rectTest.x += TEST_REGION
                elif self.player.lookingAt == PLAYER_LOOKING_LEFT:      rectTest.x -= TEST_REGION
                if rectTest.colliderect(element.collisionRect) and element.action != None:
                    self.debug.write("event triggered for element %s" % element.name, isWarn=True)
                    element.actionIndex, element.inAction = 0, True
                    self.player.playerReady = False
                    return True

    def tickWorldElements(self, world: wStore):
        """
        tickWorldElements: update the world elements.

        ARGS:
        world:      specific world.
        """
        for element in world.elements:
            if element.textureType == ELEMENT_TEX_SPRITE:
                if pygame.time.get_ticks() > element.textureTiming:
                    element.textureIndex = 0 if element.textureIndex + 1 >= len(element.texture) else element.textureIndex + 1
                    element.textureTiming = pygame.time.get_ticks() + (element.textureUpdateTime * 1000)
        self.tickElementsActions(world)
        if not self.player.busy:    self.__checkElementTriggers(world, self.player.rect)
    
    def cursorWalkEvent(self):
        """cursorWalkEvent: you can walk using the mouse clicks."""
        # TODO: implement such feature.
        pass

    def resetHides(self):
        """
        resetHides: makes all the debug stuff hidden again.
        """
        # reset the clouds
        self.debug.write("reseting draw...", isWarn=True)
        self.skyBox.deleteClouds()
        # hide the player.
        self.hidePlayer, self.hideWorld = False, False
    
    def __singleEvents(self, events):
        """
        __singleEvents: load all the single events.
        """
        for event in events:
            if event.type == pygame.QUIT:
                self.core.running = False
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:  self.cursorWalkEvent()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:            self.hidePlayer = not self.hidePlayer
                if event.key == pygame.K_F2:            self.hideWorld = not self.hideWorld
                if event.key == pygame.K_F4:            self.resetHides()
                if event.key == pygame.K_F5:            self.debugHitboxes = not self.debugHitboxes
                if event.key == pygame.K_F6:            self.skyBox.enabled = not self.skyBox.enabled
    
    def __keypressCheck(self):
        """
        __keypressCheck: process all the continuous keypresses.
        """
        keyPress = pygame.key.get_pressed()
        self.player.playerReady = keyPress[pygame.K_e]
        if   keyPress[pygame.K_UP] or keyPress[pygame.K_w]:
            self.walk(self.world, 0, self.player.speed)
            self.player.lookingAt=PLAYER_LOOKING_UP
        elif keyPress[pygame.K_DOWN] or keyPress[pygame.K_s]:
            self.walk(self.world, 0,-self.player.speed)
            self.player.lookingAt=PLAYER_LOOKING_DOWN
        elif keyPress[pygame.K_RIGHT] or keyPress[pygame.K_d]:
            self.walk(self.world, -self.player.speed,0)
            self.player.lookingAt=PLAYER_LOOKING_RIGHT
        elif keyPress[pygame.K_LEFT] or keyPress[pygame.K_a]:
            self.walk(self.world, self.player.speed, 0)
            self.player.lookingAt=PLAYER_LOOKING_LEFT

    def tick(self, events) -> None:
        """
        tick: do the game logic.

        ARGS:
        events:     the event listing.
        """
        if not self.inputLocked:
            self.__singleEvents(events)
            self.__keypressCheck()
        self.scriptManager.tickScripts()
        self.skyBox.tick()
        self.tickWorldElements(self.world)

    ##################
    # draw functions #
    ##################
    
    def cleanViewport(self):
        """cleanViewport: clean the viewport."""
        self.viewport.fill((0, 0, 0))
    
    def drawPlayer(self):
        """drawPlayer: draw the player."""
        if not self.hidePlayer:
            playerLookingAt = self.player.lookingAt
            playerTextureIndex = self.player.textureIndex
            self.viewport.blit(self.player.textures[playerLookingAt][playerTextureIndex], self.player.rect)
    
    def drawWorldElements(self, world: wStore):
        """drawWorldElements: draw the world elements.""" 
        for element in world.elements:
            # NOTE: select the method to draw.
            if element.textureType == ELEMENT_TEX_SPRITE:   self.viewport.blit(element.texture[element.textureIndex], element.drawRect)
            else:                                           self.viewport.blit(element.texture, element.drawRect)

    def drawWorld(self, world: wStore):
        """drawWorld: draw the player."""
        if not self.hideWorld:
            self.viewport.blit(world.background, world.cameraRect)
            self.drawWorldElements(self.world)
    
    def __showHitboxes(self, world: wStore):
        for element in world.elements:  pygame.draw.rect(self.viewport, (0, 0, 0, 100), element.collisionRect)

    def draw(self):
        """draw: draw the game elements."""
        if self.core.running:
            self.cleanViewport()
            self.skyBox.draw()
            if self.world:          self.drawWorld(self.world)  ;   self.drawPlayer()
            if self.debugHitboxes:  self.__showHitboxes(self.world)