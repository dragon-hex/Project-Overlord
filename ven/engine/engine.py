# import modules from the project.
from ven.gui import *
from ven.world import world
from ven.utils import *

from .core import core
from .dialog import dialog


ENGINE_VERSION = ["1.0", 1.0, 10]

# import pygame & other modules.
import pygame
import os, random, time

class engine:
    def __init__(self, sharedCore: core, debug=False):
        """
        engine: controls all the guis and the world.
        """
        # set the core function
        self.core = sharedCore

        # set the viewport.
        self.viewport = pygame.Surface(self.core.window.surface.get_size(), pygame.SRCALPHA)
        self.viewportPos = [0, 0]

        # init the world.
        self.world = world(self.viewport, sharedCore, debug=debug)

        # dialog system.
        self.dialogSystem=None

        # set the debug.
        self.debug = debugReporter(debug)
        self.debug.location = 'engine'
        self.debug.write("Debugging the engine!")

    ###########
    # utility #
    ###########

    def unlockPlayer(self):
        self.world.inputLocked = False
        self.world.player.busy = False
    
    def lockPlayer(self):
        self.world.inputLocked = True
        self.world.player.busy = True

    def crash(self, reason: str):
        """show the error screen exposing the error and try to save the game."""
        
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
                if event.type == pygame.VIDEORESIZE:
                    # TODO: this may crash the machine?
                    # BUG: this will render garbage on the screen.
                    self.debug.write("video resizing on crash?", isWarn=True)
                    self.core.window.setMode(self.viewport.get_width(), self.viewport.get_height())
            
            # => clean the viewport <=
            self.core.window.surface.fill((0, 0, 0))
            self.viewport.fill((0, 0, 0))

            self.coreDisplay.tick(events)
            self.coreDisplay.draw()

            self.core.window.surface.blit(self.viewport, self.viewportPos)
            pygame.display.flip()
        
        # quit the program due instable envirolment.
        exit(-1)

    def makeSure(self, condition, atError: str):
        if not condition: self.crash(atError)

    ##################
    # init functions #
    ##################

    def __initPlayerStatusDisplay(self):
        """init the elements of the player status frame."""
        # => show the player name & health
        self.playerStatusFrame = frame(self.coreDisplay)
        self.playerStatusFrame.background = pygame.Surface((100, 45), pygame.SRCALPHA)

        mediumFont = self.core.storage.getFont("normal", 16)

        self.playerStatusNameLabel = label(self.coreDisplay, mediumFont, self.world.player.name)
        self.playerStatusNameLabel.position = [50, 96]
        self.playerStatusNameLabel.fixedPosition = True

        self.playerHealthBar = loadbar(self.coreDisplay)
        self.playerHealthBar.backgroundColor = [100, 100, 100, 100]
        self.playerHealthBar.size = [200, 10]
        self.playerHealthBar.position = [50, 99]
        self.playerHealthBar.fixedPosition = True
        
        self.playerHealthBar.maxValue = self.world.player.maxHealth

        self.playerStatusFrame.addElement(self.playerHealthBar)
        self.playerStatusFrame.addElement(self.playerStatusNameLabel)
        self.coreDisplay.addElement(self.playerStatusFrame)

    def __initPanicDisplay(self):
        """init the elements of the panic frame."""
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
        self.mainInformativeText.foreground = [0, 0, 0]
        self.mainInformativeText.fixedPosition = True
        self.mainInformativeText.position = [50, 30]

        self.errorMessage = label(self.coreDisplay, mediumFont, getRandomMessage())
        self.errorMessage.foreground = [0, 0, 0]
        self.errorMessage.fixedPosition = True
        self.errorMessage.position = [50, 35]

        self.mainErrorLabel = label(self.coreDisplay, hugeFont, "Error")
        self.mainErrorLabel.foreground = [0, 0, 0]
        self.mainErrorLabel.fixedPosition = True
        self.mainErrorLabel.position = [50, 60]

        self.mainError = label(self.coreDisplay, littleFont, "Not collected yet.")
        self.mainError.foreground = [0, 0, 0]
        self.mainError.fixedPosition = True
        self.mainError.position = [50, 65]

        self.mainStatus = label(self.coreDisplay, littleFont, "N/A...")
        self.mainStatus.fixedPosition = True
        self.mainStatus.position = [1 , 99]
        self.mainStatus.foreground = [0, 0, 0]

        # => append all the elements <=
        self.panicFrame.addElement(self.mainInformativeText)
        self.panicFrame.addElement(self.mainError)
        self.panicFrame.addElement(self.mainStatus)
        self.panicFrame.addElement(self.mainErrorLabel)
        self.panicFrame.addElement(self.errorMessage)
        self.coreDisplay.addElement(self.panicFrame)
    
    def __initDebugDisplay(self):
        """init the elements from the debug frame."""
        # => init the core display and load the fonts!
        self.debugFrame = frame(self.coreDisplay)
        self.debugFrame.visible = False
        mediumFont  = self.core.storage.getFont("normal", 16)
        
        # => renderize the fixed texts!
        fixedTexts = [
            "Vulpes Engine I, %s" % ENGINE_VERSION[0],
            "Python %s, pygame: %s" % (getPythonVersion(), pygame.version.ver),
            "System: %s" % (getSystem()[1]),
            "Debugging? %s" % str(self.debug.enabled),
            "Viewport: W = %d, H = %d [Fixed]" % self.viewport.get_size()
        ]

        yPos        = 0
        for text in fixedTexts:
            # init the element.
            element = label(self.coreDisplay, mediumFont, text)
            element.position = [0, yPos]
            element.render()

            # set the debug frame.
            yPos += element.surface.get_height()
            self.debugFrame.addElement(element)

        # load some unfixed elements.
        self.playerPositionDebugLabel = label(self.coreDisplay, mediumFont, "X: 0, Y: 0")
        self.playerPositionDebugLabel.position = [0, yPos]
        self.playerPositionDebugLabel.render()

        self.mousePositionDebugLabel = label(self.coreDisplay, mediumFont, "MX: 0, MY: 0")
        self.mousePositionDebugLabel.render()
        self.mousePositionDebugLabel.position = [0, self.playerPositionDebugLabel.position[1]+self.mousePositionDebugLabel.surface.get_height()]

        self.tickDebugGraph = graph(self.coreDisplay)
        self.tickDebugGraph.setMaxValue(60)
        self.tickDebugGraph.fixedPosition = True
        self.tickDebugGraph.position = [100, 0]
        self.tickDebugGraph.foregroundLines = [255, 0, 0]

        self.tickDebugGraphValueLabel = label(self.coreDisplay, mediumFont, "0")
        self.tickDebugGraphValueLabel.position = [100, 0]
        self.tickDebugGraphValueLabel.fixedPosition = True

        self.drawDebugGraph = graph(self.coreDisplay)
        self.drawDebugGraph.foregroundLines = [0, 0, 255]
        self.drawDebugGraph.setMaxValue(60)
        self.drawDebugGraph.position = [100, 10]
        self.drawDebugGraph.fixedPosition = True

        self.drawDebugGraphValueLabel = label(self.coreDisplay, mediumFont, "0")
        self.drawDebugGraphValueLabel.position = [100, 10]
        self.drawDebugGraphValueLabel.fixedPosition = True

        self.fpsDebugGraph = graph(self.coreDisplay)
        self.fpsDebugGraph.foregroundLines = [0, 255, 0]
        self.fpsDebugGraph.setMaxValue(60)
        self.fpsDebugGraph.position = [100, 20]
        self.fpsDebugGraph.fixedPosition = True

        self.fpsDebugGraphValueLabel = label(self.coreDisplay, mediumFont, "0")
        self.fpsDebugGraphValueLabel.position = [100, 20]
        self.fpsDebugGraphValueLabel.fixedPosition = True

        # add the debug frame.
        self.debugFrame.addElement(self.drawDebugGraph)
        self.debugFrame.addElement(self.drawDebugGraphValueLabel)
        self.debugFrame.addElement(self.fpsDebugGraph)
        self.debugFrame.addElement(self.fpsDebugGraphValueLabel)
        self.debugFrame.addElement(self.tickDebugGraph)
        self.debugFrame.addElement(self.tickDebugGraphValueLabel)
        self.debugFrame.addElement(self.playerPositionDebugLabel)
        self.debugFrame.addElement(self.mousePositionDebugLabel)

        # finish by appending the debugFrame.
        self.coreDisplay.addElement(self.debugFrame)
    
    def initDisplayComponents(self):
        self.coreDisplay = display(self.viewport)
        self.__initPlayerStatusDisplay()
        self.__initPanicDisplay()
        self.__initDebugDisplay()
        # hook dialog system in the world.
        self.dialogSystem=dialog(self, self.debug.enabled)
        self.world.makeDialog=self.dialogSystem.new

    def init(self):
        """init: init all the engine components."""
        self.initDisplayComponents()
        self.world.crash = self.crash
        self.world.makeSure = self.makeSure
        self.world.scriptOutput = sys.stdout
        self.world.init()
    
    #
    # tick functions
    #

    def __tickDebugFrame(self):
        """tick the debug frame."""
        # => update the graph
        self.fpsDebugGraph.setValue(60 - self.core.averageFps)
        self.fpsDebugGraphValueLabel.setText(str(self.core.averageFps))

        self.drawDebugGraph.setValue(self.core.timeTakenByTick)
        self.drawDebugGraphValueLabel.setText(str(self.core.timeTakenByDraw))

        self.tickDebugGraph.setValue(self.core.timeTakenByTick)
        self.tickDebugGraphValueLabel.setText(str(self.core.timeTakenByTick))

        # => update the position
        self.playerPositionDebugLabel.setText("X: %d, Y: %d" % self.world.getInWorldPosition())
        self.mousePositionDebugLabel.setText("MX: %d, MY: %d" % (self.coreDisplay.cursor.rect.x, self.coreDisplay.cursor.rect.y))

    def atVideoResizeEvent(self, newWidth, newHeight):
        # NOTE: resize the window! but not the game viewport!
        newViewportXpos     = newWidth // 2 - (self.viewport.get_width() // 2)
        newViewportYpos     = newHeight // 2 - (self.viewport.get_height() // 2)
        self.viewportPos    = [newViewportXpos, newViewportYpos]
        self.core.window.setMode(newWidth, newHeight)

    def updatePlayerStatusFrame(self):
        self.playerHealthBar.maxValue = self.world.player.maxHealth
        self.playerHealthBar.value = self.world.player.health

    def tick(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.core.running = False
                return
            if event.type == pygame.VIDEORESIZE:
                if event.w >= self.viewport.get_width() or event.h >= self.viewport.get_height():
                    self.debug.write("resizing [w: %d, h: %d]" % (event.w, event.h), isWarn=True)
                    self.atVideoResizeEvent(event.w, event.h)
                else:
                    self.debug.write("ignoring resize as the new size is lower than fixed viewport.", isWarn=True)
                    self.core.window.setMode(self.viewport.get_width(), self.viewport.get_height())
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    self.debugFrame.visible = not self.debugFrame.visible
                if event.key == pygame.K_SPACE:
                    self.dialogSystem.skip()
        
        # set the world tick & update the core display.
        self.__tickDebugFrame()
        self.dialogSystem.tick(events)

        # => update the player stuff
        self.updatePlayerStatusFrame()
        self.coreDisplay.tick(events)

        # => update the tick
        self.world.tick(events)
    
    #
    # draw functions
    #

    def draw(self):
        if self.core.running:
            # draw the world
            self.world.draw()

            # update the display
            self.coreDisplay.draw()
        
            # in dialog?
            self.dialogSystem.draw()

            # draw the viewport.
            self.core.window.surface.blit(
                self.viewport,
                self.viewportPos
            )

            # set the display.
            pygame.display.flip()