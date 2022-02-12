import os, sys
import pygame
import ord

# ENUM THE FUNCTIONS
TICK_FUNCTION = 0
DRAW_FUNCTION = 1

class game:
    def __init__(self):
        self.ordCore = None
        self.baseDir = None
        self.enableDebug = False
    
    def __fail(self, string):
        exit(
            (print("error: " + string) or 0)
        )

    def loadArgs(self, args):
        argIndex, argSize = 1, len(args)
        if argSize < 2:
            return
        # keep.
        _DE = ("-d",    "-debug")
        _LE = ("-l",    "-log")
        _PE = ("-p",    "-path")
        _HE = ("-h",    "-help")
        while argIndex < argSize:
            arg = args[argIndex]
            if   arg in _DE:
                self.enableDebug = True
            elif arg in _LE:
                # TODO: implement log.
                pass
            elif arg in _PE:
                if argIndex + 1 >= argSize:
                    self.__fail(arg+": requires <path>")
                aPath = args[argIndex+1]

                if not os.path.exists(aPath):
                    self.__fail(arg+": invalid folder = " + aPath)
                
                path = os.path.abspath(aPath)
                self.baseDir = path + '/'
                argIndex += 1
            else:
                self.__fail("invalid argument: " + arg)
            argIndex += 1
        print(self.baseDir)
    
    def init(self):
        """init: init the engine!"""
        
        self.loadArgs(sys.argv)
        self.ordCore = ord.core(debug=self.enableDebug)

        # NOTE: case the game dir is not initialized, then use default option.
        if not self.baseDir:
            self.baseDir = os.path.abspath("./data")+os.sep

        if not os.path.exists(self.baseDir):
            self.__fail("no directory found.")

        self.ordCore.setBaseDir(self.baseDir)
        
        # finally init the core.
        self.ordCore.init()
        
        # set the core.
        self.ordWorld = ord.world(self.ordCore, debug=self.enableDebug)
        self.ordWorld.init()

        self.ordCore.modes = [
            [self.ordWorld.tick, self.ordWorld.draw, "world"]
        ]

        self.ordCore.running = True
    
    def loop(self):
        """loop: loop the engine!"""
        clock = pygame.time.Clock()

        while self.ordCore.running:
            onMode = self.ordCore.onMode
            events = pygame.event.get()

            self.ordCore.modes[onMode][TICK_FUNCTION](events)
            self.ordCore.modes[onMode][DRAW_FUNCTION]()
            
            clock.tick(60)
    
    def quit(self):
        """quit: quit the game."""
        self.ordCore.quit()

def wrapper():
    gameInstance = game()
    gameInstance.init()
    gameInstance.loop()
    gameInstance.quit()

if __name__ == '__main__':
    wrapper()