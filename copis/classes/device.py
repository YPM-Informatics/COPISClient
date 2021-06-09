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

"""Provide the COPIS Device Class."""


from copis.classes.serial_response import SerialResponse
from dataclasses import dataclass
from math import inf
from typing import List, Optional
from glm import vec3

from copis.helpers import Point5
from copis.globals import ComStatus
from . import BoundingBox


@dataclass
class Device:
    """Data structure that implements a COPIS instrument imaging device."""
    device_id: int = 0
    device_name: str = ''
    device_type: str = ''
    interfaces: Optional[List[str]] = None
    position: Point5 = Point5()
    initial_position: Point5 = Point5()
    max_feed_rates: Point5 = Point5()
    device_bounds: BoundingBox = BoundingBox(vec3(inf), vec3(-inf))
    collision_bounds: vec3 = vec3()
    port: str = ''

    edsdk_response = None
    serial_response: SerialResponse = None
    is_homed: bool = False
    is_move_absolute: bool = True
    is_writing: bool = False

    @property
    def edsdk_status(self) -> ComStatus:
        """TODO: Returns the devices EDSDK status based on its last EDSDK response."""
        return ComStatus.UNKNOWN

    @property
    def serial_status(self) -> ComStatus:
        """Returns the devices serial status based on its last serial response."""
        if not self.is_homed:
            return ComStatus.UNKNOWN

        if self.serial_response is None:
            if self.is_homed:
                return ComStatus.IDLE

            return ComStatus.UNKNOWN

        if self.serial_response.error:
            return ComStatus.ERROR

        if self.serial_response.is_idle and not self.is_writing:
            return ComStatus.IDLE

        return ComStatus.BUSY

    def as_dict(self):
        """Return a dictionary representation of a Device instance."""
        data = {
            f'Camera {self.device_name}': {
                'x': self.position.x,
                'y': self.position.y,
                'z': self.position.z,
                'p': self.position.p,
                't': self.position.t,
                'min_x': self.device_bounds.lower.x,
                'max_x': self.device_bounds.upper.x,
                'min_y': self.device_bounds.lower.y,
                'max_y': self.device_bounds.upper.y,
                'min_z': self.device_bounds.lower.z,
                'max_z': self.device_bounds.upper.z,
                'size_x': self.collision_bounds.x,
                'size_y': self.collision_bounds.y,
                'size_z': self.collision_bounds.z,
                'type': self.device_type,
                'interfaces': '\n'.join(self.interfaces),
                'port': self.port
            }
        }

        return data
