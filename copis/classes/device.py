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

"""Provide the COPIS Device Class."""

from dataclasses import dataclass
from datetime import datetime
from math import inf
from glm import vec3
from pydispatch import dispatcher

from copis.classes.serial_response import SerialResponse
from copis.globals import ComStatus
from copis.models.geometries import Point5
from . import BoundingBox


@dataclass
class Device:
    """Data structure that implements a COPIS instrument imaging device."""
    device_id: int = 0
    serial_no: str = ''
    name: str = ''
    type: str = ''
    description: str = ''
    home_position: Point5 = Point5()
    range_3d: BoundingBox = BoundingBox(vec3(inf), vec3(-inf))
    size: vec3 = vec3()
    port: str = ''
    head_radius: float = 0
    body_dims: vec3 = vec3()
    gantry_dims: vec3 = vec3()
    gantry_orientation: int = 0
    edsdk_save_to_path: str = ''
    _serial_response: SerialResponse = None
    _is_homed: bool = False
    _is_writing_ser: bool = False   # How is this flag used?
    _is_writing_eds: bool = False   # How is this flag used?
    _last_reported_on: datetime = None

    @property
    def position(self):
        """Returns the device's current position base of if it's homed."""
        return self.serial_response.position if self._is_homed else self.home_position

    @property
    def is_writing(self) -> bool:
        """Returns the device's unified IsWriting flag."""
        return self._is_writing_ser or self._is_writing_eds

    @property
    def is_writing_ser(self) -> bool:
        """Returns the device's IsWriting flag for serial com."""
        return self._is_writing_ser

    @property
    def is_writing_eds(self) -> bool:
        """Returns the device's IsWriting flag for EDSDK com."""
        return self._is_writing_eds

    @is_writing_eds.setter
    def is_writing_eds(self, value: bool) -> None:
        old_value = self._is_writing_eds
        self._is_writing_eds = value

        if self._is_writing_eds != old_value:
            dispatcher.send('ntf_device_eds_updated', device=self)

    @property
    def is_homed(self) -> bool:
        """Returns the device's IsHomed flag."""
        return self._is_homed

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
            if self._is_homed:
                return ComStatus.IDLE

            return ComStatus.BUSY if self._is_writing_ser else ComStatus.UNKNOWN

        if self.serial_response.error:
            return ComStatus.ERROR

        if self._is_writing_ser or not self.serial_response.is_idle:
            return ComStatus.BUSY

        if self.serial_response.is_idle:
            return ComStatus.IDLE

        raise ValueError('Unsupported device serial status code path.')

    @property
    def status(self) -> ComStatus:
        """Returns the device's aggregate status."""
        if self._is_writing_eds:
            return ComStatus.BUSY

        return self.serial_status

    def set_is_writing_ser(self) -> None:
        """Sets the device's IsWriting flag."""
        self._is_writing_ser = True

        dispatcher.send('ntf_device_ser_updated', device=self)

    def set_is_homed(self) -> None:
        """Sets the device's IsHomed flag and notifies."""
        self._is_homed = True

        dispatcher.send('ntf_device_homed')

    def set_serial_response(self, response: SerialResponse) -> None:
        """Sets the device's serial response."""
        self._serial_response = response

        if response:
            self._last_reported_on = datetime.now()
        else:
            self._last_reported_on = None

        self._is_writing_ser = False

        dispatcher.send('ntf_device_ser_updated', device=self)
