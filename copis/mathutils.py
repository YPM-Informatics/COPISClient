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

"""Helper math functions: arcball, project_to_sphere, and orthonormal_basis_of.
"""

from math import asin, sqrt, copysign, pi, ceil, floor, fabs
from typing import Tuple

import glm
from glm import vec3, quat


def arcball(
    p1x: float, p1y: float, p2x: float, p2y: float, r: float) -> quat:
    """Return quaternion after arcball rotation.

    See https://www.khronos.org/opengl/wiki/Object_Mouse_Trackball for details.

    Args:
        p1x: Previous screen x-coordinate, normalized.
        p1y: Previous screen y-coordinate, normalized.
        p2x: Current screen x-coordinate, normalized.
        p2y: Current screen y-coordinate, normalized.
        r: Radius of arcball.
    """
    p1 = vec3(p1x, -project_to_sphere(r, p1x, p1y), p1y)
    p2 = vec3(p2x, -project_to_sphere(r, p2x, p2y), p2y)
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

    Combines a sphere and a hyperbolic sheet for smooth transitions.
    See https://www.khronos.org/opengl/wiki/Object_Mouse_Trackball for details.

    Args:
        r: A float for radius.
        x: Screen x-coordinate, normalized.
        y: Screen y-coordinate, normalized.
    """
    xy = x * x + y * y

    r2 = r * r / 2.0
    if xy <= r2:
        return sqrt(r * r - xy)
    return r2 / sqrt(xy)


def orthonormal_basis_of(n: vec3) -> Tuple[vec3, vec3]:
    """Calculate orthonormal basis (branchless).

    From Duff et al., 2017:
        https://graphics.pixar.com/library/OrthonormalB/paper.pdf.

    Args:
        n: A vec3 to rotate to. Does not need to be normalized.

    TODO: Test if orthonormal_basis_of works as intended. If so, we can remove
    rotate_basis_to.
    """
    sign = copysign(1.0, n.z)
    a = -1.0 / (sign + n.z)
    b = n.x * n.y * a
    b1 = vec3(1.0 + sign * n.x * n.x * a, sign * b, -sign * n.x)
    b2 = vec3(b, sign + n.y * n.y * a, -n.y)
    return b1, b2


# def rotate_basis_to(v: vec3) -> Tuple[vec3, vec3, vec3]:
#     """Return normal basis vectors such that R * <0,1,0> = v.

#     Args:
#         v: A vec3 to rotate to. Does not need to be normalized.

#     Raises:
#         ValueError: If vector provided has a magnitude of zero.
#     """
#     if not glm.equal(v, vec3()):
#         raise ValueError('zero magnitude vector')
#     v = v / glm.length(v)
#     x = vec3(1, 0, 0) # x axis normal basis vector
#     z = vec3(0, 0, 1) # z axis normal basis vector

#     # rotate such that that the basis vector for the y axis (up) aligns with v
#     if not glm.equal(v, vec3(0, 1, 0)):
#         phi = acos(v.x)                         # glm.dot(v, vec3(0, 1, 0))
#         axis = vec3(v.z, 0.0, -v.x)             # glm.cross(vec3(0, 1, 0), v)
#         rot = glm.mat3_cast(glm.angleAxis(phi, axis))
#         x = glm.dot(rot, x)
#         z = glm.dot(rot, z)
#     return x, v, z


def optimize_rotation_move_to_angle(start_angle, end_angle, angular_unit='rad'):
    """Takes a starting and an ending angle in radians and determines 
        the corresponding end angle that would result in the shortest rotation between the two angles.
        additional metrics are computed for future usage. replace math.pi with 180 to work in degrees

    Args:
        start_angle: the starting angle from which a rotation is inititated
        end_angle: the angle we are trying to move to from the start angle
    """
    full_circ =  pi*2
    half_circ =  pi
    if angular_unit == 'dd':
        full_circ = 360.0
        half_circ = 180.0
    delta = (end_angle - start_angle)
    dir = 0
    full_rotations = 0
    partial_rotation = 0
    optimized_rotation = 0
    optimized_angle = end_angle
    if delta >= 0:
        dir = 1
        full_rotations = floor(delta/full_circ)
    else:
        dir = -1
        full_rotations = ceil(delta/full_circ)
    partial_rotation = delta % (full_circ*dir)
    optimized_rotation = partial_rotation
    if (fabs(partial_rotation)>(half_circ)):
        optimized_rotation =  partial_rotation -(full_circ*dir)
    optimized_angle = start_angle + optimized_rotation
    return optimized_angle