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

"""Provides the COPIS Actions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

from copis.models.g_code import Gcode

class ActionTypes(Enum):
    """Action types."""
    FOCUS = Gcode.C1.name
    FOCUS_STACK = Gcode.C10.name
    NO_OP = auto()          # Do nothing.
    PAUSE = auto()          # Pause.
    SHUTTER_RELEASE = Gcode.C0.name


class Action(ABC):
    """An abstract base class for Actions.

        Attributes:
            type: a required ActionTypes property that categorizes the child class.
    """
    @property
    @abstractmethod
    def type(self) -> ActionTypes:
        """All Action-derived classes must implement this property."""
        raise NotImplementedError(f'You must implement action type in {self.__class__}.')


@dataclass
class FocusAction(Action):
    """An autofocus press Action.

        Attributes:
            shutter_hold_time_ms: how long (in milliseconds) to hold the shutter for.
    """
    shutter_hold_time_ms: float = None      # P

    @property
    def type(self) -> ActionTypes:
        """Returns the action type."""
        return ActionTypes.FOCUS

    def to_gcode(self):
        """Returns a G-code string parsed from the action's type and parameters."""
        gcode = f'{self.type.value}'

        if self.shutter_hold_time_ms:
            gcode += f'P{self.shutter_hold_time_ms}'


@dataclass
class FocusStackAction(Action):
    """A focus stack action.

        Attributes:
            feed_rate: how fast (in millimeters or decimal degrees per minute) to perform a move.
            post_shutter_delay_ms: how long (in milliseconds) to pause after the shutter release.
            pre_shutter_delay_ms: how long (in milliseconds) to pause before the shutter release.
            return_to_start: a flag indicating whether to return to the start position when finished.
            shutter_hold_time_ms: how long (in milliseconds) to hold the shutter for.
            step_count: how many images in the stack.
            step_size_mm: how far to travel (in millimeters) between images.
    """
    feed_rate: float = 2500.0                 # F
    post_shutter_delay_ms: float = None     # Y
    pre_shutter_delay_ms: float = None      # X
    return_to_start: bool = False           # T
    shutter_hold_time_ms: float = None      # P
    step_count: int = None                  # V
    step_size_mm: float = None              # Z

    @property
    def type(self) -> ActionTypes:
        """Returns the action type."""
        return ActionTypes.FOCUS_STACK

    def to_gcode(self):
        """Returns a G-code string parsed from the action's type and parameters."""
        gcode = f'{self.type.value}'

        if self.shutter_hold_time_ms:
            gcode += f'P{self.shutter_hold_time_ms}'

        if self.pre_shutter_delay_ms:
            gcode += f'X{self.pre_shutter_delay_ms}'

        if self.post_shutter_delay_ms:
            gcode += f'Y{self.post_shutter_delay_ms}'

        if self.step_count:
            gcode += f'V{self.step_count}'

        if self.step_size_mm:
            gcode += f'Z{self.step_size_mm}'

        if self.return_to_start:
            gcode += 'T'

        if self.feed_rate:
            gcode += f'F{self.feed_rate}'


@dataclass
class NoAction(Action):
    """A noop (do nothing) Action.

        Attributes:
            duration_ms: how long (in milliseconds) to remain idle for.
    """
    duration_ms: float = None              # P

    @property
    def type(self) -> ActionTypes:
        """Returns the action type."""
        return ActionTypes.NO_OP


@dataclass
class PauseAction(Action):
    """A pause Action.

        Attributes:
            post_shutter_delay_ms: how long (in milliseconds) to pause after the shutter release.
            pre_shutter_delay_ms: how long (in milliseconds) to pause before the shutter release.

    """
    post_shutter_delay_ms: float = None    # Y
    pre_shutter_delay_ms: float = None     # X

    @property
    def type(self) -> ActionTypes:
        """Returns the action type."""
        return ActionTypes.PAUSE


@dataclass
class ShutterReleaseAction(Action):
    """A shutter release (snap image) Action.

        Attributes:
            shutter_hold_time_ms: how long (in milliseconds) to hold the shutter for.
    """
    shutter_hold_time_ms: float = None     # P

    @property
    def type(self) -> ActionTypes:
        """Returns the action type."""
        return ActionTypes.SHUTTER_RELEASE

    def to_gcode(self):
        """Returns a G-code string parsed from the action's type and parameters."""
        gcode = f'{self.type.value}'

        if self.shutter_hold_time_ms:
            gcode += f'P{self.shutter_hold_time_ms}'
