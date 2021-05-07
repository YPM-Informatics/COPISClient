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

from copis.mathutils import rotate_basis_to


def get_circle(p: glm.vec3,
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


def get_helix(p: glm.vec3,
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

'''
    def _create_line(self, startX, startY, startZ, endX, endY, endZ, noPoints, num_cams) -> None:
        xJump = (endX - startX) / (noPoints - 1)
        yJump = (endY - startY) / (noPoints - 1)
        zJump = (endZ - startZ) / (noPoints - 1)
        cam_num = 0
        cam_range = noPoints // num_cams
        for i in range(0, noPoints - 1):
            point5 = [
                startX + i*xJump,
                startY + i*yJump,
                startZ + i*zJump,
                math.atan2(startZ + i*zJump, startX + i*xJump) + math.pi,
                math.atan((startY + i*yJump)/math.sqrt((startX + i*xJump)**2+(startZ + i*zJump)**2))]
            if (i == (cam_range*(cam_num + 1))):
                cam_num += 1
            self._actions.append(Action(ActionType.G0, cam_num, 5, point5))
            self._actions.append(Action(ActionType.C0, cam_num))

    def _create_helix(self, radius, nturn, pturn, num_cams) -> None:
        """Populates action list with a spherical path to specification
        """
        # generate a sphere (for testing)
        # For each of the nine levels
            # Get path containing x,y,z and count for num of cams
        path, count = get_helix(glm.vec3(0, 0, 0), glm.vec3(0, 1, 0), radius, 10, nturn, pturn)

        for j in range(count - 1):
            # Put x,y,z,pan,tilt for camera in point5
            point5 = [
                path[j * 3],
                path[j * 3 + 1],
                path[j * 3 + 2],
                math.atan2(path[j*3+2], path[j*3]) + math.pi,
                math.atan(path[j*3+1]/math.sqrt(path[j*3]**2+path[j*3+2]**2))]

            # temporary hack to divvy ids
            rand_device = 0
            # Where is its x coord?
            for i in range(1, num_cams):
                if (path[j * 3] > (-radius + i*((radius*2)/num_cams))):
                    rand_device += 1

            self._actions.append(Action(ActionType.G0, rand_device, 5, point5))
            self._actions.append(Action(ActionType.C0, rand_device))
'''
