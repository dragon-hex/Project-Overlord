import pygame
import os, sys
import math

from ord.utils import *

#
# utils functions
#

def getPosition(baseSurface, targetSurface, position):
    """getPosition: return the position."""
    # divide the screen on 100 parts.
    position= [math.floor(position[0]), math.floor(position[1])]
    xPos    = ( baseSurface.get_width()  )  / 100
    yPos    = ( baseSurface.get_height() )  / 100

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
# __basicContainer: basic functions for display & frame.
#

class __basicContainer:
    def __init__(self):
        self.elements = []
        # !! controllers !!
        self.doTickElements = True
        self.doDrawElements = True
        # !! error handlers !!
        self.onTickError = None
        self.onDrawError = None
    
    def addElement(self, element):
        """addElement: insert a element on the frame/display."""
        self.elements.append(element)
    
    #
    # tick function
    #
    def __handleExceptionAtTick(self, exception):
        """__handleExceptionAtTick: when a tick error happens."""
        print("Exception %s" % str(exception))
        if self.onTickError:
            if callable(self.onTickError):
                invokeSafe(self.onTickError, exception)

    def tickElements(self, events):
        """tick function!"""
        if self.doTickElements:
            for element in self.elements:
                try:
                    # try to invoke the .tick() function
                    element.tick(events)
                except Exception as E:
                    self.__handleExceptionAtTick(E)
    
    #
    # draw function
    #
    def __handleExceptionAtDraw(self, exception):
        """__handleExceptionAtDraw: when a draw error happens."""
        print("Exception %s" % str(exception))
        if self.onDrawError:
            if callable(self.onDrawError):
                invokeSafe(self.onDrawError, exception)

    def drawElements(self):
        """draw function!"""
        if self.doDrawElements:
            for element in self.elements:
                try:
                    # again, try to invoke .draw() function
                    element.draw()
                except Exception as E:
                    self.__handleExceptionAtDraw(E)

#
# cursor: use the cursor to point at something!
#

CURSOR_DEFAULT = 0
CURSOR_WAITING = 1

class cursor:
    def __init__(self):
        # !! sizes & positions !! ##
        self.size = [12, 12]
        self.rect = pygame.Rect((0, 0), self.size)
        self.textures = []
        self.cursorState = CURSOR_DEFAULT
        self.cursorTextureIndex = 0
        self.cursorTiming = 0

        # cursor offset: this determines the offset created
        # by the video resizing!
        self.offsetInX = 0
        self.offsetInY = 0

        self.__initTemporaryTexture()
    
    def __initTemporaryTexture(self):
        """__initTemporaryTexture: init a simple texture."""
        pixelBlock = pygame.Surface(self.size)
        pixelBlock.fill(randomRGBColor())
        self.textures = [
            [pixelBlock.copy(), pixelBlock.copy()], # -> DEFAULT MODE...
            [pixelBlock.copy(), pixelBlock.copy()]  # -> WAITING MODE...
        ]
    
    def tick(self):
        """tick: the mouse position."""
        (self.rect.x, self.rect.y) = pygame.mouse.get_pos()
        
        self.rect.x -= (self.rect.width // 2)
        self.rect.x += self.offsetInX

        self.rect.y -= (self.rect.height // 2)
        self.rect.y += self.offsetInY

#
# display: stores the display?
#

class display(__basicContainer):
    def __init__(self, atSurface: pygame.Surface):
        # init the top class.
        super().__init__()
        # !! names & types !! ##
        self.name = 'display'
        self.type = 'display'
        # !! destination !! ##
        self.atSurface = atSurface
        self.cursor = cursor()
    
    def adjustCursor(self, neww: int, newh: int):
        # try to find the position of the viewport
        # in the new resized window.
        possibleNewX = neww // 2 - (self.atSurface.get_width() // 2)
        possibleNewY = newh // 2 - (self.atSurface.get_height() // 2)
        self.cursor.offsetInX = 0 - possibleNewX
        self.cursor.offsetInY = 0 - possibleNewY

        # adjust the position of the elements and their offsets.
    
    def tick(self, events):
        """tick: tick the main display."""
        # NOTE: process the video resize!
        self.cursor.tick()

        for event in events:
            if event.type == pygame.VIDEORESIZE:
                if event.w >= self.atSurface.get_width() or event.h >= self.atSurface.get_height():
                    self.adjustCursor(event.w, event.h)

        self.tickElements(events)
    
    def __drawCursor(self):
        """__drawCursor: draw the cursor."""
        ## process the textures index ##
        if pygame.time.get_ticks() > self.cursor.cursorTiming:
            self.cursor.cursorTextureIndex = (
                0 if self.cursor.cursorTextureIndex + 1 >= len(self.cursor.textures[self.cursor.cursorState]) 
                else self.cursor.cursorTextureIndex + 1
            )
            self.cursor.cursorTiming = pygame.time.get_ticks() + (0.2 * 1000)
        ## display the cursor ##
        self.atSurface.blit(
            self.cursor.textures[self.cursor.cursorState][self.cursor.cursorTextureIndex], 
            self.cursor.rect
        )

    def draw(self):
        """draw: draw the display.""" 
        self.drawElements()
        self.__drawCursor()

#
# frame: store the elements easy!
#

class frame(__basicContainer):
    def __init__(self, atDisplay: display):
        super().__init__() # => init the basic container.
        self.atDisplay = atDisplay
        self.background = None
        self.backgroundPosition = [0, 0]
        self.fixedPosition = False
        self.visible = True
        self.position = None
    
    def calculatePosition(self):
        # => load the position quickly!
        self.position = (
            self.backgroundPosition
            if not self.fixedPosition else 
            getPosition(self.atDisplay.atSurface, self.background, self.backgroundPosition)
        )

    def tick(self, events):
        # => case there is no position!
        if not self.position:
            self.calculatePosition()

        if self.visible:
            self.tickElements(events)
    
    def draw(self):
        if self.visible:
            if self.background and self.position:
                self.atDisplay.atSurface.blit(self.background, self.position)
            self.drawElements()

#
# button: shows a button!
#

class button:
    def __init__(self, atDisplay: display, font, string):
        """
        button: shows your typical button.
        """
        self.atDisplay = atDisplay
        self.font = font
        self.string = string
        self.size = [50, 10]
        self.backgroundColor = [0, 0, 0]
        self.foregroundColor = [255, 255, 255]
        self.position = [0, 0]
        self.fixedPosition = False
        self.__needRedraw = True
        self.rect = pygame.Rect(self.size, self.position)
        self.surface = pygame.Surface(self.size, pygame.SRCALPHA)
        self.visible = True
    
    def render(self):
        # init the surface once again!
        self.surface = pygame.Surface(self.size, pygame.SRCALPHA)
        self.surface.fill(self.backgroundColor)

        # render the text.
        renderedText = self.font.render(self.string, True, self.foregroundColor)
        self.surface.blit(
            renderedText,
            (
                (self.surface.get_width() // 2 - renderedText.get_width() // 2),
                (self.surface.get_height() // 2 - renderedText.get_height() // 2)
            )
        )

        # load the calculated position & apply to rect.
        self.__calculatedPosition = (
            self.position
            if not self.fixedPosition else 
            getPosition(self.atDisplay.atSurface, self.surface, self.position)
        )

        self.rect = pygame.Rect(self.__calculatedPosition, self.surface.get_size())

    def tick(self, events):
        # need redraw?
        if self.__needRedraw:
            self.render()
            self.__needRedraw=False
        buttonHovered = self.atDisplay.cursor.rect.colliderect(self.rect)
        if buttonHovered:
            print("OH!")

    def draw(self):
        if self.visible:
            if self.surface:
                self.atDisplay.atSurface.blit(self.surface, self.__calculatedPosition)
                pygame.draw.rect(self.atDisplay.atSurface, (0, 0, 0), self.rect)

#
# label: shows text!
#

class label:
    def __init__(self, atDisplay: display, font, string):
        """
        label: holds text.
        """ 
        self.atDisplay  = atDisplay
        self.font       = font
        self.string     = string
        self.position   = [0, 0]
        self.fixedPosition = False
        self.surface    = None
        self.visible    = True
        self.__needRedraw = True
        self.__calculatedPosition = [0, 0]
        self.foreground = [255, 255, 255]
    
    def render(self):
        self.surface = self.font.render(self.string, True, self.foreground)
        self.__calculatedPosition = (
            self.position 
            if not self.fixedPosition else 
            getPosition(self.atDisplay.atSurface, self.surface, self.position)
        )
        self.__needRedraw = False
    
    def setPosition(self, x: int, y: int, useFixed=False):
        self.fixedPosition=useFixed
        self.position = [x, y]
        self.__calculatedPosition = (
            self.position
            if not self.fixedPosition else 
            getPosition(self.atDisplay.atSurface, self.surface, self.position)
        )
    
    def setText(self, string: str):
        self.string = string
        self.__needRedraw = True
    
    def tick(self, events):
        if self.__needRedraw:
            self.render()
    
    def draw(self):
        if self.surface:
            if self.visible:
                self.atDisplay.atSurface.blit(
                    self.surface,
                    self.__calculatedPosition
                )

#
# graph: shows information but in the vertical!
#
class graph:
    def __init__(self, atDisplay: display):
        """
        Graph: this is a very cool graph.
        """
        # setup the display.
        self.atDisplay  = atDisplay

        # sizes and etc.
        self.visible    = True
        self.size       = [100, 50]
        self.position   = [0, 0]
        self.fixedPosition = False

        # result surface!
        self.surface    = pygame.Surface(self.size)

        # setup the background.
        self.__backgroundSurface    = pygame.Surface(self.size,pygame.SRCALPHA)
        self.__barSurfaces          = pygame.Surface(self.size,pygame.SRCALPHA)
        self.__xCount   = 0
        
        # NOTE value can't be 0.
        self.__value = 1
        self.__maxValue = 1

        # custom stuff
        self.foregroundLines = (0xFF, 0x00, 0xFF)
    
    def setValue(self, value):
        """SetValue: set the value here."""
        self.__value = value
    
    def setMaxValue(self, value):
        self.__maxValue = value
    
    def updateGraph(self):
        """UpdateElement: Setup the frame on the surface."""
        graphDivisions = self.size[1] / self.__maxValue
        totalHeight    = math.floor(graphDivisions * self.__value)
        totalHeight    = self.size[1] if totalHeight >= self.size[1] else totalHeight

        # update the position on X.
        if self.__xCount + 1 >= self.size[0]:
            self.__barSurfaces.fill((0, 0, 0, 255))
            self.__xCount = 0
        else:
            self.__xCount += 1
        
        # begin to draw the stuff on the frame.
        pygame.draw.line(
            self.__barSurfaces,                         # -> surface to be drawn
            self.foregroundLines,                       # -> the color of the line
            (self.__xCount, self.size[1]),              # -> where to begin (origin)
            (self.__xCount, self.size[1]-totalHeight)   # -> where to end (dest)
        )
    
    def tick(self, events):
        self.updateGraph()
    
    def draw(self):
        if self.visible:
            self.surface.blit(
                self.__barSurfaces,
                (0, 0)
            )
            self.atDisplay.atSurface.blit(
                self.surface,
                (
                    self.position 
                    if not self.fixedPosition else 
                    getPosition(self.atDisplay.atSurface, self.surface, self.position)
                )
            )

class loadbar:
    def __init__(self, atDisplay: display):

        # define the sizes and the display
        self.atDisplay = atDisplay
        self.surface = None

        # => size & background
        self.size = [10, 10]
        self.backgroundColor = [0, 0, 0]
        self.barColor = [0, 255, 0]

        self.visible = True

        # => position!
        self.position = [0, 0]
        self.fixedPosition = False

        # define the value & it's max value!
        self.value = 0
        self.maxValue = 10
    
    def updateBar(self):
        self.surface = pygame.Surface(self.size, pygame.SRCALPHA)
        self.surface.fill(self.backgroundColor)

        xDivisions    = self.size[0] / self.maxValue
        totalWidth    = math.floor(xDivisions * self.value)
        totalWidth    = self.size[0] if totalWidth >= self.size[0] else totalWidth

        self.surface.fill(
            self.barColor,
            pygame.Rect(
                (0, 0),
                (totalWidth, self.size[1])
            )
        )

    def tick(self, events):
        self.updateBar()

    def draw(self):
        if self.visible:
            self.atDisplay.atSurface.blit(
                self.surface,
                (
                    self.position 
                    if not self.fixedPosition else 
                    getPosition(self.atDisplay.atSurface, self.surface, self.position)
                )
            )