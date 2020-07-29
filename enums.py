#!/usr/bin/env python3

from enum import Enum


class ToolIds(Enum):
    PLAY     = 1
    PAUSE    = 2
    STOP     = 3
    SETTINGS = 4


class CamAxis(Enum):
    X = 'x'
    Y = 'y'
    Z = 'z'
    B = 'b'
    C = 'c'
    PLUS = '++'
    MINUS = '-'


class CamMode(Enum):
    NORMAL = 'normal'
    ROTATE = 'rotate'
