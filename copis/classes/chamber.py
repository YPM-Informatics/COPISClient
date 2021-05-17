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

"""Provides the COPIS Chamber Class"""

from dataclasses import dataclass

from . import Bounds, Dimensions
from copis.helpers import Point3


@dataclass
class Chamber:
    """Data structure that implements a chamber for the imaging instrument"""
    chamber_id: int
    name: str
    bounds: Bounds
    dimensions: Dimensions
    offsets: Point3
    port: str

    def as_dict(self):
        """Returns a dictionary representation of a Chamber instance."""
        return {
            f'Chamber {self.name}': {
                'width': self.dimensions.width,
                'depth': self.dimensions.depth,
                'height': self.dimensions.height,
                'min_x': self.bounds.lower.x,
                'max_x': self.bounds.upper.x,
                'min_y': self.bounds.lower.y,
                'max_y': self.bounds.upper.y,
                'min_z': self.bounds.lower.z,
                'max_z': self.bounds.upper.z,
                'x_offset': self.offsets.x,
                'y_offset': self.offsets.y,
                'z_offset': self.offsets.z,
                'port': self.port
            }
        }
