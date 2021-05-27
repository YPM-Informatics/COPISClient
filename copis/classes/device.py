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
from typing import List, Optional, Tuple

from copis.helpers import Point3, Point5


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
    device_bounds: Tuple[Point3, Point3] = (Point3(), Point3())
    collision_bounds: Tuple[Point3, Point3] = (Point3(), Point3())
    homing_sequence: str = ''

    def as_dict(self):
        """Return a dictionary representation of a Device instance."""
        data = {
            f'Camera {self.device_name}': {
                'x': self.position.x,
                'y': self.position.y,
                'z': self.position.z,
                'p': self.position.p,
                't': self.position.t,
                'chamber': self.chamber_name,
                'type': self.device_type,
                'interfaces': '\n'.join(self.interfaces)
            }
        }

        home = '' if self.homing_sequence is None else self.homing_sequence.strip()
        if len(home) > 0:
            data['home'] = home

        return data
