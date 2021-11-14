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
from copis.globals import ActionType, DebugEnv, WorkType
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
        self._evf_thread = None

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
        self._keep_working = False
        self._is_machine_paused = False

        self._read_threads = []
        self._working_thread = None

        self._mainqueue = []

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

    def _send_next(self):
        if not self.is_serial_port_connected:
            return

        # Wait until we get the ok from listener.
        while self.is_serial_port_connected and not self._clear_to_send \
            and self._keep_working:
            time.sleep(self._YIELD_TIMEOUT)

        if self._keep_working and len(self._mainqueue) > 0:
            packet = self._mainqueue.pop(0)

            print_debug_msg(self.console, f'Packet size is: {len(packet)}',
                self._is_dev_env)

            self._send(*packet)
            self._clear_to_send = False

        else:
            self._keep_working = False
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

    def start_imaging(self) -> bool:
        """Starts the imaging sequence, following the define action path."""
        if not self.is_serial_port_connected:
            print_error_msg(self.console,
                'The machine needs to be connected before imaging can start.')
            return False

        if self._is_machine_busy:
            print_error_msg(self.console, 'The machine is busy.')
            return False

        if not self.is_machine_idle:
            print_error_msg(self.console, 'The machine needs to be homed before imaging can start.')
            return False

        device_ids = list(set(a.device for a in self._actions))
        # 1 move command * 1 shutter command.
        batch_size = 2
        if self.config.machine_settings.machine.is_parallel_execution:
            batch_size = batch_size * len(device_ids)

        header = self._absolute_move_commands
        body = self._chunk_actions(batch_size)
        footer = self._get_initialization_commands(ActionType.G1)
        footer.extend(self._disengage_motors_commands)

        self._mainqueue = []
        self._mainqueue.extend(header)
        self._mainqueue.extend(body)
        self._mainqueue.extend(footer)

        self._keep_working = True
        self._clear_to_send = True
        self._working_thread = threading.Thread(
            target=self._worker,
            name='working thread',
            kwargs={
                "work_type": WorkType.IMAGING
            }
        )
        self._working_thread.start()
        return True

    def start_homing(self) -> bool:
        """Start the homing sequence, following the steps in the configuration."""
        def homing_callback():
            for dvc in self.devices:
                dvc.is_homed = True

        if not self.is_serial_port_connected:
            print_error_msg(self.console,
                'The machine needs to be connected before homing can start.')
            return False

        if self._working_thread:
            print_error_msg(self.console, 'The machine is busy.')
            return False

        homing_actions = self.config.machine_settings.machine.homing_actions.copy()

        if not homing_actions or len(homing_actions) == 0:
            print_error_msg(self.console, 'No homing sequence to provided.')
            return False

        # Only send homing commands for connected devices.
        device_ids = [d.device_id for d in self.devices]
        homing_actions = list(filter(lambda c: c.device in device_ids, homing_actions))

        batch_size = len(set(a.device for a in homing_actions))

        header = self._absolute_move_commands
        body = self._chunk_actions(batch_size, homing_actions)
        footer = self._get_initialization_commands(ActionType.G1)
        footer.extend(self._disengage_motors_commands)

        self._mainqueue = []
        self._mainqueue.extend(header)
        self._mainqueue.extend(body)
        self._mainqueue.extend(footer)

        self._keep_working = True
        self._clear_to_send = True
        self._working_thread = threading.Thread(
            target=self._worker,
            name='working thread',
            kwargs={
                "work_type": WorkType.HOMING,
                "extra_callback": homing_callback
            }
        )
        self._working_thread.start()
        print_info_msg(self.console, 'Homing started.')
        return True

    def stop_work(self) -> None:
        """Stops work in progress."""

        if self.pause_work():
            self._mainqueue = []
            self._is_machine_paused = False
            self._clear_to_send = True
            print_info_msg(self.console, 'Work stopped.')

    def pause_work(self) -> bool:
        """Pause work in progress, saving the current position."""

        if not self._working_thread:
            print_error_msg(self.console, 'No working thread to pause.')
            return False

        self._is_machine_paused = True
        self._keep_working = False

        # try joining the print thread: enclose it in try/except because we
        # might be calling it from the thread itself
        try:
            self._working_thread.join()
            self._working_thread = None
            print_info_msg(self.console, 'Work paused.')
            return True
        except RuntimeError as err:
            print_error_msg(self.console, f'Cannot join working thread: {err.args[0]}')
            return False

    def resume_work(self) -> bool:
        """Resume the current run."""

        if not self._is_paused:
            print_error_msg(self.console, 'Work is not paused.')
            return False

        # send commands to resume work
        device_count = len(set(a.device for a in self._mainqueue))
        batch_size = 2 * device_count

        self._is_machine_paused = False
        self._keep_working = True
        self._working_thread = threading.Thread(
            target=self._worker,
            name='working thread',
            kwargs={
                # TODO: Figure out how to retrieve this on resumption.
                "work_type": WorkType.IMAGING,
                "batch_size": batch_size,
                "resume": True
            }
        )
        self._working_thread.start()
        print_info_msg(self.console, 'Work resumed.')
        return True

    def send_now(self, *commands) -> bool:
        """Send a command to machine ahead of the command queue."""
        # Don't send now if imaging and G or C commands are sent.
        # No jogging while homing or imaging is in process.
        excluded = self._G_COMMANDS + self._C_COMMANDS
        if self._keep_working and any(cmd.atype in excluded for cmd in commands):
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
