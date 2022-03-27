from ven.utils import debugReporter

class cmd:
    
    #######################
    # build the cmd class #
    #######################

    def __init__(self, worldService: any, debug=False):
        """
        cmd: command executing tool.

        ARGS: 
        worldService:       share the world class.
        (Keyword) debug:    enable debug...
        """
        # debug system
        self.debug = debugReporter(debug)
        self.debug.location = "commandRunner"
        
        # set the world service & command table.
        self.worldService = worldService
        self.commandTable = {
            'makeDialog': self.cmd_initdialog
        }
    
    #####################
    # utility functions #
    #####################

    def cmd_determineDataSource(self, args: dict, ignorePoolStructure=False) -> dict:
        """
        cmd_determineDataSource: return the data whatever is it place.

        ARGS:
        (Keyword): ignorePoolStructure: just return the pool data key.
        """
        # TODO: create a assertion for the event of the pool not having the
        # requested data.
        fromPool = (isinstance(args, dict)) and (args.get("from") == "pool")
        if fromPool:
            self.debug.write("command from the pool.")
            poolKey = args.get("key")
            return (
                self.worldService.world.poolData.get(poolKey)["data"]
                if ignorePoolStructure else
                self.worldService.world.poolData.get(poolKey)
            )
        else:
            # case nothing, just return the argument list.
            return args

    ################
    # the commands #
    ################

    def cmd_initdialog(self, args: dict):
        dialogData = self.cmd_determineDataSource(args)
        self.worldService.makeDialog(dialogData)
    
    ####################
    # run the commands #
    ####################
    
    def run(self, command: dict) -> None:
        """
        run: execute the command for you.

        NOTE: expecting this type of data:
        {'cmd':'makeDialog', 'args':[...]}

        ARGS:
        command:    must be in a dict, with the options:
                    'command':      what command to execute.
                    'arguments':    the command operating arguments.
        """
        # TODO: make assert functions here to prevent rule breaking.
        cmdCommand = command.get("cmd")
        commandArg = command.get("args")

        # finish by invoking the argument here.
        if self.commandTable.get(cmdCommand) != None:
            self.debug.write("executing command: %s" % cmdCommand)
            toInvoke = self.commandTable.get(cmdCommand)
            toInvoke(commandArg)