"""
general: functions that doesn't fall in any specific caracteristic, that
are just for quick use, example: randomRGBColor()
"""

import random

##################
# some utilities #
##################

def getRandomMessage():
    """
    getRandomMessage: return a random, non-sense message.
    """
    __messages = [
        "I don't know english!",
        "Oh goodbye, the night and day...",
        "I didn't expect this!",
        "Sakura one of the culprits!",
        "I was sleeping when this happened.",
        "Sorry! I didn't mean to!",
        "Pixel, was it your fault?",
        "A bug just sit...",
        "Creepy Creeper?",
        "Thanks for watching!",
        "Underwater",
        "I have nothing to say!",
        "Buso Renkin!",
        "Strange noises came from [...]",
        "Nothing to see here!",
        "A little empty around here.",
        "This message was loaded in the init.",
        "Imagine reading the source code to gather the secret?",
        "Windows96",
        "Linux is cool, IMARITHE?",
        "ごめんバカ",
        "You know this font supports japanese?",
        "Look behind you...",
        "Look front you...",
        "I'm a alien! don't you see?",
        "Strange project.",
        "Project Overlord? more like overload my memory!",
        "Drive Slow",
        "xeS in Borneo"
    ]
    phrase = random.choice(__messages)
    return phrase

def randomRGBColor() -> tuple:
    """randomRGBColor: return a random color."""
    return (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    )

#######################
# assertion functions #
#######################

def cliError(error, location='unknown', code=-1):
    """cliError: report the error on the terminal.""" 
    exit(
        print("error: " + error) or code
    )

def cliAssertion(eval, atError, location='??'):
    """cliAssertion: this will use the terminal to display the error."""
    if not eval:
        cliError(atError, location=location)

def invokeSafe(function, args, returnException=True):
    """invokeSafe: invoke a function safely."""
    try:
        return function() if args == None else function(args)
    except Exception as E:
        return E if returnException else None