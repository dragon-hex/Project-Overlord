# import the main module for everything, the scripting module.
from ven.scripting import *
from ven.utils import debugReporter

# import some necessary python modules
import os

class scriptManager:

    ################################
    # scriptManager class builder. #
    ################################

    def __init__(self, worldService: any, debug=False):
        """Script Manager: store scripts."""
        # debugging
        self.debug = debugReporter(debug)
        self.debug.location = 'scriptManager'
        
        # world connection
        self.worldService = worldService

        # script execution
        self.scriptPool = []
        self.executeScripts = True

        # configurations
        self.NUMBER_TICKS_PER_TICK = 10
        self.HOLD_SCRIPT_EXCEPTION = False

    ####################
    # __sysc functions #
    ####################

    def __sysc_show_hello(self, instance: interpreter):
        """
        __sysc_show_hello: simple debug function that shows the message
        "Hello Dude" in the output.
        """
        instance.regs[0] = "Hello Dude!"
    
    def __sysc_get_position(self, instance: interpreter):
        """
        __sysc_get_position: store the player position in the registers.

        REGISTERS USED:
        R0:     store the X position in the world.
        R1:     store the Y position in the world.
        """

        playerX = 0 + self.worldService.world.cameraRect.x
        playerX = abs(playerX - self.worldService.player.rect.x)
        
        playerY = 0 + self.worldService.world.cameraRect.y
        playerY = abs(playerY - self.worldService.player.rect.y)

        # set to r0 the Xpos and r1 the Ypos
        instance.regs[0] = playerX
        instance.regs[1] = playerY
    
    def __sysc_set_health(self, instance: interpreter): 
        """
        __sysc_set_health: set the player health from the register.

        REGISTERS USED:
        R0:     (expected number) set the player health.
        """
        self.worldService.player.health = instance.regs[0]
    
    def __sysc_get_health(self, instance: interpreter):
        """
        __sysc_get_health: get the player health and store in the registers.

        REGISTERS USED: 
        R0:     store the player health in this register.
        """
        instance.regs[0] = self.worldService.player.health

    def __sysc_spawn_element(self, instance: interpreter):
        """
        __sysc_spawn_element: system call that spawns a element on the world, using the
        pool data that is usually loaded with the world.

        REGISTERS USED:
        R0:     (expected to be always a string): element target.
        """
        # TODO: to implement.
        pass

    ##################
    # load functions #
    ##################
        
    def injectCoreFunctions(self, instance: interpreter):
        """
        injectCoreFunctions: inject all the core functions that can be used for
        world manipulation, player modifications, etc.
        """

        self.debug.write("injecting the core functions on thread: %s" % instance.name)

        # set the variables.
        instance.set_var("INSIDE_VULPES",   1)
        instance.set_var("USING_VM",        "1")

        # load the opcode.
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

    
    def loadScript(self, name: str, script: str) -> interpreter:
        """
        loadScript: load the script in a interpreter and with the already
        injected functions & system calls.
        """
        extractTarget = self.worldService.core.baseDir + "map" + os.sep + "scripts/" + script + ".vl"
        self.debug.write("loading script: %s" % extractTarget)

        if os.path.isfile(extractTarget):
            # load the script interpreter
            protoScript = load_file(extractTarget)
            protoScript.output = self.debug
            protoScript.name = name

            # inject the functions (print, say, etc...)
            self.injectCoreFunctions(protoScript)

            # return the new proto-script
            self.debug.write("finished loading script %s!" % name)
            return protoScript
        else:
            self.crash("script '%s' file not found: '%s'" % (name, extractTarget))

    def initWorldScripts(self, world: any):
        """
        initScripts: this function will read the world information
        in order to load the script data.

        NOTE: all the scripts loaded will be on a single pool!
        """
        for script in world.scriptData:
            scriptName = script.get("name")
            scriptTarget = script.get("target")
            script = self.loadScript(scriptName, scriptTarget)
            self.scriptPool.append(script)
    
    ##################
    # tick functions #
    ##################

    def tickScripts(self):
        # step the script execution.
        for instance in self.scriptPool: 
            for count in range(0, self.NUMBER_TICKS_PER_TICK+1):
                result = instance.step()
                if not result: break
                if instance.status == STATUS_SLEEPING: break
        # check for dead scripts.
        for instance in self.scriptPool:
            if not instance.running:
                self.debug.write("script %s has finished." % instance.name)
                self.scriptPool.remove(instance)
        