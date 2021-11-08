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

"""Provide the COPIS Device Class."""


from dataclasses import dataclass
from datetime import datetime
from math import inf
from typing import List, Optional
from glm import vec3

from copis.classes.serial_response import SerialResponse
from copis.globals import ComStatus, Point5
from . import BoundingBox


@dataclass
class Device:
    """Data structure that implements a COPIS instrument imaging device."""
    device_id: int = 0
    device_name: str = ''
    device_type: str = ''
    interfaces: Optional[List[str]] = None
    position: Point5 = Point5()
    initial_position: Point5 = Point5()
    max_feed_rates: Point5 = Point5()
    device_bounds: BoundingBox = BoundingBox(vec3(inf), vec3(-inf))
    collision_bounds: vec3 = vec3()
    port: str = ''

    _serial_response: SerialResponse = None
    is_homed: bool = False
    is_move_absolute: bool = True
    _is_writing: bool = False
    _last_reported_on: datetime = None

    @property
    def is_writing(self) -> bool:
        """Returns the device's IsWriting flag."""
        return self._is_writing

    @property
    def serial_response(self) -> SerialResponse:
        """Returns the device's last serial response."""
        return self._serial_response

    @property
    def last_reported_on(self) -> datetime:
        """Returns the device's last serial response date."""
        return self._last_reported_on

    @property
    def serial_status(self) -> ComStatus:
        """Returns the device's serial status based on its last serial response."""
        if self.serial_response is None:
            if self.is_homed:
                return ComStatus.IDLE

            return ComStatus.BUSY if self._is_writing else ComStatus.UNKNOWN

        if self.serial_response.error:
            return ComStatus.ERROR

        if not self._is_writing and self.serial_response.is_idle:
            return ComStatus.IDLE

        if not self.serial_response.is_idle:
            return ComStatus.BUSY

        return ComStatus.UNKNOWN

    def set_is_writing(self) -> None:
        """Sets the device's IsWriting flag."""
        self._is_writing = True

    def set_serial_response(self, response: SerialResponse) -> None:
        """Sets the device's serial response."""
        self._serial_response = response

        if response:
            self._last_reported_on = datetime.now()
        else:
            self._last_reported_on = None

        self._is_writing = False

    def as_dict(self):
        """Returns a dictionary representation of a Device instance."""
        data = {
            f'Camera {self.device_name}': {
                'x': self.position.x,
                'y': self.position.y,
                'z': self.position.z,
                'p': self.position.p,
                't': self.position.t,
                'min_x': self.device_bounds.lower.x,
                'max_x': self.device_bounds.upper.x,
                'min_y': self.device_bounds.lower.y,
                'max_y': self.device_bounds.upper.y,
                'min_z': self.device_bounds.lower.z,
                'max_z': self.device_bounds.upper.z,
                'size_x': self.collision_bounds.x,
                'size_y': self.collision_bounds.y,
                'size_z': self.collision_bounds.z,
                'type': self.device_type,
                'interfaces': '\n'.join(self.interfaces),
                'port': self.port
            }
        }

        return data
