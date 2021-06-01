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

"""Provide the COPIS Maching Class."""

from dataclasses import dataclass
from math import inf

from glm import vec3


@dataclass
class Machine:
    """Data structure that implements the imagining instrument.

    Arguments:
        dimensions: a vec3 representing the build dimensions of the machine.
        origin: a vec 3 representing the machine's axis origin.
    """
    dimensions: vec3 = vec3(inf)
    origin: vec3 = vec3(inf)
    homing_sequence: str = ''

    def as_dict(self):
        """Returns a dictionary representation of a machine instance."""
        return {
            'Machine': {
                'size_x': self.dimensions.x,
                'size_y': self.dimensions.y,
                'size_z': self.dimensions.z,
                'origin_x': self.origin.x,
                'origin_y': self.origin.y,
                'origin_z': self.origin.z,
                'homing_sequence': '\n'.join(self.homing_sequence)
            }
        }
