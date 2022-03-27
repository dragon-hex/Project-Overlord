"""
Utils: functions that helps with simple tasks and are used on the entire project.
"""
from .debug import debugReporter
from .general import cliAssertion, cliError, invokeSafe, randomRGBColor, getRandomMessage
from .jsonc import jsonLoad
from .sysinfo import getPythonVersion, getSystem