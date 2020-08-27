"""Util functions."""

from dataclasses import dataclass
from functools import wraps
from time import time
from typing import Callable


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


@dataclass
class Point5:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    p: float = 0.0
    t: float = 0.0


@dataclass
class Point3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
