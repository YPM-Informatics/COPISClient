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

"""Helper functions for quaternion math, arcball rotation, and action path
generation.
"""

from math import acos, asin, cos, sin, sqrt, tan
from typing import Tuple

import glm
import numpy as np


def arcball(
    p1x: float, p1y: float, p2x: float, p2y: float, r: float) -> glm.quat:
    """Return updated quaternion after arcball rotation.

    Args:
        p1x: Previous screen x-coordinate, normalized.
        p1y: Previous screen y-coordinate, normalized.
        p2x: Current screen x-coordinate, normalized.
        p2y: Current screen y-coordinate, normalized.
        r: Radius of arcball.
    """
    p1 = glm.vec3(p1x, p1y, project_to_sphere(r, p1x, p1y))
    p2 = glm.vec3(p2x, p2y, project_to_sphere(r, p2x, p2y))
    axis = glm.normalize(glm.cross(p1, p2))

    # calculate angle between p1 and p2
    d = map(lambda x, y: x - y, p1, p2)
    t = sqrt(sum(x * x for x in d)) / (2.0 * r)
    if t > 1.0:
        t = 1.0
    if t < -1.0:
        t = -1.0
    phi = 2.0 * asin(t)

    return glm.angleAxis(phi, axis)


def project_to_sphere(r: float, x: float, y: float) -> float:
    """Return intersection position from screen coords to the arcball.

    See https://www.khronos.org/opengl/wiki/Object_Mouse_Trackball for how
    points outside the arcball are handled.

    Args:
        r: A float for radius.
        x: Screen x-coordinate, normalized.
        y: Screen y-coordinate, normalized.
    """
    d = sqrt(x * x + y * y)

    # combines a sphere and a hyperbolic sheet for smooth transitions
    if d < r * 0.70710678118654752440:
        return sqrt(r * r - d * d)
    t = r / 1.41421356237309504880
    return t * t / d


def rotate_basis_to(v: glm.vec3) -> Tuple[glm.vec3, glm.vec3, glm.vec3]:
    """Return normal basis vectors such that R * <0,1,0> = v.

    Args:
        v: A glm.vec3 to rotate to. Does not need to be normalized.

    Raises:
        ValueError: If vector provided has a magnitude of zero.
    """
    if not glm.equal(v, glm.vec3()):
        raise ValueError('zero magnitude vector')
    v = v / glm.length(v)
    x = glm.vec3(1, 0, 0) # x axis normal basis vector
    z = glm.vec3(0, 0, 1) # z axis normal basis vector

    # rotate such that that the basis vector for the y axis (up) aligns with v
    if not glm.equal(v, glm.vec3(0, 1, 0)):
        phi = acos(v.x)                         # glm.dot(v, glm.vec3(0, 1, 0))
        axis = glm.vec3(v.z, 0.0, -v.x)         # glm.cross(glm.vec3(0, 1, 0), v)
        rot = glm.mat3_cast(glm.angleAxis(phi, axis))
        x = glm.dot(rot, x)
        z = glm.dot(rot, z)
    return x, v, z
