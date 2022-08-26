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

"""COPIS Core communication (serial, edsdk) related class members."""

from collections import namedtuple
from importlib import import_module
import threading
import time
from datetime import datetime
from typing import List

from canon.EDSDKLib import EvfDriveLens
from copis.classes import Action, Pose
from copis.coms import serial_controller
from copis.globals import ActionType
from copis.helpers import create_action_args, locked, print_error_msg, print_info_msg
from copis.classes import ReadThread


class CommunicationMembersMixin:
    """Implement COPIS Core component communication (serial, edsdk)
        related class members using mixins."""
    # --------------------------------------------------------------------------
    # Canon EDSDK methods
    # --------------------------------------------------------------------------

    @property
    def edsdk_device_list(self) -> List:
        """Returns the list of detected EDSDK devices."""
        device_list = []

        if not self._is_edsdk_enabled:
            print_error_msg(self.console, 'EDSDK is not enabled.')
        else:
            device_list = self._edsdk.device_list

        return device_list

    @property
    def is_edsdk_connected(self):
        """Returns a flag indicating whether a device is connected via edsdk."""
        return self._edsdk.is_connected

    def init_edsdk(self) -> None:
        """Initializes the Canon EDSDK controller."""
        if self._is_edsdk_enabled:
            return

        self._edsdk = import_module('copis.coms.edsdk_controller')
        self._edsdk.initialize(self.console)

        self._is_edsdk_enabled = self._edsdk.is_enabled

    def terminate_edsdk(self):
        """Disconnects all EDSDK connections; and terminates the Canon EDSDK."""
        if self._is_edsdk_enabled:
            self._edsdk.terminate()

    def connect_edsdk(self, device_id):
        """Connects to the provided camera via EDSDK."""
        connected = False

        if not self._is_edsdk_enabled:
            print_error_msg(self.console, 'EDSDK is not enabled.')
        else:
            device = self._get_device(device_id)

            if device:
                connected = self._edsdk.connect(device.port, device_id)
            else:
                print_error_msg(self.console, f'Camera {device_id} cannot be found.')

        return connected

    def disconnect_edsdk(self):
        """Disconnects from the currently connect camera via EDSDK."""
        if self._is_edsdk_enabled:
            return self._edsdk.disconnect()

        return True

    def start_edsdk_live_view(self):
        """Starts EDSDK Live View."""
        if not self._is_edsdk_enabled:
            print_error_msg(self.console, 'EDSDK is not enabled.')
        else:
            self._edsdk.start_live_view()

    def end_edsdk_live_view(self):
        """Stops EDSDK Live View."""
        if not self._is_edsdk_enabled:
            print_error_msg(self.console, 'EDSDK is not enabled.')
        else:
            self._edsdk.end_live_view()

    def download_edsdk_evf_data(self):
        """Downloads EDSDK Live View image frame data."""
        data = None

        if not self._is_edsdk_enabled:
            print_error_msg(self.console, 'EDSDK is not enabled.')
        else:
            data = self._edsdk.download_evf_data()

        return data

    def snap_edsdk_picture(self, do_af, device_id, save_path, keep_last_path):
        """Takes a picture via EDSDK."""
        if not self._is_edsdk_enabled:
            print_error_msg(self.console, 'EDSDK is not enabled.')
        else:
            c_args = create_action_args([1 if do_af else 0], 'V')
            payload = [Action(ActionType.EDS_SNAP, device_id, len(c_args), c_args)]

            self.play_poses([Pose(payload=payload)], save_path, keep_last_path)

    def do_edsdk_focus(self, shutter_release_time, device_id):
        """Focuses the camera via EDSDK."""
        if not self._is_edsdk_enabled:
            print_error_msg(self.console, 'EDSDK is not enabled.')
        else:
            c_args = create_action_args([shutter_release_time], 'S')
            payload = [Action(ActionType.EDS_FOCUS, device_id, len(c_args), c_args)]

            self.play_poses([Pose(payload=payload)])

    def do_evf_edsdk_focus(self):
        """Performs Live view specific EDSDK focus."""
        if not self._is_edsdk_enabled:
            print_error_msg(self.console, 'EDSDK is not enabled.')
        else:
            self._edsdk.evf_focus()

    def transfer_edsdk_pictures(self, destination, keep_last):
        """"Transfers pictures off of the camera via EDSDK."""
        if not self._is_edsdk_enabled:
            print_error_msg(self.console, 'EDSDK is not enabled.')
        else:
            if not keep_last:
                self._imaging_session_path = destination

        self._edsdk.transfer_pictures(destination)

    def edsdk_step_focus(self, step_info: int):
        """Steps the camera's focus given step info."""
        if not self._is_edsdk_enabled:
            print_error_msg(self.console, 'EDSDK is not enabled.')
        else:
            if step_info < 0:
                if step_info == -1:
                    step = EvfDriveLens.Near1
                elif step_info == -2:
                    step = EvfDriveLens.Near2
                else:
                    step = EvfDriveLens.Near3
            else:
                if step_info == 1:
                    step = EvfDriveLens.Far1
                elif step_info == 2:
                    step = EvfDriveLens.Far2
                else:
                    step = EvfDriveLens.Far3

        self._edsdk.step_focus(step)

    # --------------------------------------------------------------------------
    # Serial methods
    # --------------------------------------------------------------------------

    @property
    def serial_bauds(self):
        """Returns available serial com bauds."""
        return self._serial.BAUDS

    @property
    def serial_port_list(self) -> List:
        """Returns a safe (without the actual connections) representation
        of the serial ports list."""
        safe_list = []
        device = namedtuple('SerialDevice', 'name is_connected is_active')

        # pylint: disable=not-an-iterable
        for port in self._serial.port_list:
            safe_port = device(
                name=port.name,
                is_connected=port.connection is not None and port.connection.is_open,
                is_active=port.is_active
            )

            safe_list.append(safe_port)

        return safe_list

    @property
    def is_serial_port_connected(self):
        """Returns a flag indicating whether the active serial port is connected."""
        return self._serial.is_port_open

    def _get_active_serial_port_name(self):
        port = next(
                filter(lambda p: p.is_active, self.serial_port_list), None
            )
        return port.name if port else None

    def init_serial(self) -> None:
        """Initializes the serial controller."""
        if self._is_serial_enabled:
            return

        self._serial = serial_controller
        self._serial.initialize(self.console, self._is_dev_env)
        self._is_serial_enabled = True

    def terminate_serial(self):
        """Disconnects all serial connections; and terminates all serial threading activity."""
        self._keep_working = False

        if self._is_serial_enabled:
            for read_thread in self._read_threads:
                read_thread.stop = True
                if threading.current_thread() != read_thread.thread:
                    read_thread.thread.join()

            self._read_threads.clear()

            if self._working_thread:
                self._working_thread.join()
                self._working_thread = None

        if self._is_serial_enabled:
            self._serial.terminate()
            time.sleep(self._YIELD_TIMEOUT * 5)

    def update_serial_ports(self) -> None:
        """Updates the serial ports list."""
        self._serial.update_port_list()

    def snap_serial_picture(self, shutter_release_time, device_id, save_path, keep_last_path):
        """Takes a picture via serial."""
        if not self.is_serial_port_connected:
            print_error_msg(self.console, 'The machine is not connected.')
        else:
            c_args = create_action_args([shutter_release_time], 'S')
            payload = [Action(ActionType.C0, device_id, len(c_args), c_args)]

            self.play_poses([Pose(payload=payload)], save_path, keep_last_path)

    @locked
    def select_serial_port(self, name: str) -> bool:
        """Sets the active serial port to the provided one."""
        selected = self._serial.select_port(name)
        if not selected:
            print_error_msg(self.console, 'Unable to select serial port.')

        return selected

    @locked
    def connect_serial(self, baud: int = serial_controller.BAUDS[-1]) -> bool:
        """Connects to the active serial port."""
        if not self._is_serial_enabled:
            print_error_msg(self.console, 'Serial is not enabled.')
        else:
            connected = self._serial.open_port(baud)

            if connected:
                self._connected_on = datetime.now()

                port_name = next(
                        filter(lambda p: p.is_connected and p.is_active, self.serial_port_list)
                    ).name

                print_info_msg(self.console, f'Connected to device {port_name}')

                read_thread = threading.Thread(
                    target=self._listener,
                    name=f'read thread {port_name}')

                self._read_threads.append(ReadThread(thread=read_thread, port=port_name))
                read_thread.start()
            else:
                print_error_msg(self.console, 'Unable to connect to device.')

        self._is_new_connection = connected
        return connected

    @locked
    def disconnect_serial(self):
        """disconnects from the active serial port."""
        self._keep_working = False

        if self.is_serial_port_connected:
            port_name = self._get_active_serial_port_name()
            read_thread = next(filter(lambda t: t.port == port_name, self._read_threads))

            if read_thread:
                read_thread.stop = True
                if threading.current_thread() != read_thread.thread:
                    read_thread.thread.join()

                self._read_threads.remove(read_thread)

            if self._working_thread:
                self._working_thread.join()
                self._working_thread = None

        if self.is_serial_port_connected:
            self._serial.close_port()
            time.sleep(self._YIELD_TIMEOUT * 5)

        self._is_new_connection = False
        self._connected_on = None
        print_info_msg(self.console, f'Disconnected from device {port_name}')
