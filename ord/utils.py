import os
import sys
import random
import json
# class: debugReporter
class debugReporter:
    def __init__(self, enabled):
        self.outputs = [sys.stdout]
        self.enabled = enabled
        self.location = 'unknown'
    
    def write(self, string: str):
        if self.enabled:
            for output in self.outputs:
                try:    output.write(("[%s] debug: " % self.location) + string + "\n")
                except: 
                    # NOTE: this will break the debug.
                    self.outputs.remove(output)
                    return

#
def randomRGBColor() -> tuple:
    """randomColor: return a random color."""
    return (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    )
#
def cliError(error, location='unknown', code=-1):
    """cliError: report the error on the terminal.""" 
    exit(
        print("error: " + error) or code
    )

def cliAssertion(eval, atError, location='??'):
    """cliAssertion: this will use the terminal to display the error."""
    if not eval:
        cliError(atError, location=location)
#
def invokeSafe(function, args, returnException=True):
    """invokeSafe: invoke a function safely."""
    try:
        return function() if args == None else function(args)
    except Exception as E:
        return E if returnException else None
#
def jsonLoad(file):
    """ 
    JSONC: json with comments, since petquest has some demos,
    it need comments to explain some of json code, so, this
    function will remove the comments, line by line and parse
    it using the JSON library on python.
    """
    # NOTE: __strip will remove all the comments from the json line.
    # FIXME: this function may break with MULTILINE comments.
    def __Strip(string):
        char_index, string_length=0,len(string)-1
        inside_comment, acc=False,""
        while char_index <= string_length:
            char        = (string[char_index])
            next_char   = (string[char_index] if char_index + 1 <= string_length else ' ')
            if      char == '/' and next_char == '*':   inside_comment = True        ; char_index += 1
            elif    char == '*' and next_char == '/':   inside_comment = False       ; char_index += 2
            if      char == '/' and next_char == '/':   break
            if      not inside_comment: acc += string[char_index]    ; char_index += 1
            else    : char_index +=1
        return acc
    def __flat(lines):
        """ flat is just a quick function to... flat array into strings. """
        acc = ""
        for line in lines: 
            acc += line
        return acc
    # test if file works.
    if not os.path.isfile(file):
        return None
    file_pointer = open(file,'r')    ; to_decode = file_pointer.readlines()
    file_pointer.close()             ; decoded = [ __Strip(Line) for Line in to_decode ]
    # NOTE: this function can crash at here.
    return json.JSONDecoder().decode(__flat(decoded))