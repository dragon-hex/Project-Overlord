import pygame
import os, sys
import math

#
# utils functions
#

def getPosition(baseSurface, targetSurface, position):
    """getPosition: return the position."""
    # divide the screen on 100 parts.
    position= [math.floor(position[0]), math.floor(position[1])]
    xPos    = ( baseSurface.get_width()  )  // 100
    yPos    = ( baseSurface.get_height() )  // 100

    # load the offset from the 0 -> 100 position
    # this is done to prevent the element from "escaping"
    # the 100% limit.
    offsetX = ( (targetSurface.get_width() / 100  ) * position[0] )
    offsetY = ( (targetSurface.get_height() / 100 ) * position[1] )

    # finally, calculate the position.
    xPos    = xPos * position[0] - offsetX
    yPos    = yPos * position[1] - offsetY

    # return the positions floored.
    return [math.floor(xPos), math.floor(yPos)]

#
# display holder
#

class display:
    def __init__(self, atDisplay: pygame.Surface):
        """display: store the display elements."""
        self.atDisplay = atDisplay
        self.elements = []
    
    def addElement(self, element):
        """addElement: insert a element."""
        self.elements.append(element)
    
    def tick(self, events):
        """tick: tick all the events here."""
        for element in self.elements:
            try:
                element.tick(events)
            except Exception as E:
                # TODO: implement a error handler.
                pass
    
    def draw(self):
        """draw: draw all the events here."""
        for element in self.elements:
            try:
                element.draw()
            except Exception as E:
                # TODO: implement a error handler.
                pass

#
# frame element
#

class frame:
    def __init__(self, atDisplay: display, backgroundSize):
        """frame: the frame contains a special drawing surface into it."""
        self.display = atDisplay
        
        # NOTE: init the main display.
        self.atDisplay = pygame.Surface(backgroundSize)
        self.background = pygame.Surface(backgroundSize)
        self.background.fill((255, 255, 255))


        # position and etc.
        self.visible = True
        self.position = [0, 0]
        self.useFixedPosition = True
        self.elements = []
    
    # set/add(s).
    def setFrameSize(self, width, height):
        self.atDisplay = pygame.Surface((width, height))
        self.atDisplay.fill((0, 0, 0))
    
    def setBackgroundColor(self, color):
        self.background.fill(color)

    def addElement(self, element):
        self.elements.append(element)
    
    # tick function(s)
    def tick(self, events):
        if self.visible:
            for element in self.elements:
                try:
                    element.tick(events)
                except Exception as E:
                    continue
    
    # draw function(s)
    def __drawDisplay(self):
        """__drawDisplay: draw the display."""
        self.display.atDisplay.blit(
            self.atDisplay,
            self.position if not self.useFixedPosition else getPosition(self.display.atDisplay, self.atDisplay, self.position)
        )

    def __cleanDisplay(self):
        """__cleanDisplay: empty the display."""
        self.atDisplay.fill((0, 0, 0))
    
    def __drawBackground(self):
        """__drawBackground: draw the background display."""
        self.atDisplay.blit(self.background, (0, 0))

    def draw(self):
        """draw: draw the frame."""
        if self.visible:
            self.__cleanDisplay()
            self.__drawBackground()
            for element in self.elements:
                try:
                    element.draw()
                except Exception as E:
                    continue
            self.__drawDisplay()

#
# label element
#

class label:
    def __init__(self, atDisplay: display | frame, text: str, font: any):
        """label: this element stores text!"""
        self.atDisplay = atDisplay
        self.text = text
        self.font = font
        
        # theme configuration
        self.foregroundColor = [255, 255, 255]
        self.useAntialising = True

        # position & geometry
        self.position = [0, 0]
        self.useFixedPosition = True

        # label stuff.
        self.__needRedraw = True
        self.__surface = None
        self.render()
    
    def render(self):
        """render: render the label."""
        self.__surface = self.font.render(self.text, self.useAntialising, self.foregroundColor)

    def setText(self, text: str):
        """setText: this will also, set the redraw!"""
        self.text = text
        self.__needRedraw = True
    
    def tick(self, events):
        """tick: basically update the label."""
        if self.__needRedraw:
            # NOTE: this prevent the label of taking the time
            # from other places.
            self.render()
            self.__needRedraw = False
        
    def draw(self):
        """draw: draw the label."""
        # TODO: fix this redundancy.
        if self.__surface:
            self.atDisplay.atDisplay.blit(
                self.__surface,
                self.position if not self.useFixedPosition else getPosition(self.atDisplay.atDisplay, self.__surface, self.position)
            )

#
# button element
# 

class button:
    def __init__(self, atDisplay: display | frame, font: any, text: str):
        """button: this is a simple button implementation!"""
        self.atDisplay = atDisplay
        self.text = text
        self.font = font

        # geometry & sizes.
        self.size = [0, 0]
        self.position = [0, 0]
        self.useFixedPosition = False
        
        # theme
        self.backgroundColor = [255, 255, 255]
        self.foregroundColor = [0, 0, 0]
        
        # events!
        self.onRightClick = None
        self.onRightClickArgs = None
        self.onLeftClick = None
        self.onLeftClickArgs = None
        
        # internal workings
        self.__needRedraw = True
        self.__surface = None
    
    def render(self):
        """render: render the element!""" 
        if self.size[0] <= 0 or self.size[1] <= 0:
            # NOTE: if there is no size, then ignore.
            return
        else:
            # NOTE: this keep the surface.
            self.__surface = pygame.Surface(self.size)
            self.__surface.fill(self.backgroundColor)
            renderedText = self.font.render(self.text, True, self.foregroundColor)
            self.__surface.blit(
                renderedText,
                (
                    self.__surface.get_width() // 2 -  renderedText.get_width() // 2,
                    self.__surface.get_height() // 2 - renderedText.get_height() // 2
                )
            )

    def setPosition(self, xPos: int, yPos: int):
        """setPosition: set the position.""" 
        self.position = [xPos, yPos]
        self.__needRedraw = True
    
    def setText(self, text: str):
        self.text = text
        self.__needRedraw = True
    
    def tick(self, events):
        if self.__needRedraw:
            self.render()
        # NOTE: check for the cursor position.
        mouseRect = pygame.Rect()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_RIGHT:
                    self.onRightClick(self.onRightClickArgs)
    
    def draw(self):
        # NOTE: sometimes, the surface can be none.
        if self.__surface:
            self.atDisplay.atDisplay.blit(
                self.__surface,
                self.position if self.useFixedPosition else getPosition(self.atDisplay.atDisplay, self.__surface, self.position)
            )

#
# name collect package.
#

class nameCollect:
    def __init__(self, atDisplay: display, font):
        self.atDisplay = atDisplay
        self.buttons = []
        self.background = None
        self.textInputed = str()
        self.font = font
        self.build()
    
    def __handle(self, button):
        print(button)
    
    def build(self):
        """build: set all the buttons here."""
        # !! LOAD THE BACKGROUND !! ##
        self.background = pygame.Surface(self.atDisplay.atDisplay.get_size())
        self.background.fill((0, 0, 0))

        # !! BUILD THE a-z buttons !! ##
        chars = [ chr(char) for char in range(ord('a'), ord('z')+1) ]
        chars +=[ '_', '!', '@', '#' ]

        positionX = 150
        positionY = 200

        __buttonWidth   = 50
        __buttonHeight  = 50
        __buttonPerLine = 6

        xOffset= 10
        yOffset= 5
        xIndex = 0
        yIndex = 0

        for char in chars:
            # load the Y lines.
            if (xIndex / __buttonWidth) >= __buttonPerLine:
                yIndex += __buttonHeight
                yOffset+= 10
                xIndex = 0
                xOffset = 10

            # build the button.
            buttonPrototype = button(self.atDisplay, self.font, char)
            buttonPrototype.onRightClick = self.__handle
            buttonPrototype.onRightClickArgs = char
            buttonPrototype.useFixedPosition = True
            buttonPrototype.size = [__buttonWidth, __buttonHeight]
            buttonPrototype.position = [
                positionX + (xIndex + xOffset),
                positionY + (yIndex + yOffset)
            ]
            # append the buttons and prepare for the next.
            self.buttons.append(buttonPrototype)
            xIndex += __buttonWidth
            xOffset += __buttonWidth
    
    def tick(self, events):
        """tick: process all the button matrix."""
        for button in self.buttons:
            button.tick(events)
    
    def draw(self):
        """draw: show all the button matrix."""
        self.atDisplay.atDisplay.blit(self.background, (0, 0))
        for button in self.buttons:
            button.draw()
