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
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""Provides the COPIS geometries."""

from dataclasses import dataclass

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


@dataclass
class Point5(Point3):
    """Five axes positional object. Inherits from Point3.

        Attributes:
            p: the pan coordinate.
            t: the tilt coordinate.
    """
    p: float = None
    t: float = None


@dataclass
class Size2:
    """2 axes dimensional object.

        Attributes:
            width: the width dimension.
            height: the height dimension.
    """
    width: float = None
    height: float = None


@dataclass
class Size3(Size2):
    """3 axes dimensional object. Inherits from Size2.

        Attributes:
            depth: the depth dimension.
    """
    depth: float = None


@dataclass
class BoundingBox:
    """Axis-aligned bounding box (AABB) object.

        Attributes:
            lower: a Point3 representing the lower corner.
            upper: a Point3 representing the upper corner.
    """
    lower: Point3 = None
    upper: Point3 = None
