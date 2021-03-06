# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

"""Store all enums."""

from enum import Enum, IntEnum, auto


class ToolIds(Enum):
    PLAY = 1
    PAUSE = 2
    STOP = 3
    SETTINGS = 4
    EXPORT = 5


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
    SMALLER = 90
    SMALL = 105
    MEDIUM = 120
    LARGE = 140
    LARGER = 160


class ActionType(Enum):
    NONE = auto()
    G0 = auto()     # rapid positioning
    G1 = auto()     # linear movement
    G2 = auto()     # movement in an arc
    G3 = auto()
    G4 = auto()     # pause device
    G17 = auto()    # XY plane
    G18 = auto()    # ZX plane
    G19 = auto()    # YZ plane
    G90 = auto()    # absolute distance mode
    G91 = auto()    # relative distance mode
    G92 = auto()    # set axis position(s)

    C0 = auto()     # press shutter
    C1 = auto()     # press auto focus
    M0 = auto()     # pause processing
    M24 = auto()    # resume processing
    M17 = auto()    # enable all motors
    M18 = auto()    # disable all motors
