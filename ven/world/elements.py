ELEMENT_TEX_IMAGE   = 0
ELEMENT_TEX_SPRITE  = 1

import pygame

class wElement:

    #########################
    # all element variables #
    #########################

    # naming and it generic name.
    name = None
    genericName = None

    # sizes and rects.
    collisionRect = None
    position = None
    drawRect = None
    size = None

    # texture storage & information
    textureData = None
    texture = None
    textureType = None
    textureIndex = 0
    textureTiming = 0
    textureUpdateTime = 0

    # events
    action = None
    actionIndex = 0
    inAction = False

    # misc. properties.
    collide = None

    #############################
    # init the element function #
    #############################

    def loadElementData(self, world: any, worldService: any, elementRecipe: dict):
        """
        loadElementData: load the element information and builds itself.

        ARGS:
        core:           the world reference, this will help to get the texture.
        elementRecipe:  how the element is supposed to be built.
        """
        textureInfo     = elementRecipe.get("texture")
        elementSize     = elementRecipe.get("size")
        elementPos      = elementRecipe.get("position")
        elementActions  = elementRecipe.get("actions")
        tileSize        = world.backgroundData.get("tileSize")

        ## !! BEGIN TO BUILD THE elementRecipe !! ##
        self.name               = elementRecipe.get("name")
        self.genericName        = elementRecipe.get("generic") or self.name

        # load the elementRecipe texture & sizes.
        self.textureType        = ELEMENT_TEX_IMAGE if textureInfo.get("type")=='image' else ELEMENT_TEX_SPRITE
        self.textureUpdateTime  = elementRecipe.get("textureUpdateTime") or 0.5
        self.texture            = worldService.core.storage.getContentByRequest(textureInfo)
        self.position           = elementPos
        self.size               = elementSize

        # load the rectangle for the collisions.
        if not world.cameraRect:
            worldService.debug.write("[element spawning] world camera not loaded yet!")
            xDrawPosition = (tileSize[0] * elementPos[0])
            yDrawPosition = (tileSize[1] * elementPos[1])
        else:
            moveQuantityX = 0 + world.cameraRect.x
            moveQuantityY = 0 + world.cameraRect.y
            xDrawPosition = moveQuantityX + (tileSize[0] * elementPos[0])
            yDrawPosition = moveQuantityY + (tileSize[1] * elementPos[1])
        
        # load the collision stuff.
        collisionData = elementRecipe.get("collision")
        self.collide = collisionData.get("enabled") or False
        if self.collide:
            if collisionData.get("use") == "fill":
                xSize = tileSize[0]
                ySize = tileSize[1]
                xPosition = xDrawPosition
                yPosition = yDrawPosition
            elif collisionData.get("use") == "modified":
                xSize = collisionData.get("xSize")  ;   ySize = collisionData.get("ySize")
                xPos  = collisionData.get("xPos")   ;   yPos  = collisionData.get("yPos")
                xPosition = xDrawPosition + xPos
                yPosition = yDrawPosition + yPos
            else:
                worldService.crash("Invalid collision method in elementRecipe: %s" % elementRecipe.get("name"))
            self.collisionRect = pygame.Rect((xPosition, yPosition), (xSize, ySize))
        self.drawRect = pygame.Rect(( xDrawPosition, yDrawPosition), elementSize)

        # load the elements actions
        if elementActions:
            self.action     = elementActions.get("atAction")
            self.inAction   = False

        self.busy       =False
        self.actionIndex=0

        # !! SAVE elementRecipe !! ##
        worldService.debug.write("new element spawned: " + str(elementRecipe.get("name")))
        

