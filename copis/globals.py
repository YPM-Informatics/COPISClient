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
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""Store all enums and global constants."""

from enum import Enum, IntEnum, auto, unique
from typing import NamedTuple

MAX_ID = 16777214


class Point5(NamedTuple):
    """Five axes positional object."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    p: float = 0.0
    t: float = 0.0


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
    CAPSULE = auto()  #2 parrallel lines connected by half circles on each end
    TURNTABLE = auto()
    GRID = auto()


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
    C0 = auto()     # Press shutter.
    C1 = auto()     # Press auto focus.
    C10 = auto()    # Remote shutter focus stack.

    G0 = auto()     # Rapid positioning.
    G1 = auto()     # Linear movement.
    G2 = auto()     # Movement in an arc.
    G3 = auto()
    G4 = auto()     # Pause device.
    G17 = auto()    # XY plane.
    G18 = auto()    # ZX plane.
    G19 = auto()    # YZ plane.
    G28 = auto()    # Homing.
    G90 = auto()    # Absolute distance mode.
    G91 = auto()    # Relative distance mode.
    G92 = auto()    # Set axis position(s).

    M0 = auto()     # Pause processing.
    M17 = auto()    # Enable all motors.
    M18 = auto()    # Disable all motors.
    M24 = auto()    # Resume processing.
    M120 = auto()   # Scan for connected cards - Only applicable on main controller.
    M360 = auto()   # Toggle multi-turn
    M511 = auto()   # Toggle device locked.
    M998 = auto()   # Reboot - V## Parameter is optional. Any value greater than 0 allows
                    # any prior buffered action to finish execution before reboot.

    # TODO: HST_F_STACK should be removed once C10 is fully baked in.
    # HST_PAUSE should also probably be removed is pause implementation goes a different route.
    HST_F_STACK = auto() # Host (serial) - focus stack.
    HST_PAUSE = auto()

    EDS_F_STACK = auto() # EDSDK - focus stack.
    EDS_SNAP = auto() # EDSDK - press shutter.
    EDS_FOCUS = auto() # EDSDK - press auto focus.

    NONE = auto()


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

class SysStatFlags(Enum):
    """bit positions for each status flag"""
    STA_PROC_SERIAL = 0
    STA_PROC_TWI = 1
    STA_CMD_AVAIL = 2
    STA_GC_EXEC = 3
    STA_MOTION_QUEUED = 4
    STA_MOTION_EXEC = 5
    STA_HOMING = 6
    STA_LOCK = 7
