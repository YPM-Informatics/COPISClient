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

import datetime
import math
import re
from collections import OrderedDict
from functools import wraps
from math import cos, sin
from time import time
from typing import Callable, List
from itertools import zip_longest

import glm
from glm import mat4, vec3, vec4


xyz_steps = [10, 1, 0.1, 0.01]
xyz_units = OrderedDict([('mm', 1.0), ('cm', 10.0), ('in', 25.4)])
pt_steps = [10, 5, 1, 0.1, 0.01]
pt_units = OrderedDict([('dd', 1.0), ('rad', 180.0/math.pi)])

_NUMBER_PATTERN = re.compile(r'^(-?\d*\.?\d+)$')


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

def xyzpt_to_mat4(x: float, y: float, z: float, p: float, t: float) -> mat4():
    """Convert x, y, z, pan, tilt into a 4x4 transformation matrix."""
    model = glm.translate(mat4(), vec3(x, y, z)) * \
            mat4(
                cos(p), -sin(p), 0.0, 0.0,
                cos(t) * sin(p), cos(t) * cos(p), -sin(t), 0.0,
                sin(t) * sin(p), sin(t) * cos(p), cos(t), 0.0,
                0.0, 0.0, 0.0, 1.0)
    return model

def point5_to_mat4(point) -> mat4:
    """Convert Point5 into a 4x4 transformation matrix."""
    return xyzpt_to_mat4(point.x, point.y, point.z, point.p, point.t)

def shade_color(color: vec4, shade_factor: float) -> vec4:
    """Return darker or lighter shade of color by a shade factor."""
    color.x = min(1.0, color.x * (1 - shade_factor))    # red
    color.y = min(1.0, color.y * (1 - shade_factor))    # green
    color.z = min(1.0, color.z * (1 - shade_factor))    # blue
    return color

def get_action_args_values(args: List[tuple]) -> List[float]:
    """Extracts and returns the values for an action arguments' list of tuples."""
    return [float(a[1]) if isinstance(a, tuple) else a for a in args]

def create_action_args(values: List[float], keys: str = 'XYZPTFSV'):
    """Given a list of values in the same order as the default keys,
    generates a list of tuples suitable for an action's arguments.
    A custom ordered string of keys can be provided.
    Note that zip matches only up to the number of values."""
    return list(zip(keys, [str(c) for c in values]))

def rad_to_dd(value: float) -> float:
    """Convers radians to decimal degrees."""
    return value * pt_units['rad']

def dd_to_rad(value: float) -> float:
    """Convers decimal degrees to radians."""
    return value / pt_units['rad']

def is_number(value: str) -> bool:
    """Checks to see if a string is a number (signed int of float).
    Because apparently that's a foreign concept to python -_-"""
    matched = _NUMBER_PATTERN.match(value) is not None
    return len(value) > 0 and matched

def get_timestamp() -> str:
    """Returns a formatted string representation of the current date and time."""
    now = datetime.datetime.now()
    return now.strftime('%H:%M:%S.%f')[:-3]

def get_timestamped(msg) -> str:
    """Returns given messages with a timestamp."""
    return f'({get_timestamp()}) {msg}'

def interleave_lists(*args):
    """Interleaves items from provided lists into one list."""
    return [val for tup in zip_longest(*args) for val in tup if val is not None]

def get_notification_msg(signal, msg) -> str:
    """Return a notification message tagged based on the signal."""
    tag = signal.split('_')[1] if signal.count('_') == 1 else signal
    padded_tag = f'{tag}:'
    padded_tag = padded_tag.ljust(6, ' ')
    return f'{padded_tag} {msg}'.strip()
