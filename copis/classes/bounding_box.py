# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""Provide the COPIS Bounding Box Class."""

from dataclasses import dataclass
from math import inf

import glm
from glm import vec3

from copis.helpers import round_point


@dataclass
class BoundingBox:
    """Axis-aligned bounding box (AABB).

    Attributes:
        lower: A vec3 representing the lower corner.
        upper: A vec3 representing the upper corner.
    """
    lower: vec3 = vec3(inf)
    upper: vec3 = vec3(-inf)

    @property
    def volume_center(self):
        """Returns the center of the proxy object's bounding box volume."""
        return _get_mid_diagonal(self.lower, self.upper)

    @property
    def ceiling_center(self):
        """Returns the center of the proxy object's bounding box ceiling."""
        ceiling_upper = self.upper
        ceiling_lower = vec3(self.lower.xy, ceiling_upper.z)

        return _get_mid_diagonal(ceiling_lower, ceiling_upper)

    @property
    def floor_center(self):
        """Returns the center of the proxy object's bounding box floor."""
        floor_lower = self.lower
        floor_upper = vec3(self.upper.xy, floor_lower.z)

        return _get_mid_diagonal(floor_lower, floor_upper)

    def bbox_intersect(self, bbox) -> bool:
        """Return whether bbox intersects bbox or not."""
        return False

    def vec3_intersect(self, point: vec3, epsilon: float) -> bool:
        """Return whether point is in bbox or not with a buffer (epsilon)."""
        return (self.lower.x - epsilon <= point.x and
                self.lower.y - epsilon <= point.y and
                self.lower.z - epsilon <= point.z and
                self.upper.x + epsilon >= point.x and
                self.upper.y + epsilon >= point.y and
                self.upper.z + epsilon >= point.z)

    def line_segment_intersect(self, start: vec3, end: vec3) -> bool:
        """Return whether line segment intersects bbox or not.

        Adapted from:
            Andrew Woo, Fast Ray-Box Intersection, Graphics Gems, pp. 395-396
            https://github.com/erich666/GraphicsGems/blob/master/gems/RayBox.c

        Args:
            start: A vec3 representing the start of the line segment.
            end: A vec3 representing the end of the line segment.
        """
        direction: vec3 = end - start
        origin: vec3 = vec3(start)
        coord: vec3 = vec3() # hit point

        LEFT, RIGHT, MIDDLE = 0, 1, 2
        inside = True
        quadrant = [-1 for _ in range(3)]
        which_plane: int
        maxT = [0.0 for _ in range(3)]
        candidate_plane = [0.0 for _ in range(3)]

        # Find candidate planes this loop can be avoided if
        # rays cast all from the eye(assume perspective view)
        for i in range(3):
            if origin[i] < self.lower[i]:
                quadrant[i] = LEFT
                candidate_plane[i] = self.lower[i]
                inside = False
            elif origin[i] > self.upper[i]:
                quadrant[i] = RIGHT
                candidate_plane[i] = self.upper[i]
                inside = False
            else:
                quadrant[i] = MIDDLE

        # Ray origin inside bounding box
        if inside:
            coord = origin
            return True

        # Calculate T distances to candidate planes
        for i in range(3):
            if (quadrant[i] != MIDDLE and direction[i] != 0.0):
                maxT[i] = (candidate_plane[i] - origin[i]) / direction[i]
            else:
                maxT[i] = -1.0

        # Get largest of the maxT's for final choice of intersection
        which_plane = 0
        for i in range(1, 3):
            if maxT[which_plane] < maxT[i]:
                which_plane = i

        # Check final candidate actually inside box
        if maxT[which_plane] < 0.0:
            return False

        for i in range(3):
            if which_plane != i:
                coord[i] = origin[i] + maxT[which_plane] * direction[i]
                if (coord[i] < self.lower[i] or coord[i] > self.upper[i]):
                    return False
            else:
                coord[i] = candidate_plane[i]

        # Ray hits box, check length
        return 0.0001 <= glm.distance(start, coord) <= glm.distance(start, end)

    def vec3_extend(self, point: vec3):
        """Extend bbox by a point."""
        for i in range(3):
            if point[i] < self.lower[i]:
                self.lower[i] = point[i]
            if point[i] > self.upper[i]:
                self.upper[i] = point[i]


def _get_mid_diagonal(lower, upper):
    return round_point((lower + upper) / 2, 3)
