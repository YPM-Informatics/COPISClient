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
from pydispatch import dispatcher

from copis.helpers import print_debug_msg, print_error_msg, print_info_msg
from copis.classes import SerialResponse

class ThreadTargetsMixin:
    """Implement COPIS Core thread targets using mixins."""
    def _listener(self) -> None:
        """Implements a listening thread."""
        read_thread = \
            next(filter(lambda t: t.thread == threading.current_thread(), self._read_threads))

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

                if self._keep_working and self._is_machine_locked:

                    print_debug_msg(self.console,
                        '**** Machine error-locked. stoping imaging!! ****', self._is_dev_env)

                    self.stop_work()
                else:
                    self._clear_to_send = controllers_unlocked or self.is_machine_idle

                if self.is_machine_idle:
                    print_debug_msg(self.console, '**** Machine is idle ****', self._is_dev_env)

                    if len(self._mainqueue) <= 0:
                        dispatcher.send('notify_machine_idle')

            if self._is_new_connection:
                if self._has_machine_reported:
                    if self._is_machine_locked and not controllers_unlocked:
                        controllers_unlocked = self._unlock_machine()
                        self._clear_to_send = controllers_unlocked or self.is_machine_idle

                        if controllers_unlocked:
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

                            self._query_machine()
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
                        self._query_machine()
                        machine_queried = True

        print_debug_msg(self.console,
            f'{read_thread.thread.name.capitalize()} stopped.', self._is_dev_env)

    def _worker(self, resuming=False, extra_callback=None) -> None:
        """Implements a worker thread."""
        t_name = self.work_type_name

        state = "resumed" if resuming else "started"
        print_debug_msg(self.console, f'{t_name} thread {state}', self._is_dev_env)

        def callback():
            if extra_callback:
                extra_callback()
            print_info_msg(self.console, f'{t_name} ended.')

        dispatcher.connect(callback, signal='notify_machine_idle')

        print_info_msg(self.console, f'{t_name} started.')

        had_error = False
        try:
            while self._keep_working and self.is_serial_port_connected:
                self._send_next()

        except AttributeError as err:
            print_error_msg(self.console, f'{t_name} thread stopped unexpectedly: {err.args[0]}')
            had_error = True

        finally:
            self._working_thread = None
            self._keep_working = False

            if not self._is_machine_paused:
                self._work_type = None

            if not had_error:
                print_debug_msg(self.console, f'{t_name} thread stopped.', self._is_dev_env)
