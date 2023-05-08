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

"""3D trigonometry functions."""

from math import asin, copysign, fabs, pi, sqrt
from typing import Tuple

import glm

from glm import quat, vec3

from copis.models.geometries import Point3


def _project_to_sphere(radius: float, normal_x: float, normal_y: float) -> float:
    """Returns intersection position from screen coords to the arcball.
        Combines a sphere and a hyperbolic sheet for smooth transitions.

        See https://www.khronos.org/opengl/wiki/Object_Mouse_Trackball for details.

        Args:
            radius: A float for radius.
            normal_x: Screen x-coordinate, normalized.
            normal_y: Screen y-coordinate, normalized.
    """
    l2_norm = normal_x * normal_x + normal_y * normal_y
    rad2 = radius * radius / 2.0

    if l2_norm <= rad2:
        return sqrt(radius * radius - l2_norm)

    return rad2 / sqrt(l2_norm)

def arcball_rotate(normal_x1: float, normal_y1: float, normal_x2: float, normal_y2: float, radius: float) -> quat:
    """Returns quaternion (angle and axis) after arcball rotation.

        See https://www.khronos.org/opengl/wiki/Object_Mouse_Trackball for details.

        Args:
            normal_x1: previous screen x-coordinate, normalized.
            normal_y1: previous screen y-coordinate, normalized.
            normal_x2: current screen x-coordinate, normalized.
            normal_y2: current screen y-coordinate, normalized.
            radius: radius of arcball.
    """
    pt1 = vec3(normal_x1, -_project_to_sphere(radius, normal_x1, normal_y1), normal_y1)
    pt2 = vec3(normal_x2, -_project_to_sphere(radius, normal_x2, normal_y2), normal_y2)
    axis = glm.normalize(glm.cross(pt1, pt2))

    # Calculate angle between point 1 and point 2.
    delta = map(lambda x, y: x - y, pt1, pt2)
    theta = sqrt(sum(x * x for x in delta)) / (2.0 * radius)
    theta = max(min(theta, 1.0), -1.0)
    phi = 2.0 * asin(theta)

    return glm.angleAxis(phi, axis)

def get_orthonormal_basis_of(end_pt: Point3) -> Tuple[Point3, Point3]:
    """Calculate orthonormal basis (branchless).

        From Duff et al., 2017: https://graphics.pixar.com/library/OrthonormalB/paper.pdf.

        Args:
            end_pt: A Point3 to rotate to. Does not need to be normalized.
    """
    sign = copysign(1.0, end_pt.z)
    a = -1.0 / (sign + end_pt.z)
    b = end_pt.x * end_pt.y * a
    pt1 = Point3(1.0 + sign * end_pt.x * end_pt.x * a, sign * b, -sign * end_pt.x)
    pt2 = Point3(b, sign + end_pt.y * end_pt.y * a, -end_pt.y)
    return pt1, pt2

def optimize_rotation(start_angle, end_angle, angular_unit='rad'):
    """Takes a starting and an ending angle in radians and determines
        the corresponding end angle that would result in the shortest rotation between the two angles.
        Additional metrics are computed for future usage.

        Notes: replace math.pi with 180 to work in degrees.

        Args:
            start_angle: the starting angle from which a rotation is initiated.
            end_angle: the angle we are trying to move to from the start angle.
    """
    full_circ = pi * 2
    half_circ = pi

    if angular_unit == 'dd':
        full_circ = 360
        half_circ = 180

    delta = end_angle - start_angle
    direction = 0
    # full_rotations = 0
    partial_rotation = 0
    optimized_rotation = 0
    optimized_angle = end_angle

    if delta >= 0:
        direction = 1
        # full_rotations = floor(delta / full_circ)
    else:
        direction = -1
        # full_rotations = ceil(delta / full_circ)
    partial_rotation = delta % (full_circ * direction)
    optimized_rotation = partial_rotation

    if (fabs(partial_rotation) > half_circ):
        optimized_rotation = partial_rotation - (full_circ * direction)

    optimized_angle = start_angle + optimized_rotation

    return optimized_angle
