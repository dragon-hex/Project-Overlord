"""
Debug: this module contains the debug report tool and other debug functions.
"""

import sys

# NOTE: in-case you want to have colorful outputs
# on the debug! this only supports linux :/
SUPPORT_COLOR_TERM = True

# class: debugReporter
class debugReporter:
    def __init__(self, enabled):
        self.outputs    = [sys.stdout]
        self.enabled    = enabled
        self.location   = 'unknown'
        self.counter    = 0
    
    def write(self, string: str, isWarn=False):
        if self.enabled:
            for output in self.outputs:
                try:
                    if SUPPORT_COLOR_TERM:    
                        output.write(
                            ("[\033[1;37m%0.8d\033[0m, \033[1;34m%s\033[0m]: \033[1;%dm%s\033[0m\n") % 
                            (self.counter, self.location, (33 if isWarn else 37), string)
                        )
                    else:
                        output.write("%0.8d [%s] debug: %s\n" % (self.counter, self.location, string))
                except Exception as E: 
                    # NOTE: this will break the debug.
                    self.outputs.remove(output)
                    return
        # set the counter here.
        self.counter += 1