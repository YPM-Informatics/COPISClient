"""Util functions."""

import math
from collections import OrderedDict
from functools import wraps
from time import time
from typing import Callable, NamedTuple

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
