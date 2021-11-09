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

"""COPIS Application Core functions."""

__version__ = ""

# pylint: disable=using-constant-test
from datetime import datetime
import sys

if sys.version_info.major < 3:
    print("You need to run this on Python 3")
    sys.exit(-1)

# pylint: disable=wrong-import-position
import threading
import time
import warnings

from queue import Queue
from typing import List
from glm import vec3

from copis.command_processor import serialize_command
from copis.helpers import (print_error_msg, print_debug_msg,
    print_info_msg)
from copis.globals import ActionType, DebugEnv
from copis.config import Config
from copis.classes import (
    Action, Device, MonitoredList, Object3D, OBJObject3D)

from ._console_output import ConsoleOutput
from ._thread_targets import ThreadTargetsMixin
from ._machine_members import MachineMembersMixin
from ._component_members import ComponentMembersMixin
from ._communication_members import CommunicationMembersMixin


class COPISCore(
    ThreadTargetsMixin,
    MachineMembersMixin,
    ComponentMembersMixin,
    CommunicationMembersMixin):
    """COPISCore. Connects and interacts with devices in system.

    Attributes:
        points: A list of points representing a path.
        devices: A list of devices (cameras).
        objects: A list of proxy objects.
        selected_device: Current selected device. -1 if not selected.
        selected_points: A list of integers representing the index of selected
            points.

    Emits:
        core_a_list_changed: When the action list has changed.
        core_a_selected: When a new point (action) has been selected.
        core_a_deselected: When a point (action) has been deselected.
        core_d_list_changed: When the device list has changed.
        core_d_selected: When a device has been selected.
        core_d_deselected: When the current device has been deselected.
        core_o_selected: When a proxy object has been selected.
        core_o_deselected: When the current proxy object has been deselected.

        msg_info: Any copiscore informational message.
        msg_debug: Any copiscore debug message.
        msg_error: Any copiscore access error message.

    """

    _YIELD_TIMEOUT = .001 # 1 millisecond
    _G_COMMANDS = [ActionType.G0, ActionType.G1, ActionType.G2, ActionType.G3,
            ActionType.G4, ActionType.G17, ActionType.G18, ActionType.G19,
            ActionType.G90, ActionType.G91, ActionType.G92]
    _C_COMMANDS = [ActionType.C0, ActionType.C1]

    def __init__(self, parent=None) -> None:
        """Initializes a CopisCore instance."""
        self.config = parent.config if parent else Config()
        self.evf_thread = None

        self.console = ConsoleOutput(parent)

        self._is_dev_env = self.config.settings.debug_env == DebugEnv.DEV.value
        self._is_edsdk_enabled = False
        self._edsdk = None
        self._is_serial_enabled = False
        self._serial = None
        self._is_new_connection = False
        self._connected_on = None

        self.init_edsdk()
        self.init_serial()

        self._check_configs()

        # clear to send, enabled after responses
        self._clear_to_send = False

        # True if sending actions, false if paused
        self.is_imaging = False
        self.is_homing = False
        self.is_paused = False

        self.read_threads = []
        self.send_thread = None
        self.stop_send_thread = False
        self.imaging_thread = None
        self.homing_thread = None

        self._mainqueue = None
        self._sidequeue = Queue(0)
        self._sidequeue_batch_size = 1

        # list of actions (paths)
        self._actions: List[Action] = MonitoredList('core_a_list_changed')

        # list of devices (cameras)
        self._devices: List[Device] = MonitoredList('core_d_list_changed',
            iterable=self.config.machine_settings.devices)

        # list of objects (proxy objects)
        self._objects: List[Object3D] = MonitoredList('core_o_list_changed',
            iterable=[
                # start with handsome dan :)
                OBJObject3D('model/handsome_dan.obj', scale=vec3(20, 20, 20)),
            ])

        self._selected_points: List[int] = []
        self._selected_device: int = -1

    @property
    def is_dev_env(self):
        """Return a flag indicating whether we are in a dev environment."""
        return self._is_dev_env

    def _check_configs(self) -> None:
        warn = self._is_dev_env
        msg = None
        machine_config = self.config.machine_settings

        if machine_config.machine is None:
            # If the machine is not configured, throw no matter what.
            warn = False
            msg = 'The machine is not configured.'

        # TODO:
        # - Check 3 cameras per chamber max.
        # - Check cameras within chamber bounds.

        if msg is not None:
            warning = UserWarning(msg)
            if warn:
                warnings.warn(warning)
            else:
                raise warning

    def _ensure_absolute_move_mode(self, cmd_list):
        device_ids = []

        for dvc in self.devices:
            if not dvc.is_move_absolute:
                cmd_list.append(Action(ActionType.G90, dvc.device_id))

            device_ids.append(dvc.device_id)

        return device_ids

    def _send_next(self, batch_size=1):
        if not self.is_serial_port_connected:
            return

        # Wait until we get the ok from listener.
        while self.is_serial_port_connected and not self._clear_to_send \
            and self.is_machine_busy:
            time.sleep(self._YIELD_TIMEOUT)

        if not self._sidequeue.empty():
            commands = []
            while len(commands) < self._sidequeue_batch_size:
                command = self._sidequeue.get_nowait()
                self._sidequeue.task_done()
                commands.append(command)

                if self._sidequeue.empty():
                    break

            self._send(*commands)
            # Maybe don't return from here so that the command in the main
            # queue can still be sent?
            return

        if self.is_machine_busy and self._mainqueue:
            currents = []
            for _ in range(batch_size):
                if len(self._mainqueue) > 0:
                    currents.append(self._mainqueue.pop(0))

            self._send(*currents)
            self._clear_to_send = False

        else:
            self.is_imaging = False
            self.is_homing = False
            self._clear_to_send = True

    def _send(self, *commands):
        """Send command to machine."""

        if not self.is_serial_port_connected:
            return

        dvcs = []
        cmds = []
        for command in commands:
            if not any(d.device_id == command.device for d in dvcs):
                dvcs.append(self._get_device(command.device))

            cmds.append(serialize_command(command))

        cmd_lines = '\r'.join(cmds)

        if self._serial.is_port_open:

            print_debug_msg(self.console, 'Writing> [{0}] to device{1} '
                    .format(cmd_lines.replace("\r", "\\r"), "s" if len(dvcs) > 1 else "") +
                f'{", ".join([str(d.device_id) for d in dvcs])}.', self._is_dev_env)

            for dvc in dvcs:
                dvc.set_is_writing()

            self._serial.write(cmd_lines)

        # debug command
        # logging.debug(command)

        # if command.atype in self._G_COMMANDS:

        #     # try writing to printer
        #     # ser.write(command.encode())
        #     pass

        # elif command.atype == ActionType.C0:
        #     if self._edsdk.connect(command.device):
        #         self._edsdk.take_picture()

        # elif command.atype == ActionType.C1:
        #     pass

        # elif command.atype == ActionType.M24:
        #     pass

        # elif command.atype == ActionType.M17:
        #     pass

        # elif command.atype == ActionType.M18:
        #     pass

    def _start_sender(self) -> None:
        self.stop_send_thread = False
        self.send_thread = threading.Thread(
            target=self.sender,
            name='send thread')
        self.send_thread.start()

    def _stop_sender(self) -> None:
        if self.send_thread:
            self.stop_send_thread = True
            self.send_thread.join()
            self.send_thread = None

    def start_imaging(self, startindex=0) -> bool:
        """Starts the imaging sequence, following the define action path."""

        if not self.is_serial_port_connected:
            print_error_msg(self.console,
                'The machine needs to be connected before imaging can start.')
            return False

        if self.is_homing:
            print_error_msg(self.console, 'Cannot image while homing the machine.')
            return False

        if self.is_imaging:
            print_error_msg(self.console, 'Imaging already in progress.')
            return False

        if not self.is_machine_idle:
            print_error_msg(self.console, 'The machine needs to be homed before imaging can start.')
            return False

        self._mainqueue = self._actions.copy()
        device_count = len(set(a.device for a in self._mainqueue))
        batch_size = 2 * device_count

        print_debug_msg(self.console, f'Imaging batch size is: {batch_size}.', self._is_dev_env)

        self.is_imaging = True
        self._clear_to_send = True
        self.imaging_thread = threading.Thread(
            target=self.imager,
            name='imaging thread',
            kwargs={
                "resuming": True,
                "batch_size": batch_size
            }
        )
        self.imaging_thread.start()
        print_info_msg(self.console, 'Imaging started.')
        return True

    def start_homing(self) -> bool:
        """Start the homing sequence, following the steps in the configuration."""
        if not self.is_serial_port_connected:
            print_error_msg(self.console,
                'The machine needs to be connected before homing can start.')
            return False

        if self.is_imaging:
            print_error_msg(self.console, 'Cannot home the machine while imaging.')
            return False

        if self.is_homing:
            print_error_msg(self.console, 'Homing already in progress.')
            return False

        homing_actions = self.config.machine_settings.machine.homing_actions.copy()

        if not homing_actions or len(homing_actions) == 0:
            print_error_msg(self.console, 'No homing sequence to provided.')
            return False

        homing_cmds = []
        # Ensure we are in absolute motion mode.
        device_ids = self._ensure_absolute_move_mode(homing_cmds)

        # Only send homing commands for connected devices.
        homing_actions = filter(lambda c: c.device in device_ids, homing_actions)

        homing_cmds.extend(homing_actions)

        self._mainqueue = homing_cmds
        batch_size = len(set(a.device for a in self._mainqueue))

        print_debug_msg(self.console, f'Homing batch size is: {batch_size}.', self._is_dev_env)

        self.is_homing = True
        self._clear_to_send = True
        self.homing_thread = threading.Thread(
            target=self.homer,
            name='homing thread',
            kwargs={"batch_size": batch_size}
        )
        self.homing_thread.start()
        print_info_msg(self.console, 'Homing started.')
        return True

    def cancel_imaging(self) -> None:
        """Stops the imaging sequence."""

        self.pause()
        self.is_paused = False
        self._mainqueue = None
        self._clear_to_send = True
        print_info_msg(self.console, 'Imaging stopped.')

    def pause(self) -> bool:
        """Pause the current run, saving the current position."""

        if not self.is_imaging:
            return False

        self.is_paused = True
        self.is_imaging = False

        # try joining the print thread: enclose it in try/except because we
        # might be calling it from the thread itself
        try:
            self.imaging_thread.join()
        except RuntimeError as e:
            pass

        self.imaging_thread = None
        return True

    def resume(self) -> bool:
        """Resume the current run."""

        if not self.is_paused:
            return False

        # send commands to resume printing
# TODO: When resuming is enabled, send batch size to _do_imaging from here.
# Batch size: 2 x number of distinct devices in action list.
        self.is_paused = False
        self.is_imaging = True
        self.imaging_thread = threading.Thread(
            target=self.imager,
            name='imaging thread',
            kwargs={"resuming": True}
        )
        self.imaging_thread.start()
        print_info_msg(self.console, 'Imaging resumed.')
        return True

    def send_now(self, *commands) -> bool:
        """Send a command to machine ahead of the command queue."""
        # Don't send now if imaging and G or C commands are sent.
        # No jogging while homing or imaging is in process.
        excluded = self._G_COMMANDS + self._C_COMMANDS
        if self.is_machine_busy and any(cmd.atype in excluded for cmd in commands):
            print_error_msg(self.console, 'Action commands not allowed when busy.')
            return False

        if self.is_serial_port_connected:
            self._sidequeue_batch_size = len(commands)

            print_debug_msg(self.console,
                f'Side queue batch size is: {self._sidequeue_batch_size}.',
                self._is_dev_env)

            for command in commands:
                self._sidequeue.put_nowait(command)
            return True

        print_error_msg(self.console, 'Not connected to device.')
        return False
