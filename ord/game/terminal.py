import pygame
import os
import sys

# terminal system for run commands.

class terminal:
    def __init__(self, core):
        # NOTE: terminal system
        self.messages = []
        self.maxMessagesAllowed = 100