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

"""COPIS Core thread targets."""

import time
import threading
from datetime import datetime
from queue import Empty as QueueEmpty

from copis.helpers import print_debug_msg, print_error_msg, print_info_msg
from copis.globals import ActionType
from copis.classes import SerialResponse

class ThreadTargetsMixin:
    """Implement COPIS Core thread targets using mixins."""
    def listener(self) -> None:
        """Implements a listening thread."""
        read_thread = \
            next(filter(lambda t: t.thread == threading.current_thread(), self.read_threads))

        continue_listening = lambda t = read_thread: not t.stop

        machine_queried = False

        print_debug_msg(self.console,
            f'{read_thread.thread.name.capitalize()} started.', self._is_dev_env)

        while continue_listening():
            time.sleep(self._YIELD_TIMEOUT)
            #if not self._edsdk.is_waiting_for_image:
            resp = self._serial.read(read_thread.port)
            controllers_unlocked = False

            if resp:
                if isinstance(resp, SerialResponse):
                    dvc = self._get_device(resp.device_id)

                    if dvc:
                        dvc.set_serial_response(resp)

                if self.is_machine_busy and self._is_machine_locked:

                    print_debug_msg(self.console,
                        '**** Machine error-locked. stoping imaging!! ****', self._is_dev_env)

                    self.cancel_imaging()
                else:
                    self._clear_to_send = controllers_unlocked or self.is_machine_idle

                if self.is_machine_idle:
                    print_debug_msg(self.console,
                        '**** Machine is idle ****', self._is_dev_env)

            if self._is_new_connection:
                if self._has_machine_reported:
                    if self._is_machine_locked and not controllers_unlocked:
                        controllers_unlocked = self._unlock_controllers()
                        cmds = []
                        self._ensure_absolute_move_mode(cmds)

                        sent = False
                        if cmds:
                            sent = self.send_now(*cmds)

                        if sent:
                            for cmd in cmds:
                                if cmd.atype == ActionType.G90:
                                    dvc = self._get_device(cmd.device)
                                    dvc.is_move_absolute = True
                                    dvc.is_homed = False

                        self._clear_to_send = controllers_unlocked or self.is_machine_idle
                        self._connected_on = None
                        self._is_new_connection = False
                        machine_queried = False
                    else:
                        # if this connection happened after the devices last reported, query them.
                        if not machine_queried and \
                            self._connected_on >= self._machine_last_reported_on:
                            print_debug_msg(self.console,
                            f'Machine status stale (last: {self._machine_status}).',
                            self._is_dev_env)

                            self._query_devices()
                            machine_queried = True
                        elif self.is_machine_idle:
                            self._connected_on = None
                            self._is_new_connection = False
                            machine_queried = False
                else:
                    no_report_span = (datetime.now() - self._connected_on).total_seconds()

                    if not self._machine_last_reported_on or \
                        self._connected_on >= self._machine_last_reported_on:
                        print_debug_msg(self.console,
                            'Machine status stale (last: {0}) for {1} seconds.'
                                .format(self._machine_status, round(no_report_span, 2)),
                            self._is_dev_env)

                    # If no device has reported for 1 second since connecting, query the devices.
                    if not machine_queried and no_report_span > 1:
                        self._query_devices()
                        machine_queried = True

        print_debug_msg(self.console,
            f'{read_thread.thread.name.capitalize()} stopped.', self._is_dev_env)

    def sender(self) -> None:
        """Implments a sending thread."""
        print_debug_msg(self.console, 'Send thread started.', self._is_dev_env)

        while not self.stop_send_thread:
            try:
                commands = []

                while len(commands) < self._sidequeue_batch_size:
                    command = self._sidequeue.get(True, .1)
                    self._sidequeue.task_done()
                    commands.append(command)
            except QueueEmpty:
                if not commands:
                    continue

            while self.is_serial_port_connected and not self._clear_to_send \
                and not self.stop_send_thread:
                time.sleep(self._YIELD_TIMEOUT)

            self._send(*commands)

        print_debug_msg(self.console, 'Send thread stopped.', self._is_dev_env)

    def homer(self, batch_size=1) -> None:
        """Implements a homing thread."""
        print_debug_msg(self.console, 'Homing thread started.', self._is_dev_env)

        self._stop_sender()

        has_error = False

        try:
            while self.is_homing and self.is_serial_port_connected:
                self._send_next(batch_size)

            for dvc in self.devices:
                resp = dvc.serial_response
                dvc.is_homed = isinstance(resp, SerialResponse) and resp.is_idle

                dvc.is_move_absolute = True

        except AttributeError as err:
            has_error = True
            print_error_msg(self.console, f'Homing thread stopped unexpectedly: {err.args[0]}')

        finally:
            self.homing_thread = None
            self.is_homing = False
            print_info_msg(self.console, 'Homing ended.')

            if len(self.read_threads) > 0:
                self._start_sender()

            port_name = self._get_active_serial_port_name()
            read_thread = next(filter(lambda t: t.port == port_name, self.read_threads)) \
                if self.read_threads and len(self.read_threads) > 0 \
                    else None

            if not has_error and read_thread:
                self.go_to_ready()

        print_debug_msg(self.console, 'Homing thread stopped.', self._is_dev_env)

    def imager(self, batch_size=2, resuming=False) -> None:
        """Implements an imaging thread."""
        print_debug_msg(self.console, 'Imaging thread started', self._is_dev_env)

        self._stop_sender()

        try:
            while self.is_imaging and self.is_serial_port_connected:
                self._send_next(batch_size)

        except AttributeError as err:
            print_error_msg(self.console, f'Imaging thread stopped unexpectedly: {err.args[0]}')

        finally:
            self.imaging_thread = None
            self.is_imaging = False
            print_info_msg(self.console, 'Imaging ended.')

            if len(self.read_threads) > 0:
                self._start_sender()

        print_debug_msg(self.console, 'Imaging thread stopped.', self._is_dev_env)
