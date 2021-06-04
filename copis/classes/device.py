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
    edsdk_status: ComStatus = ComStatus.UNKNOWN
    serial_status: ComStatus = ComStatus.UNKNOWN
    is_homed: bool = False
    is_move_absolute: bool = True

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
