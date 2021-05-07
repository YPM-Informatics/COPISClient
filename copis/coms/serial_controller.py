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

"""Manages COPIS Serial Communications"""

import serial
from serial.tools import list_ports


class SerialController():
    """Implement Serial Functionalities"""

    def __init__(self):
        self.selected_serial = None
        self.ports = self.get_ports()
        self.bauds = []

    def get_ports(self):
        ports = []

        for n, (portname, desc, hwind) in enumerate(sorted(list_ports.comports())):
            ports.append(portname)
        return ports

    def get_bauds(self):
        if self.selected_serial:
            standard = [9600, 19200, 38400, 57600, 115200]
            return standard #[:standard.index(self.selected_serial.baudrate) + 1]

    def set_current_serial(self, port):
        try:
            self.selected_serial = serial.Serial(port)
            self.selected_serial.close()
            self.bauds = self.get_bauds()
            return True
        except serial.serialutil.SerialException:
            return False
