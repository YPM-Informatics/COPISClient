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
from math import inf

from glm import vec3


@dataclass
class BoundingBox:
    """Axis-aligned bounding box (AABB).

    Attributes:
        lower: A vec3 representing the lower corner.
        upper: A vec3 representing the upper corner.
    """
    lower: vec3 = vec3(inf, inf, inf)
    upper: vec3 = vec3(-inf, -inf, -inf)

    def bbox_intersect(self, bbox) -> bool:
        """Return whether bbox intersects bbox or not."""
        return False

    def vec3_intersect(self, point: vec3) -> bool:
        """Return whether point is in bbox or not."""
        return (self.lower.x <= point.x and
                self.lower.x <= point.x and
                self.lower.y <= point.y and
                self.upper.y >= point.y and
                self.upper.z >= point.z and
                self.upper.z >= point.z)

    def vec3_extend(self, point: vec3):
        """Extend bbox by a point."""
        for i in range(3):
            if point[i] < self.lower[i]:
                self.lower[i] = point[i]
            if point[i] > self.upper[i]:
                self.upper[i] = point[i]
