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

"""Provide the COPIS Chamber Class."""

from dataclasses import dataclass

from . import BoundingBox


@dataclass
class Chamber:
    """Data structure that implements a chamber for the imaging instrument."""
    chamber_id: int
    name: str
    box: BoundingBox
    port: str


    def as_dict(self):
        """Returns a dictionary representation of a Chamber instance."""
        return {
            f'Chamber {self.name}': {
                'min_x': self.box.lower.x,
                'max_x': self.box.upper.x,
                'min_y': self.box.lower.y,
                'max_y': self.box.upper.y,
                'min_z': self.box.lower.z,
                'max_z': self.box.upper.z,
                'port': self.port
            }
        }
