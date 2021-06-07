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

"""Store all enums and global constants."""

from enum import Enum, IntEnum, auto, unique

MAX_ID = 16777214


class ToolIds(Enum):
    """Toolbar item IDs."""
    PLAY = 1
    PAUSE = 2
    STOP = 3
    SETTINGS = 4
    EXPORT = 5


class PathIds(Enum):
    """Path type IDs."""
    CYLINDER = auto()
    HELIX = auto()
    SPHERE = auto()
    LINE = auto()
    POINT = auto()


class CamAxis(Enum):
    """Camera axes."""
    X = 'x'
    Y = 'y'
    Z = 'z'
    B = 'b'
    C = 'c'
    PLUS = '++'
    MINUS = '-'


class CamMode(Enum):
    """Camera modes."""
    NORMAL = 'normal'
    ROTATE = 'rotate'


class ViewCubePos(Enum):
    """View cube positions"""
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3


class ViewCubeSize(IntEnum):
    """View cube sizes."""
    SMALLER = 100
    SMALL = 115
    MEDIUM = 130
    LARGE = 150
    LARGER = 170


class ActionType(Enum):
    """Action types."""
    NONE = auto()
    G0 = auto()     # rapid positioning
    G1 = auto()     # linear movement
    G2 = auto()     # movement in an arc
    G3 = auto()
    G4 = auto()     # pause device
    G17 = auto()    # XY plane
    G18 = auto()    # ZX plane
    G19 = auto()    # YZ plane
    G28 = auto()    # homing
    G90 = auto()    # absolute distance mode
    G91 = auto()    # relative distance mode
    G92 = auto()    # set axis position(s)

    C0 = auto()     # press shutter
    C1 = auto()     # press auto focus
    M0 = auto()     # pause processing
    M24 = auto()    # resume processing
    M17 = auto()    # enable all motors
    M18 = auto()    # disable all motors


@unique
class DebugEnv(Enum):
    """Debug environment flags."""
    PROD = 'prod'
    DEV = 'dev'

class ComStatus(Enum):
    """Communication protocol statuses."""
    ERROR = 0
    BUSY = 1
    UNKNOWN = 2
    IDLE = 3
