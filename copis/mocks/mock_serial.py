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

"""Emulate Serial Port"""

from . import MockCopisController, MockSerialControllerInterface


class MockSerial:
    """A mock serial port to pair with an emulated mock COPIS serial controller."""
    def __init__(self, port=None, baudrate=9600, timeout=None):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._is_open = False

        # Constrain the mock serial device type so that we can expect the proper methods.
        if not issubclass(MockCopisController, MockSerialControllerInterface):
            raise TypeError("Only objects that implement 'MockSerialControllerInterface' " +
                "can serve as a mock serial device.")

        self._device = MockCopisController()

        if self.port:
            self.open()

    def open(self):
        """Emulates serial open method."""
        self._device.start()
        self._is_open = True

    def close(self):
        """Emulates serial close method."""
        self._device.stop()
        self._is_open = False

    def readline(self, size=-1) -> bytes:
        """Emulates serial readline method."""
        return self._device.output_line(size)

    def write(self, data: bytes) -> int:
        """Emulates serial write method."""
        return self._device.execute(data)

    @property
    def is_open(self):
        """Emulates serial is_open property."""
        return self._is_open
