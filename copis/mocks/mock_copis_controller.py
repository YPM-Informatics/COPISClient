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

"""Emulate COPIS Serial Controller"""

import datetime
import sys
import threading
import time
import random

from typing import Any
from collections import namedtuple

from copis.command_processor import deserialize_command
from copis.helpers import is_number
from copis.globals import Point5
from copis.models.g_code import Gcode


class MockSerialControllerMeta(type):
    """A COPIS mock serial controller metaclass that'll be used for
    mock serial controller class creation."""
    def __instancecheck__(cls, instance: Any) -> bool:
        # pylint: disable=no-value-for-parameter
        return cls.__subclasscheck__(type(instance))

    def __subclasscheck__(cls, subclass: type) -> bool:
        return (hasattr(subclass, 'start') and
            callable(subclass.start) and
            hasattr(subclass, 'stop') and
            callable(subclass.stop) and
            hasattr(subclass, 'execute') and
            callable(subclass.execute) and
            hasattr(subclass, 'output_line') and
            callable(subclass.output_line))


class MockSerialControllerInterface(metaclass=MockSerialControllerMeta):
    """This interface is used for concrete classes to inherit from.
    There is no need to define the MockSerialControllerMeta methods as any class
    as they are implicitly made available via .__subclasscheck__().
    """
    pass


class MockCopisController():
    """Implements a mock COPIS serial controller."""
    _INTERVAL = 2 # Seconds
    _MAX_FEEDRATE = 5000 # mm or dd/min
    _DEFAULT_SHUTTER_PRESS = .01 # 10 milliseconds in seconds
    _DEFAULT_ACTION_TIMESPAN = .1 # 100 millisecond in seconds
    _MINS_TO_SECS_RATIO = 60
    _MSS_TO_SECS_RATIO = 1/1000

    _MOVE_COMMANDS = [Gcode.G0, Gcode.G1]
    _MODE_COMMANDS = [Gcode.G90, Gcode.G91]
    _RESET_COMMANDS = [Gcode.G92]
    _HOME_COMANDS = [Gcode.G28]
    _CAMERA_COMMANDS = [Gcode.C0, Gcode.C1]

    _BOUNDS = {
        'x': (-180, 180),
        'y': (-300, 300),
        'z': (0, 300),
        'p': (-180, 180),
        't': (-180, 180)
    }

    _COPIS_RESPONSE = namedtuple('CopisResponse', 'payload report_on')

    def __init__(self):
        self._is_running = False
        self._is_absolute_move_mode = []
        self._is_locked = []
        self._response_buffer = []
        self._output_buffer = []

        self._last_positions = []

    def start(self):
        """Starts the controller as a result of connecting to it via serial."""
        self._is_running = True
        response_thread = threading.Thread(
            target=self._respond,
            daemon=True,
            name = 'response thread'
        )

        self._is_absolute_move_mode = [True] * 3
        self._is_locked = [True] * 3
        self._last_positions = [Point5()] * 3

        now = datetime.datetime.now()

        startup_start = [
            'settings read from EEPROM',
            '**COPIS**',
            'Version: SZRC_RC6 Tue Jun 08 15:38:58 2021',
            'Device ID: 0',
            '2 connected',
            'id:1;state:255',
            'id:2;state:255'
        ]
        startup_end = [
            '9860 bytes available',
            'COPIS_READY'
        ]

        for line in startup_start:
            resp = self._COPIS_RESPONSE(
                payload=line,
                report_on=now
            )
            self._response_buffer.append(resp)

        for i in range(len(self._last_positions)):
            resp = self._COPIS_RESPONSE(
                payload=self._get_formatted_response(i),
                report_on=now
            )
            self._response_buffer.append(resp)

        for line in startup_end:
            resp = self._COPIS_RESPONSE(
                payload=line,
                report_on=now
            )
            self._response_buffer.append(resp)

        response_thread.start()

    def stop(self):
        """Stops the controller as a result of disconnecting from it via serial."""
        self._is_running = False

        self._last_positions = []

    def execute(self, cmd: bytes) -> int:
        """Executs a command written to the controller from serial."""
        def to_dict(args):
            obj = {
                'x': None,
                'y': None,
                'z': None,
                'p': None,
                't': None,
                'f': None,
                's': None,
                'v': None
            }

            for arg in args:
                key = arg[0].lower()
                val = arg[1]
                val = 0.0 if not is_number(val) else float(val)
                obj[key] = val

            return obj

        if cmd and len(cmd) > 0:
            cmds = cmd.decode().strip('\r ').split('\r')
            actions = [deserialize_command(c) for c in cmds]
            pos = 'xyzpt'

            for action in actions:
                x, y, z, p, t = self._last_positions[action.device]
                prev_position = {
                    'x': x,
                    'y': y,
                    'z': z,
                    'p': p,
                    't': t
                }
                position = prev_position.copy()

                feedrate = None
                action_timespan = self._DEFAULT_ACTION_TIMESPAN
                data = None if action.argc == 0 else to_dict(action.args)

                if self._is_locked[action.device] and action.atype != Gcode.M511:
                    pass
                elif action.atype in self._MODE_COMMANDS:
                    self._is_absolute_move_mode[action.device] = action.atype == Gcode.G90
                elif action.atype in self._RESET_COMMANDS:
                    for key in pos:
                        if data[key] is not None:
                            position[key] = data[key]
                elif action.atype in self._CAMERA_COMMANDS:
                    if data['p']:
                        action_timespan = data['p'] * self._MSS_TO_SECS_RATIO
                    elif data['s']:
                        action_timespan = data['s']
                    else:
                        action_timespan = self._DEFAULT_SHUTTER_PRESS
                elif action.atype in self._MOVE_COMMANDS:
                    if action.atype == Gcode.G1:
                        feedrate = self._MAX_FEEDRATE / 2 \
                            if data['f'] is None else min(data['f'], self._MAX_FEEDRATE)
                    for key in pos:
                        if data and data[key] is not None:
                            if self._is_absolute_move_mode[action.device]:
                                position[key] = data[key]
                            else:
                                position[key] = position[key] + data[key]
                elif action.atype in self._HOME_COMANDS:
                    if data['f']:
                        feedrate = min(data['f'], self._MAX_FEEDRATE)

                    for key in pos:
                        if data[key] is not None:
                            low_bound = self._BOUNDS[key][0]
                            hi_bound = self._BOUNDS[key][1]
                            start = 0 if low_bound == 0 else random.randrange(low_bound, 0)
                            finish = random.randrange(0, hi_bound)
                            position[key] = finish - start
                elif action.atype == Gcode.M511:
                    self._is_locked[action.device] = not self._is_locked[action.device]
                elif action.atype == Gcode.M18:
                    # Disengage motors.
                    pass
                else:
                    raise NotImplementedError(f'Action {action.atype} not implemented.')

                now = datetime.datetime.now()

                if self._is_locked[action.device]:
                    resp = self._COPIS_RESPONSE(
                        payload=self._get_formatted_response(action.device),
                        report_on=now
                    )

                    self._response_buffer.append(resp)
                else:
                    delta = list(map(lambda start, end: abs(end - start), \
                        prev_position.values(), position.values()))
                    max_delta = max(delta)
                    travel_time = action_timespan

                    if feedrate and max_delta > 0:
                        travel_time = self._MINS_TO_SECS_RATIO * max_delta / feedrate

                    if action.atype == Gcode.G28:
                        for key in pos:
                            if data[key] is not None:
                                position[key] = 0.0

                    x, y, z, p, t = position.values()

                    start_resp = self._COPIS_RESPONSE(
                        payload=self._get_formatted_response(action.device, False),
                        report_on=now
                    )

                    self._last_positions[action.device] = Point5(x, y, z, p, t)

                    end_resp = self._COPIS_RESPONSE(
                        payload=self._get_formatted_response(action.device, True),
                        report_on=now+datetime.timedelta(0, travel_time)
                    )

                    self._response_buffer.extend([start_resp, end_resp])

        return sys.getsizeof(cmd)

    def output_line(self, _size=-1) -> bytes:
        """Puts a line of response data on the output buffer."""
        packet = ''.encode()
        if len(self._output_buffer) > 0:
            packet = f'{self._output_buffer.pop(0)}\r\n'.encode()

        return packet

    def _get_formatted_response(self, device_id, is_idle = None):
        ssf = 128 if is_idle is None else int(not is_idle)
        pos = self._last_positions[device_id]
        return (f'<id:{device_id},ssf:{ssf},pos:{pos.x:.3f},' +
            f'{pos.y:.3f},{pos.z:.3f},{pos.p:.3f},{pos.t:.3f}>')


    def _respond(self):
        while self._is_running:
            if len(self._response_buffer) > 0:
                now = datetime.datetime.now()
                to_report = list(filter(lambda r: r.report_on <= now, self._response_buffer))

                if to_report and len(to_report) > 0:
                    self._output_buffer.extend([r.payload for r in to_report])
                    for data in to_report:
                        self._response_buffer.remove(data)

                if to_report:
                    del to_report

            time.sleep(self._INTERVAL)
