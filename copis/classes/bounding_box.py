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
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

"""Provide the COPIS Bounding Box Class."""

from dataclasses import dataclass
from math import inf

from glm import vec3
import glm


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
        origin: vec3 = start
        coord: vec3 = vec3() # hit point

        LEFT, RIGHT, MIDDLE = 0, 1, 2
        inside = True
        quadrant = [-1 for _ in range(3)]
        which_plane: int
        maxT = [0.0 for _ in range(3)]
        candidate_plane = [0.0 for _ in range(3)]

        # Find candidate planes this loop can be avoided if
        # rays cast all from the eye(assume perpsective view)
        for i in range(3):
            if(origin[i] < self.lower[i]):
                quadrant[i] = LEFT
                candidate_plane[i] = self.lower[i]
                inside = False
            elif (origin[i] > self.upper[i]):
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
            if (maxT[which_plane] < maxT[i]):
                which_plane = i

        # Check final candidate actually inside box
        if (maxT[which_plane] < 0.0): return False
        for i in range(3):
            if (which_plane != i):
                coord[i] = origin[i] + maxT[which_plane] * direction[i]
                if (coord[i] < self.lower[i] or coord[i] > self.upper[i]):
                    return False
            else:
                coord[i] = candidate_plane[i]

        # Ray hits box, check length
        return (glm.distance(start, coord) <= glm.distance(start, end))

    def vec3_extend(self, point: vec3):
        """Extend bbox by a point."""
        for i in range(3):
            if point[i] < self.lower[i]:
                self.lower[i] = point[i]
            if point[i] > self.upper[i]:
                self.upper[i] = point[i]
