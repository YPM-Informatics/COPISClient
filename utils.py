"""Util functions."""

import math
from collections import OrderedDict
from functools import wraps
from time import time
from typing import Callable, NamedTuple

import glm

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
    """Text"""
    model = glm.translate(glm.mat4(), glm.vec3(point.x, point.y, point.z)) * \
            glm.mat4(math.cos(t) * math.cos(p), -math.sin(t), math.cos(t) * math.sin(p), 0.0,
                    math.sin(t) * math.cos(p), math.cos(t), math.sin(t) * math.sin(p), 0.0,
                    -math.sin(p), 0.0, math.cos(p), 0.0,
                    0.0, 0.0, 0.0, 1.0)
    return model

def point5_to_mat4(point) -> glm.mat4():
    return xyzpt_to_mat4(point.x, point.y, point.z, point.p, point.t)


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
