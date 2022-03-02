import pygame
import os
import random
import time

#
# import modules from the project.
#

from .core import core
from .utils import *
from .gui import *
from .modules import *
from .world import *

#
# A main engine function (...)
#

class engine:
    def __init__(self, sharedCore: core, debug=False):
        # => set the core function.
        self.core = sharedCore

        # => set the viewport.
        self.viewport = pygame.Surface(self.core.window.surface.get_size(), pygame.SRCALPHA)
        self.viewportPos = [0, 0]

        # => init the world
        self.world = world(self.viewport, sharedCore, debug=debug)

        # => dialog system
        self.dialogBuffer = []
        self.dialogCharacters = []
        
        # the dialog animation!
        self.dialogAtPhrase = 0
        self.dialogCharacterIndex = 0
        self.dialogCharacterSpeed = 0.01
        self.dialogCharacterTime = 0

        self.dialogCharBeginX = 25
        self.dialogCharBeginY = 0

        self.inDialog = False
        self.dialogFrozen = False

        # => set the debug.
        self.debug = debugReporter(debug)
        self.debug.location = 'engine'
        self.debug.write("Debugging the engine!")

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
            "Project Overlord? more like overload my memory!",
            "Drive Slow",
            "xeS in Borneo"
        ]
        phrase = random.choice(__messages)
        self.debug.write("game phrase selected: '%s'" % phrase)
        return phrase

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
                if event.type == pygame.VIDEORESIZE:
                    # TODO: this may crash the machine?
                    # BUG: this will render garbage on the screen.
                    self.debug.write("video resizing on crash?")
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

    def __initPlayerStatusDisplay(self):
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

        self.errorMessage = label(self.coreDisplay, mediumFont, self.__getRandomMessage())
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
        """initDebugDisplay: all the elements for the debug display."""
        # => init the core display and load the fonts!
        self.debugFrame = frame(self.coreDisplay)
        self.debugFrame.visible = False
        mediumFont  = self.core.storage.getFont("normal", 16)
        
        # => renderize the fixed texts!
        fixedTexts = [
            "Reaper I, %s" % REAPER_VERSION[0],
            "Python %s, pygame: %s" % (getPythonVersion(), pygame.version.ver),
            "Debugging? %s" % str(self.debug.enabled),
            "Screen: W = %d, H = %d [Fixed]" % self.viewport.get_size()
        ]

        tElements   = []
        yPos        = 0
        for text in fixedTexts:
            # init the element.
            element = label(self.coreDisplay, mediumFont, text)
            element.position = [0, yPos]
            element.render()

            # set the debug frame.
            yPos += element.surface.get_height()
            self.debugFrame.addElement(element)

        # => non fixed elements, this will change in some parts in debugging!
        self.playerPositionDebugLabel = label(self.coreDisplay, mediumFont, "X: 0, Y: 0")
        self.playerPositionDebugLabel.position = [0, yPos]
        self.playerPositionDebugLabel.render()

        self.mousePositionDebugLabel = label(self.coreDisplay, mediumFont, "MX: 0, MY: 0")
        self.mousePositionDebugLabel.render()
        self.mousePositionDebugLabel.position = [0, self.playerPositionDebugLabel.position[1]+self.mousePositionDebugLabel.surface.get_height()]
    
        # => show the graph and it's value!
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

        self.debugFrame.addElement(self.drawDebugGraph)
        self.debugFrame.addElement(self.drawDebugGraphValueLabel)

        self.debugFrame.addElement(self.fpsDebugGraph)
        self.debugFrame.addElement(self.fpsDebugGraphValueLabel)

        self.debugFrame.addElement(self.tickDebugGraph)
        self.debugFrame.addElement(self.tickDebugGraphValueLabel)

        self.debugFrame.addElement(self.playerPositionDebugLabel)
        self.debugFrame.addElement(self.mousePositionDebugLabel)

        self.coreDisplay.addElement(self.debugFrame)
    
    def __initDialogDisplay(self):
        self.dialogFrame = frame(self.coreDisplay)
        
        # NOTE: dialog size and position is /4 of the screen.
        self.dialogFrame.background = pygame.Surface((
            self.viewport.get_width(), self.viewport.get_height()//3
        ), pygame.SRCALPHA)

        self.dialogFrame.background.fill((0, 0, 0))
        self.dialogFrame.backgroundPosition=[0, (self.viewport.get_height()//3)*2]
        self.dialogFrame.visible=False

        # load font
        mediumFont  = self.core.storage.getFont("normal", 24)

        self.dialogFromLabel = label(self.coreDisplay, mediumFont, "...")

        self.dialogFromLabel.position[0] = 25
        self.dialogFromLabel.position[1] = 25 + self.dialogFrame.backgroundPosition[1]

        self.dialogFrame.addElement(self.dialogFromLabel)
        self.coreDisplay.addElement(self.dialogFrame)

        # => apply vars
        self.dialogCharBeginX = 25
        self.dialogCharBeginY = self.dialogFromLabel.position[1] + 50

    def initDisplayComponents(self):
        """initDisplayComponents: init all the display components."""
        # => init the core display <=
        self.coreDisplay = display(self.viewport)
        
        # => init the player data <=
        self.__initPlayerStatusDisplay()

        # => init the panic display <=
        self.__initPanicDisplay()

        # => init debug display <=
        self.__initDebugDisplay()

        # => init the dialog display <=
        self.__initDialogDisplay()

    def makeSure(self, condition, atError: str):
        """makeSure: automatically crash the program."""
        if not condition:
            self.crash(atError)
    
    def makeDialog(self, dialog: list):
        """makeDialog: lock the world input & make dialog."""
        # lock player input!
        self.world.inputLocked = True

        # load the new dialog buffer
        self.dialogBuffer = dialog
        
        # reset the dialog variables.
        self.dialogCharacterIndex   = -1
        self.dialogAtPhrase = 0

        # set the frame to be visible
        # and enable the dialog mode!
        self.dialogFrame.visible = True
        self.inDialog = True

    def init(self):
        # set the viewport to the display & init the world display.
        self.initDisplayComponents()

        # connect necessary functions world -> engine
        self.world.crash = self.crash
        self.world.makeSure = self.makeSure
        self.world.makeDialog = self.makeDialog

        # make sure to use the terminal!
        self.world.scriptOutput = sys.stdout

        # => init the world components!
        self.world.init()
    
    #
    # tick functions
    #

    def __tickDebugFrame(self):
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
    
    def __endDialog(self):
        # => reset the values.
        self.dialogAtPhrase = 0
        self.dialogCharacterIndex = 0
        self.dialogFrozen = False

        # => unlock & disable stuff.
        self.inDialog = False
        self.dialogFrame.visible = False
        self.world.inputLocked = False

    def __tickDialog(self):
        """__tickDialog: update the dialog!"""
        messageAt = self.dialogBuffer[self.dialogAtPhrase].get("message")
        if not self.dialogFrozen:
            if self.dialogCharacterIndex + 1 > len(messageAt):
                # froze the dialog, because there are no dialog anymore.
                self.dialogFrozen = True
            else:
                self.dialogCharacterIndex += 1
        
        if self.dialogAtPhrase >= len(self.dialogBuffer):
            self.__endDialog()

    def updateDialog(self, events):
        if pygame.time.get_ticks() > self.dialogCharacterTime:
            self.__tickDialog()
            self.dialogCharacterTime = pygame.time.get_ticks() + (1000 * self.dialogCharacterSpeed)
    
    def skipDialogLine(self):
        self.debug.write("skipping dialog...")
        if self.dialogAtPhrase + 1 >= len(self.dialogBuffer): 
            # end the dialog.
            self.__endDialog()
        else:
            # => reset the values and unfreeze the dialog system
            self.dialogFrozen = False
            self.dialogCharacterIndex = 0
            self.dialogAtPhrase += 1

    def tick(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.core.running = False
                return
            
            if event.type == pygame.VIDEORESIZE:
                if event.w >= self.viewport.get_width() or event.h >= self.viewport.get_height():
                    self.debug.write("resizing [w: %d, h: %d]" % (event.w, event.h))
                    self.atVideoResizeEvent(event.w, event.h)
                else:
                    self.debug.write("ignoring resize as the new size is lower than fixed viewport.")
                    self.core.window.setMode(self.viewport.get_width(), self.viewport.get_height())
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    self.debugFrame.visible = not self.debugFrame.visible
                if event.key == pygame.K_SPACE:
                    # => case dialog is enabled!
                    if self.inDialog:
                        self.skipDialogLine()
        
        # set the world tick & update the core display.
        self.__tickDebugFrame()
        if self.inDialog:
            self.updateDialog(events)

        # => update the player stuff
        self.updatePlayerStatusFrame()
        self.coreDisplay.tick(events)

        # => update the tick
        self.world.tick(events)
    
    #
    # draw functions
    #

    def __drawDialog(self):
        # TODO: fix the strange BUMP in the text when bold text is set.
        # TODO: implement more ways to see the text, such as italic!

        # set the dialog box.
        dialog      = self.dialogBuffer[self.dialogAtPhrase]
        dialogFrom  = dialog.get("from")
        dialogText  = dialog.get("message")

        # load the effects
        effects = {} if dialog.get("effects") == None else dialog.get("effects")

        enableShaking = "shake" in effects.keys()
        shakingLevel  = effects['shake']['level'] if enableShaking else 0

        # => load the font <=
        mediumFont = self.core.storage.getFont("normal", 16)

        # begin indexing the position!
        xIndex = self.dialogCharBeginX
        yIndex = self.dialogCharBeginY

        for index in range(0, self.dialogCharacterIndex):
            # NOTE: there are a char the indicate a newline, '/' one!
            renderedChar = mediumFont.render(dialogText[index], True, (255, 255, 255))
            if dialogText[index] == '/':
                xIndex = self.dialogCharBeginX
                yIndex += renderedChar.get_height()
            elif dialogText[index] == '*':
                mediumFont.set_bold(not mediumFont.get_bold())
            elif dialogText[index] == '_':
                mediumFont.set_italic(not mediumFont.get_italic())
            else:
                self.viewport.blit(
                    renderedChar,
                    (
                        xIndex + (random.randint(-shakingLevel, shakingLevel) if enableShaking else 0),
                        yIndex + (random.randint(-shakingLevel, shakingLevel) if enableShaking else 0)
                    )
                )
                xIndex += renderedChar.get_width()

        # => set the from label!
        self.dialogFromLabel.setText(dialogFrom)

    def draw(self):
        if self.core.running:
            # draw the world
            self.world.draw()

            # update the display
            self.coreDisplay.draw()
        
            # in dialog?
            if self.inDialog:
                self.__drawDialog()

            # draw the viewport.
            self.core.window.surface.blit(
                self.viewport,
                self.viewportPos
            )

            # set the display.
            pygame.display.flip()