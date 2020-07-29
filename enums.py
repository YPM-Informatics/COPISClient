#!/usr/bin/env python3

from enum import Enum, IntEnum


class ToolIds(Enum):
    PLAY = 1
    PAUSE = 2
    STOP = 3
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


class ViewCubePos(Enum):
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3


class ViewCubeSize(IntEnum):
    SMALLER = 85
    SMALL = 100
    MEDIUM = 115
    LARGE = 140
    LARGER = 170
