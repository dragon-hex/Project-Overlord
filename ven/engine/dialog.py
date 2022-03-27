import pygame
from ven.utils import debugReporter
from ven.gui import *

class dialog:
    def __init__(self, engine: any, debug=False):
        self.debug=debugReporter(debug)
        self.debug.location='dialog'
        self.debug.write("hello from the dialog module.")
        self.engine=engine
        # = arrays & indexers =
        self.buffer=[]
        self.bufIndex=0
        self.chrIndex=0
        # = animation =
        self.speed=0.01
        self.timing=0
        # = controls =
        self.inDialog=False
        self.frozen=False
        # init the dialog guis.
        self.initDialogUI()

    def initDialogUI(self):
        # init the dialog frame.
        self.dialogFrame = frame(self.engine.coreDisplay)
        
        # NOTE: dialog size and position is /4 of the screen.
        VW, VH=self.engine.viewport.get_size()
        self.dialogFrame.background = pygame.Surface((VW, VH//3), pygame.SRCALPHA)

        # init the dialog frame.
        self.dialogFrame.background.fill((0, 0, 0))
        self.dialogFrame.backgroundPosition=[0, (VH//3)*2]
        self.dialogFrame.visible=False

        mediumFont  = self.engine.core.storage.getFont("normal", 24)

        self.dialogFromLabel = label(self.engine.coreDisplay, mediumFont, "...")
        self.dialogFromLabel.position[0] = 25
        self.dialogFromLabel.position[1] = 25 + self.dialogFrame.backgroundPosition[1]

        self.dialogFrame.addElement(self.dialogFromLabel)
        self.engine.coreDisplay.addElement(self.dialogFrame)

        # apply the variables.
        self.xPosition = 25
        self.yPosition = self.dialogFromLabel.position[1] + 50
    
    #####################
    # utility functions #
    #####################

    def new(self, buffer: list):
        self.debug.write("new dialog request: %s" % str(buffer))
        self.buffer=buffer
        self.dialogFrame.visible, self.inDialog=True, True
        self.engine.lockPlayer()
    
    def endDialog(self):
        self.debug.write("finished dialog!")
        self.buffer=[]
        self.bufIndex=0
        self.chrIndex=0
        self.inDialog, self.dialogFrame.visible=False, False
        self.frozen=False
        self.engine.unlockPlayer()

    def advanceDrawing(self):
        whatText=self.buffer[self.bufIndex]['msg']
        if self.chrIndex+1>len(whatText):  
            self.frozen=True
        else:
            self.chrIndex+=1
    
    def skip(self):
        if self.bufIndex+1>=len(self.buffer):
            self.endDialog()
        else:
            # advance drawing.
            self.frozen=False
            self.bufIndex+=1
            self.chrIndex=0

    ###############
    # tick system #
    ###############

    def tick(self, events: any):
        if self.inDialog:
            if not self.frozen:
                if pygame.time.get_ticks() > self.timing:
                    self.advanceDrawing()

    ###############
    # draw system #
    ###############

    def draw(self):
        if self.inDialog:
            # extract the current data
            currentTalk = self.buffer[self.bufIndex]

            # from who?
            fromWho = currentTalk.get("from")
            fromWho = (self.engine.world.player.name if not fromWho else fromWho)
            self.dialogFromLabel.setText(fromWho)

            # get the font, case nothing, use the normal one.
            font=currentTalk.get('font') or 'normal'
            fontSize=currentTalk.get('fontSize') or 16
            font=self.engine.core.storage.getFont(font, fontSize)

            # draw the message
            message = currentTalk.get("msg") or '...'

            # index here
            atX, atY = self.xPosition, self.yPosition
            for idx in range(0, self.chrIndex):
                character = message[idx]
                if   character == '*':          font.set_bold(not font.get_bold())
                elif character == '_':          font.set_italic(not font.get_italic())
                elif character == '¬':          font.set_underline(not font.get_underline())
                else:
                    renderedChar=font.render(character, True, (255, 255, 255))
                    self.engine.viewport.blit(renderedChar,(atX, atY))
                    atX = atX + renderedChar.get_width()