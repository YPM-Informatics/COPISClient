# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""Store all enums and global constants."""

from enum import Enum, IntEnum, auto, unique
from typing import NamedTuple

MAX_ID = 16777214


class WindowState(NamedTuple):
    """Flat structure representing the state of the application window."""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    is_maximized: bool = False


class Size(NamedTuple):
    """Structure representing size."""
    width: int = 0
    height: int = 0


class ToolIds(Enum):
    """Toolbar item IDs."""
    PLAY_ALL = 1
    PLAY = 2
    PAUSE = 3
    STOP = 4
    SNAP_SHOT = 5
    SNAP_SHOTS = 6
    SETTINGS = 7
    EXPORT = 8


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

class WorkType(Enum):
    """Thread work types."""
    IMAGING = 0
    HOMING = 1
    JOGGING = 2
    SET_READY = 3
    STEPPING = 4
