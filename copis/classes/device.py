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
from glm import vec3
from typing import List, Optional

from . import BoundingBox
from copis.helpers import Point5


@dataclass
class Device:
    """Data structure that implements a COPIS instrument imaging device."""
    device_id: int = 0
    device_name: str = ''
    device_type: str = ''
    chamber_name: str = ''
    interfaces: Optional[List[str]] = None
    position: Point5 = Point5()
    initial_position: Point5 = Point5()
    max_feed_rates: Point5 = Point5()
    device_bounds: BoundingBox = BoundingBox()
    collision_bounds: vec3 = vec3()
    homing_sequence: str = ''
    port: str = ''

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
                'chamber': self.chamber_name,
                'type': self.device_type,
                'interfaces': '\n'.join(self.interfaces),
                'port': self.port
            }
        }

        home = '' if self.homing_sequence is None else self.homing_sequence.strip()
        if len(home) > 0:
            data['home'] = home

        return data
