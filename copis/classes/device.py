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

"""Provides the COPIS Device Class"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from helpers import Point3, Point5


@dataclass
class Device:
    """Data structure that implements a COPIS instrument imaging device"""
    device_id: int = 0
    device_name: str = ''
    device_type: str = ''
    chamber_name: str = ''
    interfaces: Optional[List[str]] = None
    position: Point5 = Point5()
    home_position: Point5 = Point5()
    max_feed_rates: Point5 = Point5()
    device_bounds: Tuple[Point3, Point3] = (Point3(), Point3())
    collision_bounds: Tuple[Point3, Point3] = (Point3(), Point3())

    def as_dict(self):
        """Returns a dictionary representation of a Device instance."""
        return {
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
