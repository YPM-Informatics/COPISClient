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

"""Util functions."""

import math
import os
from collections import OrderedDict
from functools import wraps
from pathlib import Path
from time import time
from typing import Callable, NamedTuple

import glm

# --------------------------------------------------------------------------
# Path finding global logic
# --------------------------------------------------------------------------
_PROJECT_FOLDER = 'copis'

_current = os.path.dirname(__file__)
_segments = _current.split(os.sep)
_index = _segments.index(_PROJECT_FOLDER)
_root_segments = _segments[1:_index]

_root = '/' + Path(os.path.join(*_root_segments)).as_posix()
# --------------------------------------------------------------------------


xyz_steps = [10, 1, 0.1, 0.01]
xyz_units = OrderedDict([('mm', 1), ('cm', 10), ('in', 25.4)])
pt_steps = [10, 5, 1, 0.1, 0.01]
pt_units = OrderedDict([('dd', math.pi/180), ('rad', 1)])


def timing(f: Callable) -> Callable:
    """Time a function."""
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print(
            f'func:{f.__name__} args:[{args}, {kw}] took: {(te-ts)*1000:.4f}ms')
        return result
    return wrap


def xyzpt_to_mat4(x: float, y: float, z: float, p: float, t: float) -> glm.mat4():
    """Convert x, y, z, pan, tilt into a 4x4 transformation matrix."""
    model = glm.translate(glm.mat4(), glm.vec3(x, y, z)) * \
            glm.mat4(
                math.cos(t) * math.cos(p), -math.sin(t), math.cos(t) * math.sin(p), 0.0,
                math.sin(t) * math.cos(p), math.cos(t), math.sin(t) * math.sin(p), 0.0,
                -math.sin(p), 0.0, math.cos(p), 0.0,
                0.0, 0.0, 0.0, 1.0)
    return model


def point5_to_mat4(point) -> glm.mat4():
    """Convert Point5 into a 4x4 transformation matrix."""
    return xyzpt_to_mat4(point.x, point.y, point.z, point.p, point.t)


def shade_color(color: glm.vec4(), shade_factor: float) -> glm.vec4():
    """Return darker or lighter shade of color by a shade factor."""
    color.x = min(1.0, color.x * (1 - shade_factor))    # red
    color.y = min(1.0, color.y * (1 - shade_factor))    # green
    color.z = min(1.0, color.z * (1 - shade_factor))    # blue
    return color


def find_path(filename: str = '') -> str:
    paths = [p for p in Path(_root).rglob(filename)]
    return str(paths[0]) if len(paths) > 0 else ''


class Point5(NamedTuple):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    p: float = 0.0
    t: float = 0.0


class Point3(NamedTuple):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

'''
def _create_sphere(self, radius, ncircle, pcircle, num_cams) -> None:
        """Populates action list with a spherical path to specification
        """
        jump = 2 * radius / ncircle
        heights = []
        level = -radius
        for i in range(1, ncircle + 1):
            heights.append(level)
            level += jump

        num_bottom = int(num_cams // 2)
        num_top = int(-(num_cams // -2))

        # generate a sphere (for testing)
        # For each of the nine levels
        for i in heights:
            # Compute radius, number of cameras
            r = math.sqrt(radius * radius - i * i)
            # Get path containing x,y,z and count for num of cams
            path, count = get_circle(glm.vec3(0, i, 0), glm.vec3(0, 1, 0), r, pcircle)

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
                # Is it above or below 0?
                if path[j * 3 + 1] > 0:
                    rand_device += num_bottom
                # Where is its x coord?
                for i in range(1, num_top):
                    if (path[j * 3] > (-radius + i*((radius*2)/num_top))):
                        rand_device += 1

                self._actions.append(Action(ActionType.G0, rand_device, 5, point5))
                self._actions.append(Action(ActionType.C0, rand_device))

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