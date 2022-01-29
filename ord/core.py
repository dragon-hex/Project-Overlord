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
        self.size       = [800, 600]
    
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
        self.surface    = invokeSafe(pygame.display.set_mode, self.size)
        cliAssertion(self.surface != None, "display failed to init: " + pygame.get_error())
        pygame.display.set_caption(self.title)
        # NOTE: case there is no icon, generate one.
        if not self.icon:
            self.generateIcon()
        self.applyIcon()

    def destroyWindow(self):
        """destroyWindow: close the window."""
        invokeSafe(pygame.display.quit,None)

# content provider
CPR_ELEMENT_INDEX = 0
CPR_ELEMENT_TIMER = 1
CPR_TYPE_IMAGE  = 'image'
CPR_TYPE_FONT = 'font'
CPR_TYPE_SPRITE = 'sprite'

class contentProvider:
    def __init__(self):
        self.baseDir = None
        self.cache = {}
        self.missingTexture = self.__generateMissingTexture()
    
    def __generateMissingTexture(self) -> pygame.Surface:
        """__generateMissingTexture: missing texture is returned by safe functions."""
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
        return _S
    
    def newCache(self, label, element):
        """newCache: creates cache on the list, max time: 2 minutes."""
        maxTime = pygame.time.get_ticks() + (2 * 1000)
        self.cache[label] = [element, maxTime]
    
    def cleanCache(self):
        """cleanCache: this will clean the cache."""
        # HACK: the list when changed, can raise a exception in next iter.
        for key in self.cache.keys():
            if pygame.time.get_ticks() > self.cache[key][1]:
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
        imageReturned = invokeSafe(pygame.image.load, target)
        return imageReturned

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
        try:    fontReturned = pygame.font.Font(target, size)
        except: return None
        return fontReturned
    
    def getFont(self, name: str, size: int) -> None | pygame.font.Font:
        """getFont: return the font object to render."""
        targetKey = "f_" + name + "_" + str(size)
        cacheReturn = self.getCache(targetKey)
        if not cacheReturn:
            fontLoaded = self.__loadFont(name, size)
            if not fontLoaded:
                # NOTE: couldn't load the font.
                return False
            self.newCache(targetKey, fontLoaded)
            return fontLoaded
        else:
            return cacheReturn[CPR_ELEMENT_INDEX]
        
    def getSprites(self, name: str, ordered=False):
        """getSprites: return the sprites!""" 
        # NOTE: case you modifying the path to your resources on the game
        # here is to change the sprites direction! it is set to default to
        # sprites/, but you can change it here.
        SPRITE_DIR = "sprites"
        sourceImage = self.getImage(name,base=SPRITE_DIR)
        sourceMapTarget = self.baseDir + SPRITE_DIR + os.sep + name + ".json"
        sourceMap   = jsonLoad(sourceMapTarget)
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
        if eType == CPR_TYPE_SPRITE:
            return self.getSprites(eName)
        elif eType == CPR_TYPE_IMAGE:
            return self.getImage(eName)
        else:
            # NOTE: wut?
            return None

# core    
class core:
    def __init__(self):
        """core: this is the core of overlord."""
        self.window = window()
        self.storage= contentProvider()
        self.baseDir= None
        self.running= False
        self.modes  = []
        self.onMode = 0
    
    def init(self):
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