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
from utils import Point3, Point5

if sys.version_info.major < 3:
    print("You need to run this on Python 3")
    sys.exit(-1)


@dataclass
class Camera:
    device_id: int = 0
    device_name: str = ''
    device_type: str = ''
    interfaces: Optional[List[str]] = None
    home_position: Point5 = Point5()
    max_feed_rates: Point5 = Point5()
    device_bounds: Tuple[Point3, Point3] = (Point3(), Point3())
    collision_bounds: Tuple[Point3, Point3] = (Point3(), Point3())


# @dataclass
# class Action:


class COPISCore():
    """COPISCore. Connects and interacts with cameras in system.

    Attributes:
        selected_camera
        points
        cameras
    """

    def __init__(self, *args, **kwargs) -> None:
        """Inits a CopisCore instance.
        """

        path, count = get_helix(glm.vec3(0, -100, 0),
                                glm.vec3(0, 1, 0),
                                185, 50, 4, 36)
        self._points: List[Tuple[int, Point5]] = [
            (0, Point5(
                path[i * 3],
                path[i * 3 + 1],
                path[i * 3 + 2],
                math.atan2(path[i*3+2], path[i*3]) + math.pi,
                math.atan(path[i*3+1]/math.sqrt(path[i*3]**2+path[i*3+2]**2))))
            for i in range(count)
        ]

        self._cameras = [
            Camera(0, 'Camera A', 'Canon EOS 80D DSLR', ['RemoteShutter'], Point5(100, 100, 100)),
            Camera(1, 'Camera B', 'Canon EOS 80D DSLR', ['USBHost-PTP'], Point5(-100, 100, 100)),
            Camera(2, 'Camera C', 'Canon EOS 80D DSLR', ['PC', 'PC-External'], Point5(100, -100, 100)),
            Camera(3, 'Camera D', 'Canon EOS 80D DSLR', ['PC-EDSDK', 'PC-PHP'], Point5(100, 100, -100)),
        ]

        self._selected_camera_id: int = -1

    def connect(self):
        """TODO"""
        pass

    def disconnect(self):
        """TODO"""
        pass

    def add_point(self, device_id: int, pos: Point5) -> None:
        if device_id not in self._cameras:
            return
        self._points.append((device_id, pos))

    def clear_points(self) -> None:
        """Clear points list. (for testing)"""
        self._points = []

    @property
    def selected_camera(self) -> int:
        return self._selected_camera_id

    @selected_camera.setter
    def selected_camera(self, device_id: int) -> None:
        if device_id != -1 and device_id not in (c.device_id for c in self._cameras):
            return
        self._selected_camera_id = device_id

    @property
    def points(self) -> List[Tuple[int, Point5]]:
        return self._points

    @property
    def cameras(self) -> List[Camera]:
        return self._cameras
