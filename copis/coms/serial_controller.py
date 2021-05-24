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

from dataclasses import dataclass
from typing import List

import serial

from serial.tools import list_ports
from mprop import mproperty


@dataclass
class SerialPort():
    """Data structure to hold a COPIS serial port object"""
    name: str = ''
    connection: serial.Serial = None
    description: str = ''
    is_active: bool = False

    def __iter__(self):
        return iter((
            self.name,
            self.connection,
            self.description,
            self.is_active
        ))


class SerialController():
    """Implement Serial Functionalities"""

    _TEST_SERIAL_PORT = 'TEST'

    BAUDS = [ 9600, 19200, 38400, 57600, 115200]

    def __init__(self):
        self._ports = []
        self._active_port = None
        self._console = None
        self._is_dev_env = False

    def initialize(self, console, is_dev_env: bool = False) -> None:
        """Initialize the serial object"""
        if any(p.is_open for p in self._ports):
            return

        self._console = console
        self._is_dev_env = is_dev_env

        self.update_port_list()

    def select_port(self, name: str) -> SerialPort:
        """Creates a serial connection with the given port, without opening it"""
        port = self._get_port(name)
        has_active_port = self._active_port is not None

        if port is None:
            self._console.print('Invalid attempt to select unknown port.')
            return None

        if has_active_port and port.name == self._active_port.name \
            and self._active_port is not None:
            self._console.print('Port already selected.')
            return port

        if has_active_port:
            self._active_port.is_active = False

        if port.connection is not None:
            port.is_active = True
            self._active_port = port
            return port

        try:
            connection = None
            if name == SerialController._TEST_SERIAL_PORT:
                connection = serial.serial_for_url('loop://', do_not_open=True)
            else:
                connection = serial.Serial()
                connection.port = name

            port.connection = connection
            port.is_active = True
            self._active_port = port

            return port
        except serial.SerialException as err:
            self._console.print(f'Error instantiating serial connection: {err.args[0]}')
            return None

    def open_port(self, baud: int = BAUDS[-1]) -> bool:
        """Opens the active port"""
        active_port = self._active_port
        has_active_port = active_port is not None

        if not has_active_port:
            self._console.print('No port selected.')
            return False

        if active_port.connection.is_open:
            self._console.print('Port connection already open.')
            return True

        active_port.connection.baudrate = baud
        active_port.connection.open()
        return True

    def close_port(self) -> None:
        """Closes the active port"""
        active_port = self._active_port
        has_active_port = active_port is not None

        if has_active_port and active_port.connection.is_open:
            active_port.connection.close()

    def write(self, data: str) -> None:
        """Writes to the active port"""
        active_port = self._active_port

        if active_port is not None and active_port.connection is not None \
            and active_port.connection.is_open:
            data = data.rstrip("\r")
            data = f'{data}\r'.encode()
            active_port.connection.write(data)

    def terminate(self) -> None:
        """Closes all ports"""
        for port in self._ports:
            if port is not None and port.connection is not None and port.connection.is_open:
                port.connection.close()

    @property
    def is_port_open(self) -> bool:
        """Returns open status of the active port"""
        return self._active_port.connection.is_open \
            if self._active_port is not None and self._active_port.connection is not None else False

    @property
    def port_list(self) -> List[SerialPort]:
        """Returns a copy of the serial ports list"""

        return self._ports.copy()

    def update_port_list(self) -> None:
        """Updates the serial ports list"""
        new_ports = []
        has_active_port = self._active_port is not None

        for (name, desc, _hwid) in sorted(list_ports.comports()):
            port = self._get_port(name)

            is_active = has_active_port and self._active_port.name == name

            if port is None:
                port = SerialPort(name, None, desc, is_active)

            new_ports.append(port)

        # Ensure test port is added if in dev environment
        if self._is_dev_env:
            p_name = SerialController._TEST_SERIAL_PORT
            port = self._get_port(p_name)
            is_active = has_active_port and self._active_port.name == p_name

            if port is None:
                port = SerialPort(p_name, None, 'Loopback port for test', is_active)

            new_ports.append(port)

        self._ports.clear()
        self._ports.extend(new_ports)

        if has_active_port and not \
            any(p.name == self._active_port.name for p in self._ports):
            self._active_port = None

    def _get_port(self, name: str):
        """Finds a serial port by name in the list of ports and returns it, or None"""
        if len(self._ports) < 1:
            return None

        return next(filter(lambda p, n = name: p.name == n, self._ports), None)


_instance = SerialController()

initialize = _instance.initialize
update_port_list = _instance.update_port_list
select_port = _instance.select_port
open_port = _instance.open_port
close_port = _instance.close_port
write = _instance.write
terminate = _instance.terminate
BAUDS = _instance.BAUDS

@mproperty
def is_port_open(mod) -> bool:
    """Returns open status of the active port, from the module"""
    return mod._instance.is_port_open

@mproperty
def port_list(mod) -> List[SerialPort]:
    """Returns a copy of the serial ports list, from the module"""
    return mod._instance.port_list
