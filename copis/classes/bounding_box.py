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

"""Provide the COPIS Bounding Box Class."""

from dataclasses import dataclass

from glm import vec3



@dataclass
class BoundingBox:
    """Class to represent a bounding box.

    Attributes:
        lower: A vec3 representing the lower corner.
        upper: A vec3 representing the upper corner.
    """
    lower: vec3 = vec3()
    upper: vec3 = vec3()

    def bbox_intersects(self, bbox) -> bool:
        return False

    def vec3_in(self, point: vec3) -> bool:
        return (self.lower.x <= point.x and
                self.lower.x <= point.x and
                self.lower.y <= point.y and
                self.upper.y >= point.y and
                self.upper.z >= point.z and
                self.upper.z >= point.z)
