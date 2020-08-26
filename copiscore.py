"""

TODO: add license boilerplate
"""

import math
import os
import platform
import random
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from gl.glutils import get_helix
from typing import Any, Dict, List, Optional, Tuple

import glm

if sys.version_info.major < 3:
    print("You need to run this on Python 3")
    sys.exit(-1)


@dataclass
class Point:
    """"""
    id_: int
    x: float
    y: float
    z: float
    pan: float = 0.0
    tilt: float = 0.0


@dataclass
class Camera:
    """"""
    label: str
    position: Optional[Point]


class COPISCore():
    """COPISCore. Connects and interacts with cameras in system.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Inits a CopisCore instance.
        """

        path, count = get_helix(glm.vec3(0, -100, 0),
                                glm.vec3(0, 1, 0),
                                185, 50, 4, 36)
        # path = [random.randint(-200, 200) for _ in range(300)]
        # count = 100
        self._points = [
            Point(0,
                  path[i * 3],
                  path[i * 3 + 1],
                  path[i * 3 + 2],
                  math.atan2(path[i*3+2], path[i*3]) + math.pi,
                  math.atan(path[i*3+1]/math.sqrt(path[i*3]**2+path[i*3+2]**2)))
            for i in range(count)
        ]

        self._cameras = {
            0: Camera('Camera A', Point(-1, 100, 100, 100)),
            1: Camera('Camera B', None),
            2: Camera('Camera C', None),
            3: Camera('Camera D', None),
        }

        self._selected_camera_id: int = -1

    def connect(self):
        """TODO"""
        pass

    def disconnect(self):
        """TODO"""
        pass

    def add_point(
        self, id_: int, pos: Tuple[float, float, float, float, float]) -> None:
        if id_ not in self._cameras:
            return
        self._points.append(Point(id_, *pos))

    def clear_points(self) -> None:
        """Clear points list. only for testing."""
        self._points = []

    @property
    def selected_camera(self) -> int:
        return self._selected_camera_id

    @selected_camera.setter
    def selected_camera(self, id_: int) -> None:
        if id_ != -1 and id_ not in self._cameras.keys():
            return
        self._selected_camera_id = id_

    @property
    def points(self) -> Optional[List[Point]]:
        return self._points

    @property
    def cameras(self) -> Dict[int, Camera]:
        return self._cameras
