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

"""Helper functions for path generation."""

import math

from typing import Tuple

import numpy as np
from glm import vec3

from .mathutils import orthonormal_basis_of


def create_circle(p: vec3,
                  n: vec3,
                  r: float,
                  sides: int = 36) -> Tuple[np.ndarray, int]:
    """Create circle vertices given point, normal vector, radius, and # sides.

    Uses an approximation method to compute vertices versus many trig calls.
    """
    b1, _ = orthonormal_basis_of(n)
    theta = math.tau / sides
    tangential_factor = math.tan(theta)
    radial_factor = math.cos(theta)

    x, y, z = b1 * r
    count = sides + 1
    vertices = np.empty(count * 3)
    for i in range(count):
        vertices[i * 3] = x + p.x
        vertices[i * 3 + 1] = y + p.y
        vertices[i * 3 + 2] = z + p.z
        tx = (y * n.z - z * n.y) * tangential_factor
        ty = (z * n.x - x * n.z) * tangential_factor
        tz = (x * n.y - y * n.x) * tangential_factor
        x = (x + tx) * radial_factor
        y = (y + ty) * radial_factor
        z = (z + tz) * radial_factor

    return vertices, count


def create_helix(p: vec3,
                 n: vec3,
                 r: float,
                 pitch: int = 1,
                 turns: float = 1.0,
                 sides: int = 36) -> Tuple[np.ndarray, int]:
    """Create helix vertices given point, normal vector, radius, pitch, # turns,
    and # sides.

    Uses an approximation method rather than trig functions.
    """
    b2, _ = orthonormal_basis_of(n)
    theta = math.tau / sides
    tangential_factor = math.tan(theta)
    radial_factor = math.cos(theta)

    x, y, z = b2 * r
    d = n * pitch / sides
    count = int(sides * turns) + 1
    vertices = np.empty(count * 3)
    for i in range(count):
        vertices[i * 3] = x + p.x + d.x * i
        vertices[i * 3 + 1] = y + p.y + d.y * i
        vertices[i * 3 + 2] = z + p.z + d.z * i
        tx = (y * n.z - z * n.y) * tangential_factor
        ty = (z * n.x - x * n.z) * tangential_factor
        tz = (x * n.y - y * n.x) * tangential_factor
        x = (x + tx) * radial_factor
        y = (y + ty) * radial_factor
        z = (z + tz) * radial_factor

    return vertices, count


def create_line(start: vec3,
                end: vec3,
                points: int = 2) -> Tuple[np.ndarray, int]:
    """Create line given start position, end position, and # points."""
    if points < 2:
        raise IndexError('number of points in line must be greater than 2')

    vertices = np.empty(points * 3)
    vertices[::3] = np.linspace(start.x, end.x, points)
    vertices[1::3] = np.linspace(start.y, end.y, points)
    vertices[2::3] = np.linspace(start.z, end.z, points)

    return vertices, points