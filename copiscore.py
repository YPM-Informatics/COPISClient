"""

TODO: add license boilerplate
"""

import math
import os
import platform
import sys
from dataclasses import dataclass
from gl.glutils import get_helix
from typing import List, Optional, Tuple

from pydispatch import dispatcher

import glm
from utils import Point3, Point5

if sys.version_info.major < 3:
    print("You need to run this on Python 3")
    sys.exit(-1)


class MonitoredList(list):
    def __init__(self, iterable, signal: str) -> None:
        super().__init__(iterable)
        self.signal = signal

    def clear(self) -> None:
        super().clear()
        dispatcher.send(self.signal)

    def append(self, __object) -> None:
        super().append(__object)
        dispatcher.send(self.signal)

    def extend(self, __iterable) -> None:
        super().extend(__iterable)
        dispatcher.send(self.signal)

    def pop(self, __index: int):
        value = super().pop(__index)
        dispatcher.send(self.signal)
        return value

    def insert(self, __index: int, __object) -> None:
        super().insert(__index, __object)
        dispatcher.send(self.signal)

    def remove(self, __value) -> None:
        super().remove(__value)
        dispatcher.send(self.signal)

    def reverse(self) -> None:
        super().reverse()
        dispatcher.send(self.signal)

    def __setitem__(self, key, value) -> None:
        super().__setitem__(key, value)
        dispatcher.send(self.signal)

    def __delitem__(self, key) -> None:
        super().__delitem__(key)
        dispatcher.send(self.signal)


@dataclass
class Device:
    device_id: int = 0
    device_name: str = ''
    device_type: str = ''
    interfaces: Optional[List[str]] = None
    position: Point5 = Point5()
    home_position: Point5 = Point5()
    max_feed_rates: Point5 = Point5()
    device_bounds: Tuple[Point3, Point3] = (Point3(), Point3())
    collision_bounds: Tuple[Point3, Point3] = (Point3(), Point3())


class COPISCore:
    """COPISCore. Connects and interacts with devices in system.

    Attributes:
        points:
        devices:
        selected_device:

    Emits:
        core_point_list_changed:
        core_device_list_changed:
        core_device_selected:
        core_device_deselected:
        core_error:
    """

    def __init__(self, *args, **kwargs) -> None:
        """Inits a CopisCore instance.
        """

        path, count = get_helix(glm.vec3(0, -100, 0),
                                glm.vec3(0, 1, 0),
                                185, 20, 10, 48)
        self._points: List[Tuple[int, Point5]] = MonitoredList([
            (0, Point5(
                path[i * 3],
                path[i * 3 + 1],
                path[i * 3 + 2],
                math.atan2(path[i*3+2], path[i*3]) + math.pi,
                math.atan(path[i*3+1]/math.sqrt(path[i*3]**2+path[i*3+2]**2)))
            )
            for i in range(count)
        ], 'core_point_list_changed')

        self._devices = MonitoredList([
            Device(0, 'Camera A', 'Canon EOS 80D', ['RemoteShutter'], Point5(100, 100, 100)),
            Device(1, 'Camera B', 'Nikon Z50', ['RemoteShutter', 'PC'], Point5(100, 100, 100)),
            Device(2, 'Camera C', 'RED Digital Cinema \n710 DSMC2 DRAGON-X', ['USBHost-PTP'], Point5(-100, 100, 100)),
            Device(3, 'Camera D', 'Phase One XF IQ4', ['PC', 'PC-External'], Point5(100, -100, 100)),
            Device(4, 'Camera E', 'Hasselblad H6D-400c MS', ['PC-EDSDK', 'PC-PHP'], Point5(100, 100, -100)),
        ], 'core_device_list_changed')

        self._selected_device: Optional[Device] = None

    def connect(self):
        """TODO"""
        pass

    def disconnect(self):
        """TODO"""
        pass

    @property
    def points(self) -> List[Tuple[int, Point5]]:
        return self._points

    @property
    def devices(self) -> List[Device]:
        return self._devices

    def check_point(self, point: Tuple[int, Point5]) -> bool:
        if point[0] not in (c.device_id for c in self._devices):
            dispatcher.send('core_error', message=f'invalid point {point}')
            return False
        return True

    @property
    def selected_device(self) -> Optional[Device]:
        return self._selected_device

    @property
    def selected_device_id(self) -> int:
        if self._selected_device is None:
            return -1
        return self._selected_device.device_id

    @selected_device_id.setter
    def selected_device_id(self, device_id: int) -> None:
        device = next((x for x in self._devices if x.device_id == device_id), None)
        if device_id == -1 or device is None:
            dispatcher.send('core_device_deselected', device=self.selected_device)
            self._selected_device = None
            # dispatcher.send('core_error', message=f'invalid device id {device_id}')
            return
        self._selected_device = device
        dispatcher.send('core_device_selected', device=device)
