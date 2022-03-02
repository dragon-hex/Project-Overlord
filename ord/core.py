from .utils import *
import pygame
import math

# window
class window:
    def __init__(self):
        # TODO: for now, the game doesn't support resizing!
        self.surface    = None
        self.title      = 'Overlord Project'
        self.icon       = None
        self.size       = [900, 650]
    
    def generateIcon(self):
        """generateWindow: generate the window icon."""
        _W = 64 ; _H = 64
        coloredBlock = pygame.Surface((_W, _H))
        coloredBlock.fill(randomRGBColor())
        self.icon = coloredBlock
    
    def applyIcon(self):
        """applyIcon: set the window icon."""
        if self.icon:
            pygame.display.set_icon(self.icon)

    def initWindow(self) -> bool:
        """initWindow: initializes the window with all the loaded settings."""
        self.surface    = pygame.display.set_mode(self.size, pygame.RESIZABLE)
        cliAssertion(self.surface != None, "display failed to init: " + pygame.get_error())
        pygame.display.set_caption(self.title)
        # NOTE: case there is no icon, generate one.
        if not self.icon:
            self.generateIcon()
        self.applyIcon()
    
    def setMode(self, width: int, height: int) -> None:
        """setMode: change the window mode."""
        # BUG: the display doesn't change the size even after function called.
        # So, this is a UGLY way to assert the mode was set up!
        self.surface = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        while (width != self.surface.get_width()) or (height != self.surface.get_height()):
            self.surface = pygame.display.set_mode((width, height), pygame.RESIZABLE)

    def destroyWindow(self):
        """destroyWindow: close the window."""
        invokeSafe(pygame.display.quit,None)

# content provider
CPR_ELEMENT_INDEX   = 0
CPR_ELEMENT_TIMER   = 1
CPR_TYPE_IMAGE      = 'image'
CPR_TYPE_FONT       = 'font'
CPR_TYPE_SPRITE     = 'sprite'

class contentProvider:
    def __init__(self, debug=False):
        # => basic elements.
        self.baseDir = None
        self.cache = {}
        
        # => case you enabled debug?
        self.debug = debugReporter(debug)
        self.debug.location = 'contentProvider'
        self.debug.write("Hello from Content Provider!")

        # => generate the missing texture.
        self.missingTexture = self.__generateMissingTexture()
    
    def __generateMissingTexture(self) -> pygame.Surface:
        """__generateMissingTexture: missing texture is returned by safe functions."""
        _T = pygame.time.get_ticks()

        _W = 1024 ; _H = 1024
        _PW = 12  ; _PH = 12
        _P  = pygame.Surface((_PW, _PH))
        _P.fill(randomRGBColor())
        _S  = pygame.Surface((_W, _H))
        for yIndex in range(0, math.floor(_H/_PH)):
            for xIndex in range(0, math.floor(_W/_PW)):
                _S.blit(
                    _P, (xIndex * _PW, yIndex * _PH)
                )
            
        self.debug.write("finished in " + str(pygame.time.get_ticks() - _T) + "secs.")
        return _S
    
    def newCache(self, label, element):
        """newCache: creates cache on the list, max time: 2 minutes."""
        maxTime = ( pygame.time.get_ticks() + (60 * 1000) ) * 2
        self.cache[label] = [element, maxTime]
        self.debug.write("cache %s created, estimated time to cleanup: " % label + str(maxTime) + ", now: " + str(pygame.time.get_ticks()))
    
    def cleanCache(self):
        """cleanCache: this will clean the cache."""
        # HACK: the list when changed, can raise a exception in next iter.
        for key in self.cache.keys():
            if pygame.time.get_ticks() > self.cache[key][1]:
                self.debug.write("cache reached max time: %s" % key)
                del self.cache[key]
                return
    
    def getCache(self, label):
        """getCache: return the cache."""
        # TODO: update time for more used elements.
        return self.cache.get(label)
    
    def __loadImage(self, label, base='images'):
        """__loadImage: load the surface of the image.""" 
        # TODO: use a generic file extension such as '.image'
        target = self.baseDir + base + os.sep + label + ".png"
        self.debug.write("loading image path: %s" % target)
        imageReturned = invokeSafe(pygame.image.load, target, returnException=False)
        if imageReturned == None:
            # => in this case, image is none.
            return None
        else:
            # => return the image with the alpha layer.
            return imageReturned.convert_alpha()


    def getImage(self, name, base='images'):
        """getImage: get a image."""
        targetKey = "i_" + name + base
        cacheReturn = self.getCache(targetKey)
        if not cacheReturn:
            imageLoaded = self.__loadImage(name, base=base)
            if not imageLoaded:
                # NOTE: couldn't load the image.
                return False
            self.newCache(targetKey,imageLoaded)
            return imageLoaded
        else:
            return cacheReturn[CPR_ELEMENT_INDEX]
        
    def __loadFont(self, name, size):
        target = self.baseDir + "fonts" + os.sep + name + ".dat"
        #self.debug.write("loading font from path: %s" % target)
        try:    fontReturned = pygame.font.Font(target, size)
        except: return None
        return fontReturned
    
    def getFont(self, name: str, size: int) -> None | pygame.font.Font:
        """getFont: return the font object to render."""
        # NOTE: the font can't be shared, unlike a image.
        return self.__loadFont(name, size)
        
    def getSprites(self, name: str, ordered=False):
        """getSprites: return the sprites!""" 
        # NOTE: case you modifying the path to your resources on the game
        # here is to change the sprites direction! it is set to default to
        # sprites/, but you can change it here.
        SPRITE_DIR = "sprites"
        sourceImage = self.getImage(name,base=SPRITE_DIR)

        if not sourceImage:
            return False

        sourceMapTarget = self.baseDir + SPRITE_DIR + os.sep + name + ".json"
        sourceMap   = jsonLoad(sourceMapTarget)

        if not sourceMap:
            return False

        surfaces    = {} if ordered else []
        for spriteKeys in sourceMap.keys():
            size    = sourceMap.get(spriteKeys)['size']
            cutX    = sourceMap.get(spriteKeys)['cutX']
            cutY    = sourceMap.get(spriteKeys)['cutY']
            # TODO: use the UTILS assert function.
            assert  ((cutX != None and isinstance(cutX, int)) and (isinstance(cutY, int) and cutY != None) and 
                    (isinstance(size, list) and size != None)), ("Error while processing sprite %s" % spriteKeys)
            assert  (isinstance(size[0],int) and isinstance(size[1],int)),("Error while processing sprite %s" % spriteKeys)
            # case all the values are well asserted, then keep doing the sprite thing.
            dummySurface = pygame.Surface(size,pygame.SRCALPHA)
            dummySurface.blit(sourceImage,(-cutX, -cutY))
            # create a copy instead of a reference.
            # but NOTE: this will consume a bit of memory, so,
            # don't abuse too much of the sprites.
            if ordered: surfaces[spriteKeys] = dummySurface.copy()
            else: surfaces.append(dummySurface.copy())
        return surfaces
    
    def getContentByRequest(self, data):
        """getContentByRequest: request the content."""
        eName = data.get("name")
        eType = data.get("type")

        self.debug.write("loading element: %s, type: %s" % (eName, eType))

        if eType == CPR_TYPE_SPRITE:
            only = data.get("only")
            if not only:
                return self.getSprites(eName)
            else:
                self.debug.write("loading only sprites: %s" % str(only))
                orderedDict = self.getSprites(eName, ordered=True)
                if not orderedDict:
                    return False
                else:
                    toReturn = []
                    for key in orderedDict.keys():
                        if key in only:
                            toReturn.append(orderedDict.get(key))
                    return toReturn
        elif eType == CPR_TYPE_IMAGE:
            return self.getImage(eName)
        else:
            # NOTE: wut?
            self.debug.write("getContent was unable to load element: %s" % eType)
            return None

# core    
class core:
    def __init__(self, debug=False):
        """core: this is the core of overlord."""
        self.window = window()
        self.storage= contentProvider(debug=debug)
        self.baseDir= None
        self.running= False
        self.modes  = []
        self.onMode = 0
        self.debug = debug

        # => statistics!
        self.timeTakenByScripts = 0
        self.timeTakenByDraw = 0
        self.timeTakenByTick = 0
        self.averageFps = 0
    
    def init(self, debug=False):
        """init: load the pygame and all the window properties."""
        cliAssertion(
            invokeSafe(pygame.init, None) != None,
            "failed to init pygame."
        )
        # TODO: load the window properties on this stage!
        self.window.initWindow()
    
    def quit(self):
        """quit: destroy the window."""
        self.window.destroyWindow()
        try:    pygame.quit()
        except: return

    def setBaseDir(self, path):
        """setBaseDir: set the base directory for file searching."""
        self.baseDir = path
        self.storage.baseDir = path