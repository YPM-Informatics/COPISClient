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

"""Util functions."""

import datetime
import re
import threading

from collections import OrderedDict
from functools import wraps
from math import cos, sin, pi
from time import time
from typing import Callable, List
from itertools import zip_longest

import glm
from glm import mat4, vec3, vec4


xyz_steps = [10, 1, 0.1, 0.01]
xyz_units = OrderedDict([('mm', 1.0), ('cm', 10.0), ('in', 25.4)])
pt_steps = [10, 5, 1, 0.1, 0.01]
pt_units = OrderedDict([('dd', 1.0), ('rad', 180.0/pi)])

_NUMBER_PATTERN = re.compile(r'^(-?\d*\.?\d+)$')
_SCIENTIFIC_NOTATION_PATTERN = re.compile(r'[-+]?[\d]+\.?[\d]*[Ee](?:[-+]?[\d]+)?')


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

def fade_color(color: vec4, fade_pct: float, alpha: float=None) -> vec4:
    """Returns color faded by fade percentage (0 to 1).
    An alpha value (0 to 1) can be optionally provided."""
    bind = lambda x: min(max(x, 0), 1)

    if alpha is None:
        alpha = color.w

    alpha = bind(alpha)
    fade_pct = bind(fade_pct)

    return vec4(
        *map(lambda v: 1 * fade_pct + v * (1 - fade_pct), vec3(color)),
        alpha)

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
    """Converts radians to decimal degrees."""
    return value * pt_units['rad']

def dd_to_rad(value: float) -> float:
    """Converts decimal degrees to radians."""
    return value / pt_units['rad']

def is_number(value: str) -> bool:
    """Checks to see if a string is a number (signed int of float).
    Because apparently that's a foreign concept to python -_-"""
    matched = _NUMBER_PATTERN.match(value) is not None
    return len(value) > 0 and matched

def sanitize_number(value: float) -> float:
    """Sanitizes a number approaching zero:
    signed zero and tiny number at 5 or more decimal places."""
    if _SCIENTIFIC_NOTATION_PATTERN.match(str(value)):
        value = float(f'{value:.4f}')

    return value if value != 0.0 else 0.0

def sanitize_point(value: vec3) -> vec3:
    """Sanitizes a vec3 point with coordinates approaching zero."""
    return vec3(list(map(sanitize_number, list(value))))

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
    """Returns a notification message tagged based on the signal."""
    tag = signal.split('_')[1] if signal.startswith('msg_') else signal
    padded_tag = f'{tag}:'
    padded_tag = padded_tag.ljust(6, ' ')

    return f'{padded_tag} {msg}'.strip()

def print_debug_msg(console, msg, is_dev_env) -> None:
    """Prints a debug message to the console, if we are in a dev environment."""
    if is_dev_env:
        dispatch_msg(console, 'msg_debug', msg)

def print_error_msg(console, msg) -> None:
    """Prints an error message to the console."""
    dispatch_msg(console, 'msg_error', msg)

def print_info_msg(console, msg):
    """Prints an info message to the console."""
    dispatch_msg(console, 'msg_info', msg)

def print_raw_msg(console, msg):
    """Echos COPIS controller output to the console."""
    dispatch_msg(console, 'msg_raw', msg.strip('\r\n'))

def print_echo_msg(console, msg):
    """Echos console command to the console."""
    dispatch_msg(console, 'msg_echo', msg)

def dispatch_msg(console, signal, msg):
    """Dispatches a message to the GUI console or standard console if no GUI."""
    ts_msg = get_timestamped(msg)
    if console:
        console.log(signal, ts_msg)
    else:
        print(get_notification_msg(signal, ts_msg))

def locked(func):
    """Provides thread locking mechanism."""
    @wraps(func)
    def inner(*args, **kw):
        with inner.lock:
            return func(*args, **kw)
    inner.lock = threading.Lock()
    return inner

def create_cuboid(size: vec3) -> List[vec3]:
    """Returns a cuboid centered at 0,0,0 given its size"""
    edges = [
        0, 1, 3, 2,     # bottom
        4, 0, 2, 6,      # right
        5, 4, 6, 7,       # top
        1, 5, 7, 3,      # left
        6, 2, 3, 7,       # back
        0, 4, 5, 1     # front
    ]

    corner = size / -2

    vertices = [corner]
    vertices.append(vec3(corner.x, corner.y, corner.z + size.z))
    vertices.append(vec3(corner.x, corner.y + size.y, corner.z))
    vertices.append(vec3(corner.x, corner.y + size.y, corner.z + size.z))
    vertices.append(vec3(corner.x + size.x, corner.y, corner.z))
    vertices.append(vec3(corner.x + size.x, corner.y, corner.z + size.z))
    vertices.append(vec3(corner.x + size.x, corner.y + size.y, corner.z))
    vertices.append(vec3(corner.x + size.x, corner.y + size.y, corner.z + size.z))

    edge_nodes = list(map(lambda e: vertices[e], edges))

    return edge_nodes
