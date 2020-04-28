from enum import Enum

class Axis(Enum):
    X = "x"
    Y = "y"
    Z = "z"
    B = "b"
    C = "c"
    Plus = "++"
    Minus = "-"

class Tool_Ids(Enum):
    Play = 1
    Pause = 2
    Stop = 3
    Settings = 4