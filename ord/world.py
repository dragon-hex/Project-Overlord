# high priority module!
import pygame

from .core import core
from .utils import *
from .modules import *
from .gui import *

import random
import time
import os

#
# constants.
#

REAPER_VERSION = ["1.0", 1.0]

#
# wElement: world element.
#

ELEMENT_TEX_IMAGE   = 0
ELEMENT_TEX_SPRITE  = 1

class wElement:
    # naming and it generic name.
    name = None
    genericName = None

    # sizes and rects.
    size = None
    drawRect = None
    collisionRect = None
    position = None

    # texture storage & information
    textureData = None
    texture = None
    textureType = None
    textureIndex = 0
    textureTiming = 0
    textureUpdateTime = 0

    # misc. properties.
    collide = None

#
# wEntity: stores the world entity.
#

class wEntity(wElement):
    pass

#
# wStore: world storage.
#

class wStore:
    def __init__(self):
        """wStore: store the current world or room.""" 
        self.backgroundData = None
        self.elementData = None
        self.playerData = None
        self.skyboxData = None
        self.scriptData = None
        self.infoData = None
        self.poolData = None

        # => background <=
        self.background = None

        # => view & camera <=
        self.cameraRect = pygame.Rect((0, 0), (0, 0))

        # => elements <=
        self.elements = []

        # => world info <=
        self.name = None

#
# world: main functions.
#

class world:
    def __init__(self, viewport: pygame.Surface, sharedCore: core, debug=False):
        """world: render out the world and everything."""
        # load all the generic stuff.
        self.core = sharedCore
        self.player = player()

        # => init the debug <=
        self.debug = debugReporter(debug)
        self.debug.location = "world"
        self.debug.write("Hello! You enabled debug!")
        
        # viewport and drawing stuff.
        self.viewport = viewport

        # world storage
        self.world = None
        self.scriptPool = []

        # define the skybox.
        self.skyBox = skyBox(self.viewport)

        # debug functions!
        self.hideWorld = False
        self.hidePlayer = False
        self.debugHitboxes = False

        # shared events.
        self.crash = None
        self.makeSure = None
        
        # => terminal instance
        self.scriptOutput = None

    #
    # init functions
    #

    def loadWorldByName(self, name, format=".json"):
        """loadWorldByName: load the world by it's name."""

        extractTarget = self.core.baseDir + "map" + os.sep + name + format
        self.makeSure(os.path.isfile(extractTarget), "File not found: %s" % extractTarget)

        self.debug.write("loading map file: %s" % extractTarget)
        extractedInfo = jsonLoad(extractTarget)

        self.loadWorldByData(extractedInfo)
    
    def loadPlayerSpawn(self, world: wStore):
        # TODO: this function.
        pass

    def spawnElements(self, world: wStore):
        """spawnElements: load all the world elements."""
        self.debug.write("there are %d elements to load." % len(world.elementData))
        for element in world.elementData:
            self.newElement(world, element)
        
    def finalize(self, world: wStore):
        """finalize: do some final stuff to the world.""" 
        self.skyBox.background = world.skyboxData.get("backgroundColor")
        self.makeSure(self.skyBox.background and isinstance(self.skyBox.background, list), "invalid skybox background color.")
        self.skyBox.enabledClouds = world.skyboxData.get("enableClouds")
        world.cameraRect = pygame.Rect((0, 0), world.background.get_size())
    
    # functions for the interpreter #
    def __sysc_show_hello(self, instance: interpreter):
        instance.regs[0] = "Hello Dude!"
    
    def __sysc_get_position(self, instance: interpreter):
        # => return the world position of the player.
        
        # NOTE: to find the player position relative to the map, we just need to
        # remove the player distance on the screen and convert it to the map
        # constants!

        playerX = 0 + self.world.cameraRect.x
        playerX = abs(playerX - self.player.rect.x)
        
        playerY = 0 + self.world.cameraRect.y
        playerY = abs(playerY - self.player.rect.y)

        # set to r0 the Xpos and r1 the Ypos
        instance.regs[0] = playerX
        instance.regs[1] = playerY
    
    def __sysc_set_health(self, instance: interpreter): 
        # => set the player health
        self.player.health = instance.regs[0]
    
    def __sysc_get_health(self, instance: interpreter):
        instance.regs[0] = self.player.health

    def __sysc_spawn_element(self, instance: interpreter):
        self.debug.write("thread %s is spawning element..." % instance.name)
        targetInPool = instance.regs[0]
        self.debug.write("element: %s" % targetInPool)
        targetInPool = self.world.poolData.get(targetInPool)
        # case the element wasn't found.
        if targetInPool == None:
            instance.regs[0] = 0
            return
        # set the data.
        posx = instance.regs[1]
        if posx == 'keep-pos':
            # NOTE: keep position doesn't change anything.
            pass
        else:
            posy = instance.regs[2]
            element = targetInPool.get("data")
            element['position'][0] = posx
            element['position'][1] = posy
        self.newElement(self.world, targetInPool.get("data"))
        

    def injectCoreFunctions(self, instance: interpreter):
        self.debug.write("injecting the core functions on thread: %s" % instance.name)

        # => set the variables.
        instance.set_var("INSIDE_OVERLORD", 1)
        instance.set_var("USING_VM", "1")

        # => load the opcodes!
        n_opcodes = len(instance.syscalls)
        table = [
            ["sysc_show_hello",     self.__sysc_show_hello],
            ["sysc_get_position",   self.__sysc_get_position],
            ["sysc_set_health",     self.__sysc_set_health],
            ["sysc_get_health",     self.__sysc_get_health],
            ["sysc_spawn_element",  self.__sysc_spawn_element]
        ]
        for tableIndex in range(0, len(table)):
            instance.syscalls.append(table[tableIndex][1])
            instance.set_var(table[tableIndex][0], n_opcodes + tableIndex)

        # => print function()
        instance.new_label("print", ["sysc", "0", "retn"])

    def loadScript(self, name: str, script: str) -> interpreter:
        """loadScripts: load the scriptlet."""
        extractTarget = self.core.baseDir + "map" + os.sep + "scripts/" + script + ".vl"
        self.debug.write("loading script: %s" % extractTarget)
        if os.path.isfile(extractTarget):
            # => begin to load the script <=
            protoScript = load_file(extractTarget)

            # => inject some stuff inside the intepreter <=
            protoScript.output = self.scriptOutput
            protoScript.name = name

            # => print function <=
            self.injectCoreFunctions(protoScript)
            self.debug.write("finished loading script %s!" % name)
            
            return protoScript
        else:
            self.crash("script '%s' file not found: '%s'" % (name, extractTarget))

    def initScripts(self, world: wStore):
        """initScripts: init the script."""
        for script in world.scriptData:
            # => script load information.
            scriptName = script.get("name")
            scriptTarget = script.get("target")
            
            # => load the file.
            script = self.loadScript(scriptName, scriptTarget)

            # => append the script here.
            self.scriptPool.append(script)

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

        self.makeSure(protoWorld.backgroundData != None,    "Background not defined.")
        self.makeSure(protoWorld.elementData != None,       "Element not defined.")
        self.makeSure(protoWorld.playerData != None,        "Player not defined.")
        self.makeSure(protoWorld.skyboxData != None,        "Skybox not defined.")
        self.makeSure(protoWorld.infoData != None,          "Info not defined.")
        self.makeSure(protoWorld.scriptData != None,        "Script not defined.")
        self.makeSure(protoWorld.poolData != None,          "Pool not defined.")

        protoWorld.name = protoWorld.infoData.get("name")
        self.makeSure(protoWorld.name != None, "World has no name set up!")

        # -- init the world loading process! --
        # generateBackground() -> spawnElements() -> finalize()
        self.generateBackground(protoWorld)
        self.debug.write("loaded background!")

        self.spawnElements(protoWorld)
        self.debug.write("loaded elements!")
        
        self.finalize(protoWorld)
        self.debug.write("finalized loading.")

        # -- init the player! --
        # loadPlayerSprites() -> loadPlayerSpawn()
        self.loadPlayerSpawn(protoWorld)
        self.debug.write("loading player spawn...")

        # -- init the scripts --
        self.initScripts(protoWorld)
        self.debug.write("loading the scripts...")

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

        self.makeSure(_W  != None and isinstance(_W, int),  "Background width was not set or invalid value!")
        self.makeSure(_H  != None and isinstance(_H, int),  "Background height was not set or invalid value!")
        self.makeSure(_TW != None and isinstance(_TW, int), "Background tiles width was set or invalid value!")
        self.makeSure(_TH != None and isinstance(_TH, int), "Background tiles height was not set or invalid value!")

        # TODO: implement the other ways to generate the world!
        if generationInstruction.get("method") == "random":
            # TODO: this way of rendering the tiles are not very good
            # in games that have a large map, so on the next versions
            # implement the chunk rendering system!
            self.debug.write("background is using the random generation.")
        
            world.background = pygame.Surface(((_W + 1) * _TW, (_H + 1) * _TH))
        
            for yIndex in range(0, _H+1):
                for xIndex in range(0, _W+1):
                    textureChoice = __randomGenerator.choice(texturesLoad)
                    world.background.blit(textureChoice, (_TW * xIndex, _TH * yIndex))

        elif generationInstruction.get("method") == "mapped":
            # NOTE: load the blocks texture.
            self.debug.write("background is using the mapped generation.")

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
                    self.debug.write("yLine has finished before expected: %d -> %d" % (yIndex, len(matrix)))
                    break
            
                for xIndex in range(0, _W + 1):
                    # NOTE: prevent from errors.
                    if xIndex >= len(matrix[yIndex]):
                        self.debug.write("xLine has finished before expected: %d -> %d" % (xIndex, len(matrix[yIndex])))
                        break

                    blockRequest = matrix[yIndex][xIndex]
                    textureAdquired = blockDict[blockRequest]
                    
                    if isinstance(textureAdquired, list):
                        if len(textureAdquired) <= 1:
                            texture = textureAdquired[0]
                        else:
                            texture = __randomGenerator.choice(textureAdquired)
                    
                    world.background.blit(texture, (xIndex * _TW, yIndex * _TH))
        else:
            self.crash("Unknown background generation method: '%s' in '%s' level." % (generationInstruction.get("method"), world.name))
    
    def init(self):
        """init: init the player and the world."""
        # player init!
        self.player.playerTextureGenerate()
        self.player.centerPlayer(self.viewport.get_width(), self.viewport.get_height())

        self.debug.write("loading temporary map...")
        self.loadWorldByName("initial-room")

    #
    # utility functions
    #

    def getInWorldPosition(self):
        # return the player relative to world position.
        if self.world:
            playerX = 0 + self.world.cameraRect.x
            playerX = abs(playerX - self.player.rect.x)
            
            playerY = 0 + self.world.cameraRect.y
            playerY = abs(playerY - self.player.rect.y)

            # => return the x and y.
            return (playerX, playerY)
        else:
            return (0, 0)

    #
    # tick functions
    #

    def newElement(self, world: wStore, element: dict):
        ## !! EXTRACT INFO !! ##
        textureInfo = element.get("texture")
        elementSize = element.get("size")
        elementPos  = element.get("position")
        tileSize    = world.backgroundData.get("tileSize")

        self.debug.write("new element spawned: " + str(element.get("name")))

        ## !! BEGIN TO BUILD THE ELEMENT !! ##
        protoElement = wElement()

        protoElement.name               = element.get("name")
        self.makeSure(protoElement.name != None, "no name provided for element in level '%s'" % world.name)
        
        protoElement.genericName        = element.get("generic") or protoElement.name
        protoElement.textureType        = ELEMENT_TEX_IMAGE if textureInfo.get("type")=='image' else ELEMENT_TEX_SPRITE
        protoElement.textureUpdateTime  = element.get("textureUpdateTime") or 0.5
        protoElement.texture            = self.core.storage.getContentByRequest(textureInfo)
        
        self.makeSure(protoElement.texture != False, "unable to load texture: %s" % textureInfo)

        protoElement.position           = elementPos
        protoElement.size               = elementSize

        # => load the collision rectangle <=
        if not self.world:
            # NOTE: there is no need to calculate the world offset when
            # the world isn't loaded yet.
            xDrawPosition = (tileSize[0] * elementPos[0])
            yDrawPosition = (tileSize[1] * elementPos[1])
        else:
            # determine how much the world has moved since the beginning
            # and apply this change to the element, setting it to it's 
            # point!
            moveQuantityX = 0 + world.cameraRect.x
            moveQuantityY = 0 + world.cameraRect.y
            xDrawPosition = moveQuantityX + (tileSize[0] * elementPos[0])
            yDrawPosition = moveQuantityY + (tileSize[1] * elementPos[1])

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
                xSize = collisionData.get("xSize")  ;   ySize = collisionData.get("ySize")
                xPos  = collisionData.get("xPos")   ;   yPos  = collisionData.get("yPos")

                # NOTE: the offset is made from the (0, 0) position.
                xPosition = xDrawPosition + xPos
                yPosition = yDrawPosition + yPos
            else:
                # TODO: crash here.
                self.crash("Invalid collision method in element: %s" % element.get("name"))

            # build the rect here.
            protoElement.collisionRect = pygame.Rect((xPosition, yPosition), (xSize, ySize))

        # => load the drawing rectangle <=
        protoElement.drawRect = pygame.Rect(( xDrawPosition, yDrawPosition), elementSize)

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
    
    def __checkElementCollisions(self, world: wStore, rect: pygame.Rect):
        for element in world.elements:
            if rect.colliderect(element.collisionRect):
                return True
        return False

    def walk(self, world: wStore, xDir: int, yDir: int):
        """preciseWalk: basically, the walk but with more precion."""
        walkX = 0
        walkY = 0

        # NOTE: case walk 0, then ignore.
        if xDir != 0:
            maxWalkX    = 0
            xWalk       = abs(xDir)
            for xTest in range(0, xWalk):
                playerCollisionTest     = self.player.rect.copy()
                playerCollisionTest.x  -= xTest if xDir > 0 else -(xTest)
                if not world.cameraRect.contains(playerCollisionTest):
                    break
                if self.__checkElementCollisions(world, playerCollisionTest):
                    break
                maxWalkX = xTest
            walkX = -(maxWalkX) if xDir <= 0 else maxWalkX

        if yDir != 0:
            maxWalkY    = 0
            yWalk       = abs(yDir)
            for yTest in range(0, yWalk):
                playerCollisionTest     = self.player.rect.copy()
                playerCollisionTest.y  -= yTest if yDir > 0 else -(yTest)
                if not world.cameraRect.contains(playerCollisionTest):
                    break
                if self.__checkElementCollisions(world, playerCollisionTest):
                    break
                maxWalkY = yTest
            walkY = -(maxWalkY) if yDir <= 0 else maxWalkY

        world.cameraRect.x += walkX
        world.cameraRect.y += walkY
        self.moveWorld(world, walkX, walkY)
    
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
        self.debug.write("reseting draw...")
        self.skyBox.deleteClouds()

        # hide the player.
        self.hidePlayer = False
        self.hideWorld  = False
    
    def tickScripts(self):
        # 1° run the script
        SCRIPT_STEP_PER_TICK = 10
        HOLD_SCRIPT_EXCEPTIONS = True

        timeTaken = 0
        for script in self.scriptPool:
            beginTime = time.time()
            if HOLD_SCRIPT_EXCEPTIONS:
                for tick_counter in range(0, SCRIPT_STEP_PER_TICK):
                    try:
                        result = script.step()
                        if not result: break
                    except Exception as E:
                        self.crash("[%d] script %s, error: %s" % (tick_counter, script.name, str(E)))
            else:
                for tick_counter in range(0, SCRIPT_STEP_PER_TICK):
                    result = script.step()
                    if not result: break
            timeTaken += ( (time.time() - beginTime) * 1000)
        
        # NOTE: record the time taken by the scripts.
        self.core.timeTakenByScripts = timeTaken

        # 2° check for dead scripts
        for script in self.scriptPool:
            if not script.running:
                self.debug.write("%s has finished task, removing!" % script.name)
                self.scriptPool.remove(script)

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
                if event.key == pygame.K_F4:
                    self.resetHides()
                if event.key == pygame.K_F5:
                    self.debugHitboxes = not self.debugHitboxes
                if event.key == pygame.K_F6:
                    self.skyBox.enabled = not self.skyBox.enabled
                if event.key == pygame.K_p:
                    self.newElement(self.world, {
                        "name":                 "table_left",
                        "generic":              "table00left00",
                        "position":             [2, 0],
                        "size":                 [128, 128],
                        "collision": {
                            "enabled":          True,
                            "use":              "modified",
                            "xSize":            78,
                            "ySize":            128,
                            "xPos":             50,
                            "yPos":             0
                        },
                        "textureUpdateTime":    0.3,
                        "texture":              {"type":"sprite","name":"r_table","only":["table00"]}
                    })
                    
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
        
        # NOTE: the scripts should always catch the procesed data.
        self.tickWorldElements(self.world)
        self.tickScripts()

    #
    # draw functions
    #
    
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
            if element.textureType == ELEMENT_TEX_SPRITE:
                self.viewport.blit(element.texture[element.textureIndex], element.drawRect)
            else:
                self.viewport.blit(element.texture, element.drawRect)

    def drawWorld(self, world: wStore):
        """drawWorld: draw the player."""
        if not self.hideWorld:
            self.viewport.blit(world.background, world.cameraRect)
            self.drawWorldElements(self.world)
    
    def __showHitboxes(self, world: wStore):
        for element in world.elements:
            # NOTE: draw the hitbox.
            hitbox = pygame.Surface((element.collisionRect.w, element.collisionRect.h), pygame.SRCALPHA)
            hitbox.fill((0, 0, 0, 100))
            self.viewport.blit(hitbox, element.collisionRect)

    def draw(self):
        """draw: draw the game elements."""
        timeBegin = time.time()
        if self.core.running:
            # cleanViewport [clean stage]
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