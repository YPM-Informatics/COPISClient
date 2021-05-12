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

"""Helper functions for path generation."""

import math
from math import acos, asin, cos, sin, sqrt, tan
from typing import Tuple

import numpy as np
import glm

from .mathutils import rotate_basis_to


def create_circle(p: glm.vec3,
                  n: glm.vec3,
                  r: float,
                  sides: int = 36) -> Tuple[np.ndarray, int]:
    """Create circle vertices given point, normal vector, radius, and # sides.

    Uses an approximation method to compute vertices versus many trig calls.
    """
    a, n, _ = rotate_basis_to(n)
    theta = math.tau / sides
    tangential_factor = tan(theta)
    radial_factor = cos(theta)

    x, y, z = a * r
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


def create_helix(p: glm.vec3,
                 n: glm.vec3,
                 r: float,
                 pitch: int = 1,
                 turns: float = 1.0,
                 sides: int = 36) -> Tuple[np.ndarray, int]:
    """Create helix vertices given point, normal vector, radius, pitch, # turns,
    and # sides.

    Uses an approximation method rather than trig functions.
    """
    a, n, _ = rotate_basis_to(n)
    theta = math.tau / sides
    tangential_factor = tan(theta)
    radial_factor = cos(theta)

    x, y, z = a * r
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


def create_line(start: glm.vec3,
                end: glm.vec3,
                points: int = 2) -> Tuple[np.ndarray, int]:
    """Create line given start position, end position, and # points."""
    if points < 2:
        raise IndexError('number of points in line must be greater than 2')

    vertices = np.empty(points * 3)
    vertices[::3] = np.linspace(start.x, end.x, points)
    vertices[1::3] = np.linspace(start.y, end.y, points)
    vertices[2::3] = np.linspace(start.z, end.z, points)

    return vertices, points


# def get_circle_trig(p, n, r, sides=36):
#     a, n, b = rotate_basis_to(glm.vec3(*n))
#     tau = 6.28318530717958647692

#     count = sides + 1
#     vertices = np.empty(count * 3)
#     for i in range(count):
#         vertices[i*3] = p[0] + r*(a[0]*cos(i*tau/sides) + b[0]*sin(i*tau/sides))
#         vertices[i*3 + 1] = p[1] + r*(a[1]*cos(i*tau/sides) + b[1]*sin(i*tau/sides))
#         vertices[i*3 + 2] = p[2] + r*(a[2]*cos(i*tau/sides) + b[2]*sin(i*tau/sides))
#     return vertices, count


# def get_helix_trig(p, n, r, pitch=1, turns=1.0, sides=36):
#     a, n, b = rotate_basis_to(glm.vec3(*n))
#     tau = 6.28318530717958647692

#     count = int(sides * turns) + 1
#     vertices = np.empty(count * 3)
#     for i in range(count):
#         vertices[i*3] = p[0] + n[0]*(i*pitch/sides) + r*(a[0]*cos(i*tau/sides) + b[0]*sin(i*tau/sides))
#         vertices[i*3 + 1] = p[1] + n[1]*(i*pitch/sides) + r*(a[1]*cos(i*tau/sides) + b[1]*sin(i*tau/sides))
#         vertices[i*3 + 2] = p[2] + n[2]*(i*pitch/sides) + r*(a[2]*cos(i*tau/sides) + b[2]*sin(i*tau/sides))
#     return vertices, count
