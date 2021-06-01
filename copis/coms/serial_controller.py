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

"""Manage COPIS Serial Communications."""

import re
import time

from dataclasses import dataclass
from typing import List

import serial

from mprop import mproperty
from serial.serialutil import SerialException
from serial.tools import list_ports

from copis.helpers import Point5
from copis.classes import SerialResponse


@dataclass
class SerialPort():
    """Data structure to hold a COPIS serial port object."""
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
    """Implement Serial Functionalities."""

    _TEST_SERIAL_PORT = 'TEST'
    _READ_TIMEOUT = 1
    _KEY_MAP = {
        'id': 'device_id',
        'ssf': 'system_status_number',
        'pos': 'position',
        'ERR': 'error'
    }
    _OBJECT_PATTERN = re.compile(r'^<(.*)>$')
    _PAIR_PATTERN = re.compile(r'\w+:[-?\d+\.?\d+,]+|\w+:\w+')
    _KEY_VAL_PATTERN = re.compile(r'(\w+):(.*)')

    BAUDS = [9600, 19200, 38400, 57600, 115200]

    def __init__(self):
        self._ports = []
        self._active_port = None
        self._console = None
        self._is_dev_env = False
        self._response = None

    def initialize(self, console = None, is_dev_env: bool = False) -> None:
        """Initialize the serial object."""
        if any(p.is_open for p in self._ports):
            return

        self._console = console
        self._is_dev_env = is_dev_env

        self.update_port_list()

    def select_port(self, name: str) -> SerialPort:
        """Create a serial connection with the given port, without opening it."""
        port = self._get_port(name)
        has_active_port = self._active_port is not None

        if port is None:
            self._print('Invalid attempt to select unknown port.')
            return None

        if has_active_port and port.name == self._active_port.name \
            and self._active_port is not None:
            self._print('Port already selected.')
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
            self._print(f'Error instantiating serial connection: {err.args[0]}')
            return None

    def open_port(self, baud: int = BAUDS[-1]) -> bool:
        """Open the active port."""
        active_port = self._active_port
        has_active_port = active_port is not None

        if not has_active_port:
            self._print('No port selected.')
            return False

        if active_port.connection.is_open:
            self._print('Port connection already open.')
            return True

        try:
            active_port.connection.baudrate = baud
            active_port.connection.timeout = self._READ_TIMEOUT
            active_port.connection.open()
        except SerialException as err:
            self._print(err.args[0])
            return False

        responses = self._read()
        for resp in responses:
            if isinstance(resp, str):
                self._print(f'{resp}')
            elif isinstance(resp, SerialResponse):
                if resp.error is None and resp.is_idle:
                    self._print(f'Serial port to device {0} is open.')


        return True

    def close_port(self) -> None:
        """Close the active port."""
        active_port = self._active_port
        has_active_port = active_port is not None

        if has_active_port and active_port.connection.is_open:
            active_port.connection.close()

    def write(self, data: str) -> List[str]:
        """Writes to the active port"""
        active_port = self._active_port
        response = []

        if active_port is not None and active_port.connection is not None \
                and active_port.connection.is_open:
            data = data.rstrip("\r")
            data = f'{data}\r'.encode()

            active_port.connection.write(data)
            response = self._read()

        return response

    def terminate(self) -> None:
        """Close all ports."""
        for port in self._ports:
            if port is not None and port.connection is not None and port.connection.is_open:
                port.connection.close()

    def update_port_list(self) -> None:
        """Update the serial ports list."""
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

    def _read(self) -> List:
        wait = .2
        active_port = self._active_port
        self._response = []
        time.sleep(wait)

        if active_port is not None and active_port.connection is not None \
                and active_port.connection.is_open:
            while active_port.connection.is_open and active_port.connection.in_waiting:
                p_bytes = active_port.connection.readline().decode()
                self._response.append(p_bytes)
                time.sleep(wait)

        return self._parse_response()

    def _print(self, msg):
        if self._console is None:
            print(msg)
        else:
            self._console.print(msg)

    def _get_port(self, name):
        if len(self._ports) < 1:
            return None

        return next(filter(lambda p, n = name: p.name == n, self._ports), None)

    def _parse_response(self):
        response_stack = []

        for line in self._response:
            line = line.strip('\r\n')
            if self._OBJECT_PATTERN.match(line):
                result = SerialResponse()

                for pair in self._PAIR_PATTERN.findall(line):
                    for key_val in self._KEY_VAL_PATTERN.findall(pair.rstrip(',')):
                        key = self._KEY_MAP[key_val[0]]
                        value = key_val[1]

                        if (key in ['device_id', 'system_status_number']):
                            value = int(value)
                        elif key == 'position':
                            x, y, z, p, t = [float(v) for v in [*key_val[1].split(',')]]
                            value = Point5(x, y, z, p ,t)

                        setattr(result, key, value)
                response_stack.append(result)
            else:
                response_stack.append(line)

        return response_stack

    @property
    def is_port_open(self) -> bool:
        """Return open status of the active port."""
        return self._active_port.connection.is_open \
            if self._active_port is not None and self._active_port.connection is not None else False

    @property
    def port_list(self) -> List[SerialPort]:
        """Return a copy of the serial ports list."""

        return self._ports.copy()


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
    """Return open status of the active port, from the module."""
    return mod._instance.is_port_open

@mproperty
def port_list(mod) -> List[SerialPort]:
    """Return a copy of the serial ports list, from the module."""
    return mod._instance.port_list
