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

"""Provides the COPIS path related data structures."""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

from models.geometries import Point5
from models.actions import Action
from models.machine import Device
from models.g_code import Gcode

class MoveTypes(Enum):
    """Move types."""
    ARC_CW = Gcode.G2.name
    ARC_CCW = Gcode.G3.name
    LINEAR = Gcode.G1.name
    LINEAR_RAPID = Gcode.G0.name


@dataclass
class Pose:
    """Imaging path Pose object.

        Attributes:
            position: the intended destination for the device.
            actions: actions for the device to perform ounce at the destination.
    """
    position: Point5 = None
    actions: Optional[List[Action]] = None


@dataclass
class Move:
    """Imaging path Move object.

        Attributes:
            type: MoveTypes that characterizes the Move.
            start_pose: the move's starting position (a reference to the previous move's end pose or the devices current position).
            end_pose: The move's destination.
            feed_rate: how fast (in millimeters or decimal degrees per minute) to perform a move.
            device: The device to move.
            waypoints: intermediary position between the start and end poses; executed in one continuous motion.
    """
    type: MoveTypes = None
    start_pose: Pose = None
    end_pose: Pose = None
    feed_rate: float = None
    device: Device = None
    waypoints: List[Point5] = None
