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

"""OpenGL viewport util functions."""

from copis.classes.proxyobject import AABBObject3D
import ctypes
import math
from math import cos, tan
from typing import Tuple

import glm
from glm import vec3, vec4, u32vec3, mat3

from copis.classes import CylinderObject3D, AABBObject3D


def get_cylinder_vertices(cylinder: CylinderObject3D, sides: int) -> Tuple[glm.array, glm.array, glm.array]:
    """Get vertices, normals, and indices for a cylinder box.

    Args:
        sides: An int representing the number of sides per circle.
    """
    # faster way to calculate points along a circle
    theta = 2.0 * math.pi / sides
    tan_factor = tan(theta)
    rad_factor = cos(theta)

    x = vec3(cylinder.radius, 0.0, 0.0)

    vertices = []
    for i in range(sides):
        vertices.append(vec3(0.0, 0.0, 0.0) + x)
        vertices.append(vec3(0.0, 0.0, cylinder.height) + x)
        delta = vec3(x[1] * tan_factor, -x[0] * tan_factor, 0.0)
        x = (x + delta) * rad_factor
    vertices.append(vec3(0.0, 0.0, 0.0))
    vertices.append(vec3(0.0, 0.0, cylinder.height))

    normals = []
    for i in range(len(vertices)):
        n = vec3(vertices[i].x, vertices[i].y, 0.0) * mat3(cylinder.trans_matrix)
        normals.append(glm.normalize(n))
        vertices[i] = vec3(vec4(vertices[i], 1.0) * cylinder.trans_matrix)
    normals[-2] = vec3(0.0, 0.0, -1.0) * mat3(cylinder.trans_matrix)
    normals[-1] = vec3(0.0, 0.0, 1.0) * mat3(cylinder.trans_matrix)

    indices = []
    for i in range(0, sides * 2, 2):
        i2 = (i + 2) % (2 * sides)
        i3 = (i + 3) % (2 * sides)
        indices.append(u32vec3(i, i + 1, i2))
        indices.append(u32vec3(i + 1, i3, i2))
        indices.append(u32vec3(2 * sides, i, i2))
        indices.append(u32vec3(2 * sides + 1, i3, i + 1))

    return glm.array(vertices), glm.array(normals), glm.array(indices)


def get_aabb_vertices(aabb: AABBObject3D) -> Tuple[glm.array, glm.array, glm.array]:
    """Get vertices, normals, and indices for an axis-aligned box."""
    vertices = glm.array(
        vec3(aabb.upper.x, aabb.lower.y, aabb.upper.z), # front
        vec3(aabb.lower.x, aabb.lower.y, aabb.upper.z),
        vec3(aabb.lower.x, aabb.lower.y, aabb.lower.z),
        vec3(aabb.upper.x, aabb.lower.y, aabb.lower.z),
        vec3(aabb.upper.x, aabb.upper.y, aabb.upper.z), # top
        vec3(aabb.lower.x, aabb.upper.y, aabb.upper.z),
        vec3(aabb.lower.x, aabb.lower.y, aabb.upper.z),
        vec3(aabb.upper.x, aabb.lower.y, aabb.upper.z),
        vec3(aabb.upper.x, aabb.upper.y, aabb.upper.z), # right
        vec3(aabb.upper.x, aabb.lower.y, aabb.upper.z),
        vec3(aabb.upper.x, aabb.lower.y, aabb.lower.z),
        vec3(aabb.upper.x, aabb.upper.y, aabb.lower.z),
        vec3(aabb.lower.x, aabb.lower.y, aabb.lower.z), # bottom
        vec3(aabb.lower.x, aabb.upper.y, aabb.lower.z),
        vec3(aabb.upper.x, aabb.upper.y, aabb.lower.z),
        vec3(aabb.upper.x, aabb.lower.y, aabb.lower.z),
        vec3(aabb.lower.x, aabb.lower.y, aabb.lower.z), # left
        vec3(aabb.lower.x, aabb.lower.y, aabb.upper.z),
        vec3(aabb.lower.x, aabb.upper.y, aabb.upper.z),
        vec3(aabb.lower.x, aabb.upper.y, aabb.lower.z),
        vec3(aabb.upper.x, aabb.upper.y, aabb.upper.z), # back
        vec3(aabb.upper.x, aabb.upper.y, aabb.lower.z),
        vec3(aabb.lower.x, aabb.upper.y, aabb.lower.z),
        vec3(aabb.lower.x, aabb.upper.y, aabb.upper.z),
    )
    normals = glm.array(
        vec3(0.0, -1.0, 0.0),   # front
        vec3(0.0, -1.0, 0.0),
        vec3(0.0, -1.0, 0.0),
        vec3(0.0, -1.0, 0.0),
        vec3(0.0, 0.0, 1.0),    # top
        vec3(0.0, 0.0, 1.0),
        vec3(0.0, 0.0, 1.0),
        vec3(0.0, 0.0, 1.0),
        vec3(1.0, 0.0, 0.0),    # right
        vec3(1.0, 0.0, 0.0),
        vec3(1.0, 0.0, 0.0),
        vec3(1.0, 0.0, 0.0),
        vec3(0.0, 0.0, -1.0),   # bottom
        vec3(0.0, 0.0, -1.0),
        vec3(0.0, 0.0, -1.0),
        vec3(0.0, 0.0, -1.0),
        vec3(-1.0, 0.0, 0.0),   # left
        vec3(-1.0, 0.0, 0.0),
        vec3(-1.0, 0.0, 0.0),
        vec3(-1.0, 0.0, 0.0),
        vec3(0.0, 1.0, 0.0),    # back
        vec3(0.0, 1.0, 0.0),
        vec3(0.0, 1.0, 0.0),
        vec3(0.0, 1.0, 0.0),
    )
    indices = glm.array(
        u32vec3(0, 1, 2),       # front
        u32vec3(2, 3, 0),
        u32vec3(4, 5, 6),       # top
        u32vec3(6, 7, 4),
        u32vec3(8, 9, 10),      # right
        u32vec3(10, 11, 8),
        u32vec3(12, 13, 14),    # bottom
        u32vec3(14, 15, 12),
        u32vec3(16, 17, 18),    # left
        u32vec3(18, 19, 16),
        u32vec3(20, 21, 22),    # back
        u32vec3(22, 23, 20),
    )

    return vertices, normals, indices
