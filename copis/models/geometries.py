# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""Provides the COPIS geometries."""

import math

from dataclasses import dataclass, asdict
from glm import vec3

def _get_mid_diagonal(lower, upper):
    return round_point((lower + upper) / 2, 3)


def round_point(value: 'Point3', places: int=1) -> 'Point3':
    """Rounds the vertices of a point.

    Args:
        value: the point for which to round the vertices.
        places: the number of decimal places to round to.
    """
    cls = type(value)

    return cls(*list(map(lambda v: round(v, places), list(value))))


@dataclass
class Point3:
    """3 axes positional object.

        Attributes:
            x: the x coordinate.
            y: the y coordinate.
            z: the z coordinate.
    """
    x: float = None
    y: float = None
    z: float = None

    def __iter__(self):
        return iter(self.__dict__.values())

    def __add__(self, other):
        dic = dict(
            (k, (v or 0) + (other.__dict__[k] or 0)) for k, v in self.__dict__.items()
        )

        cls = type(self)

        return cls(**dic)

    def __sub__(self, other):
        dic = dict(
            (k, (v or 0) - (other.__dict__[k] or 0)) for k, v in self.__dict__.items()
        )

        cls = type(self)

        return cls(**dic)

    def __mul__(self, other):
        if isinstance(other, type(self)):
            dic = dict(
                (k, (v or 0) * (other.__dict__[k] or 0)) for k, v in self.__dict__.items()
            )
        elif isinstance(other, (int, float)):
            dic = dict(
                (k, (v or 0) * other) for k, v in self.__dict__.items()
            )
        else:
            raise TypeError(f"unsupported operand type(s) for *: '{type(self)}' and '{type(other)}'.")

        cls = type(self)

        return cls(**dic)

    def __truediv__(self, other):
        if isinstance(other, type(self)):
            dic = dict(
                (k, (v or 0) / (other.__dict__[k] or 0)) for k, v in self.__dict__.items()
            )
        elif isinstance(other, (int, float)):
            dic = dict(
                (k, (v or 0) / other) for k, v in self.__dict__.items()
            )
        else:
            raise TypeError(f"unsupported operand type(s) for /: '{type(self)}' and '{type(other)}'.")

        cls = type(self)

        return cls(**dic)

    def __getitem__(self, idx):
        return list(self.__dict__.values())[idx]

    def __setitem__(self, idx, value):
        prop = list(self.__dict__.keys())[idx]
        setattr(self, prop, value)

    def to_vec3(self) -> vec3:
        """Returns a 3D glm vector from the Point."""
        return vec3(list(asdict(self).values())[:3])

    def to_Size3(self) -> 'Size3':
        """Returns a Size3 object from the Point."""
        return Size3(self.x, self.z, self.y)


@dataclass
class Point5(Point3):
    """Five axes positional object. Inherits from Point3.

        Attributes:
            x: the x coordinate.
            y: the y coordinate.
            z: the z coordinate.
            p: the pan coordinate.
            t: the tilt coordinate.
    """
    p: float = None
    t: float = None

    def to_point3(self) -> Point3:
        """Returns a Point3 equivalent of this instance."""
        return Point3(self.x, self.y, self.z)


@dataclass
class Size2:
    """2 axes dimensional object.

        Attributes:
            width: the width dimension.
            height: the height dimension.
    """
    width: float = None
    height: float = None

    def __iter__(self):
        return iter(self.__dict__.values())

    def __add__(self, other):
        dic = dict(
            (k, (v or 0) + (other.__dict__[k] or 0)) for k, v in self.__dict__.items()
        )

        cls = type(self)

        return cls(**dic)

    def __sub__(self, other):
        dic = dict(
            (k, (v or 0) - (other.__dict__[k] or 0)) for k, v in self.__dict__.items()
        )

        cls = type(self)

        return cls(**dic)

    def __mul__(self, other):
        if isinstance(other, type(self)):
            dic = dict(
                (k, (v or 0) * (other.__dict__[k] or 0)) for k, v in self.__dict__.items()
            )
        elif isinstance(other, (int, float)):
            dic = dict(
                (k, (v or 0) * other) for k, v in self.__dict__.items()
            )
        else:
            raise TypeError(f"unsupported operand type(s) for *: '{type(self)}' and '{type(other)}'.")

        cls = type(self)

        return cls(**dic)

    def __truediv__(self, other):
        if isinstance(other, type(self)):
            dic = dict(
                (k, (v or 0) / (other.__dict__[k] or 0)) for k, v in self.__dict__.items()
            )
        elif isinstance(other, (int, float)):
            dic = dict(
                (k, (v or 0) / other) for k, v in self.__dict__.items()
            )
        else:
            raise TypeError(f"unsupported operand type(s) for /: '{type(self)}' and '{type(other)}'.")

        cls = type(self)

        return cls(**dic)

    def __getitem__(self, idx):
        return list(self.__dict__.values())[idx]

    def __setitem__(self, idx, value):
        prop = list(self.__dict__.keys())[idx]
        setattr(self, prop, value)


@dataclass
class Size3(Size2):
    """3 axes dimensional object. Inherits from Size2.

        Attributes:
            width: the width dimension.
            height: the height dimension.
            depth: the depth dimension.
    """
    depth: float = None

    def to_vec3(self) -> vec3:
        """Returns a 3D glm vector from the Size3."""
        return vec3(list(asdict(self).values()))


@dataclass
class BoundingBox:
    """Axis-aligned bounding box (AABB) object.

        Attributes:
            lower: a Point3 representing the lower corner.
            upper: a Point3 representing the upper corner.
    """
    lower: Point3 = None
    upper: Point3 = None

    @property
    def volume_center(self):
        """Returns the center of the proxy object's bounding box volume."""
        return _get_mid_diagonal(self.lower, self.upper)

    @property
    def ceiling_center(self):
        """Returns the center of the proxy object's bounding box ceiling."""
        ceiling_upper = self.upper
        ceiling_lower = Point3(self.lower.x, self.lower.y, ceiling_upper.z)

        return _get_mid_diagonal(ceiling_lower, ceiling_upper)

    @property
    def floor_center(self):
        """Returns the center of the proxy object's bounding box floor."""
        floor_lower = self.lower
        floor_upper = Point3(self.upper.x, self.upper.y, floor_lower.z)

        return _get_mid_diagonal(floor_lower, floor_upper)

    def does_bbox_intersect(self, bbox) -> bool:
        """Returns whether this bbox intersects the given bbox.

        Args:
            bbox: the bounding box to check intersection against.
        """
        # TODO: implement bbox intersection check.
        return False

    def is_point_inside(self, point: Point3, epsilon: float) -> bool:
        """Returns whether the given point is in this bbox, with a buffer (epsilon).

        Args:
            point: point to check bounding box against.
            epsilon: buffer value.
        """
        return (self.lower.x - epsilon <= point.x and
                self.lower.y - epsilon <= point.y and
                self.lower.z - epsilon <= point.z and
                self.upper.x + epsilon >= point.x and
                self.upper.y + epsilon >= point.y and
                self.upper.z + epsilon >= point.z)

    def does_line_intersect(self, start: Point3, end: Point3) -> bool:
        """Returns whether line segment intersects bbox or not.

        Adapted from:
            Andrew Woo, Fast Ray-Box Intersection, Graphics Gems, pp. 395-396
            https://github.com/erich666/GraphicsGems/blob/master/gems/RayBox.c

        Args:
            start: A vec3 representing the start of the line segment.
            end: A vec3 representing the end of the line segment.
        """
        direction: Point3 = end - start
        origin: Point3 = Point3(*start)
        coord: Point3 = Point3(0, 0, 0) # Hit point.

        left, right, middle = 0, 1, 2
        inside = True
        quadrant = [-1 for _ in range(3)]
        which_plane: int
        max_t = [0.0 for _ in range(3)]
        candidate_plane = [0.0 for _ in range(3)]

        # Find candidate planes this loop can be avoided if
        # rays cast all from the eye(assume perspective view).
        for i in range(3):
            if origin[i] < self.lower[i]:
                quadrant[i] = left
                candidate_plane[i] = self.lower[i]
                inside = False
            elif origin[i] > self.upper[i]:
                quadrant[i] = right
                candidate_plane[i] = self.upper[i]
                inside = False
            else:
                quadrant[i] = middle

        # Ray origin inside bounding box.
        if inside:
            coord = origin
            return True

        # Calculate T distances to candidate planes
        for i in range(3):
            if (quadrant[i] != middle and direction[i] != 0.0):
                max_t[i] = (candidate_plane[i] - origin[i]) / direction[i]
            else:
                max_t[i] = -1.0

        # Get largest of the maxT's for final choice of intersection
        which_plane = 0
        for i in range(1, 3):
            if max_t[which_plane] < max_t[i]:
                which_plane = i

        # Check final candidate actually inside box
        if max_t[which_plane] < 0.0:
            return False

        for i in range(3):
            if which_plane != i:
                coord[i] = origin[i] + max_t[which_plane] * direction[i]
                if (coord[i] < self.lower[i] or coord[i] > self.upper[i]):
                    return False
            else:
                coord[i] = candidate_plane[i]

        # Ray hits box, check length.
        return 0.0001 <= math.dist(start, coord) <= math.dist(start, end)

    def extend_to_point(self, point: Point3):
        """Extend bbox by a point.

        Args:
            point: the point to extend the bounding box to.
        """
        for i in range(3):
            if point[i] < self.lower[i]:
                self.lower[i] = point[i]
            if point[i] > self.upper[i]:
                self.upper[i] = point[i]
