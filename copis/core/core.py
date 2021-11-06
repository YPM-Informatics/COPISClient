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

from collections import namedtuple
from importlib import import_module
from functools import wraps
from queue import Queue, Empty as QueueEmpty
from typing import List
from glm import vec3

from pydispatch import dispatcher

from .console_output import _ConsoleOutput

from copis.command_processor import deserialize_command, serialize_command
from copis.coms import serial_controller
from copis.helpers import create_action_args, print_error_msg, print_debug_msg, print_info_msg
from copis.globals import ActionType, ComStatus, DebugEnv
from copis.config import Config
from copis.classes import (
    Action, Device, MonitoredList, Object3D, OBJObject3D,
    ReadThread, SerialResponse)


def locked(func):
    """Provide thread locking mechanism."""
    @wraps(func)
    def inner(*args, **kw):
        with inner.lock:
            return func(*args, **kw)
    inner.lock = threading.Lock()
    return inner


class COPISCore:
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
        """Initialize a CopisCore instance."""
        self.config = parent.config if parent else Config()
        self.evf_thread = None

        self.console = _ConsoleOutput(parent)

        self._is_dev_env = self.config.settings.debug_env == DebugEnv.DEV.value
        self._is_edsdk_enabled = False
        self._edsdk = None
        self._is_serial_enabled = False
        self._serial = None

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

    @locked
    def disconnect(self):
        """disconnects from the active serial port."""
        if self.is_serial_port_connected:
            port_name = self._get_active_serial_port_name()
            read_thread = next(filter(lambda t: t.port == port_name, self.read_threads))

            if read_thread:
                read_thread.stop = True
                if threading.current_thread() != read_thread.thread:
                    read_thread.thread.join()

                self.read_threads.remove(read_thread)

            if self.imaging_thread:
                self.is_imaging = False
                self.imaging_thread.join()
                self.imaging_thread = None

            if self.homing_thread:
                self.is_homing = False
                self.homing_thread.join()
                self.homing_thread = None

            if len(self.read_threads) == 0:
                self._stop_sender()

        self.is_imaging = False
        self.is_homing = False

        if self.is_serial_port_connected:
            self._serial.close_port()
            time.sleep(self._YIELD_TIMEOUT * 5)

        print_info_msg(self.console, f'Disconnected from device {port_name}.')

    @locked
    def connect(self, baud: int = serial_controller.BAUDS[-1]) -> bool:
        """Connects to the active serial port."""
        if not self._is_serial_enabled:
            print_error_msg(self.console, 'Serial is not enabled')
        else:
            connected = self._serial.open_port(baud)

            if connected:
                port_name = next(
                        filter(lambda p: p.is_connected and p.is_active, self.serial_port_list)
                    ).name

                print_info_msg(self.console, f'Connected to device {port_name}.')

                read_thread = threading.Thread(
                    target=self._listen,
                    name=f'read thread {port_name}')

                self.read_threads.append(ReadThread(thread=read_thread, port=port_name))
                read_thread.start()

                self._start_sender()
            else:
                print_error_msg(self.console, 'Unable to connect to device.')

        return connected

    def _listen(self) -> None:
        read_thread = \
            next(filter(lambda t: t.thread == threading.current_thread(), self.read_threads))

        continue_listening = lambda t = read_thread: not t.stop

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
                else:
                    if resp == 'COPIS_READY':
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

                if self.is_machine_busy and self._is_machine_locked():

                    print_debug_msg(self.console,
                        '**** Machine error-locked. stoping imaging!! ****', self._is_dev_env)

                    self.cancel_imaging()
                else:
                    self._clear_to_send = controllers_unlocked or self.is_machine_idle

                if self.is_machine_idle:
                    print_debug_msg(self.console,
                        '**** Machine is idle ****', self._is_dev_env)

        print_debug_msg(self.console,
            f'{read_thread.thread.name.capitalize()} stopped.', self._is_dev_env)

    def _get_device(self, device_id):
        return next(filter(lambda d: d.device_id == device_id, self.devices), None)

    def _is_machine_locked(self):
        for dvc in self.devices:
            if dvc.serial_response:
                flags = dvc.serial_response.system_status_flags

                if flags and len(flags) == 8 and int(flags[0]):
                    return True

        return False

    @property
    def is_machine_idle(self):
        """Returns a value indicating whether the machine is idle."""
        return all(dvc.serial_status == ComStatus.IDLE for dvc in self.devices)

    @property
    def is_machine_homed(self):
        """Returns a value indicating whether the machine is homed."""
        return all(dvc.is_homed for dvc in self.devices)

    @property
    def is_machine_busy(self):
        """Returns a value indicating whether the machine is busy
        (imaging or homing)."""
        return self.is_homing or self.is_imaging

    def _start_sender(self) -> None:
        self.stop_send_thread = False
        self.send_thread = threading.Thread(
            target=self._sender,
            name='send thread')
        self.send_thread.start()

    def _stop_sender(self) -> None:
        if self.send_thread:
            self.stop_send_thread = True
            self.send_thread.join()
            self.send_thread = None

    def _sender(self) -> None:
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
            target=self._do_imaging,
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
            target=self._do_homing,
            name='homing thread',
            kwargs={"batch_size": batch_size}
        )
        self.homing_thread.start()
        print_info_msg(self.console, 'Homing started.')
        return True

    def go_to_ready(self):
        """Sends the gantries to their initial positions."""
        print_info_msg(self.console, 'Go to ready started.')

        self._initialize_gantries(ActionType.G1)

        print_info_msg(self.console, 'Go to ready ended.')

    def set_ready(self):
        """Initializes the gantries to their current positions."""
        print_info_msg(self.console, 'Set ready started.')

        self._initialize_gantries(ActionType.G92)

        for dvc in self.devices:
            dvc.is_homed = True

        print_info_msg(self.console, 'Set ready ended.')

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
            target=self._do_imaging,
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

            print_debug_msg(self.console, f'Side queue batch size is: {self._sidequeue_batch_size}.',
                self._is_dev_env)

            for command in commands:
                self._sidequeue.put_nowait(command)
            return True

        print_error_msg(self.console, 'Not connected to device.')
        return False

    def _initialize_gantries(self, atype: ActionType):
        cmds = []
        actions = []
        g_code = str(atype).split('.')[1]
        device_ids = self._ensure_absolute_move_mode(cmds)

        for device_id in device_ids:
            cmd_str = ''
            x, y, z, p, t = self._get_device(device_id).initial_position

            if device_id == 0:
                cmd_str = f'{g_code}X{x}Y{y}Z{z}P{p}T{t}'
            elif device_id == 1:
                cmd_str = f'>{device_id}{g_code}X{x}Y{y}Z{z}P{p}T{t}'
            elif device_id == 2:
                cmd_str = f'>{device_id}{g_code}X{x}Y{y}Z{z}P{p}T{t}'

            actions.append(deserialize_command(cmd_str))

        actions.reverse()
        sent = True

        if cmds:
            sent = self.send_now(*cmds)
        if sent:
            sent = self.send_now(*actions)

        if sent:
            for cmd in cmds:
                if cmd.atype == ActionType.G90:
                    dvc = self._get_device(cmd.device)
                    dvc.is_move_absolute = True

    def _ensure_absolute_move_mode(self, cmd_list):
        device_ids = []

        for dvc in self.devices:
            if not dvc.is_move_absolute:
                cmd_list.append(Action(ActionType.G90, dvc.device_id))

            device_ids.append(dvc.device_id)

        return device_ids

    def _unlock_controllers(self):
        cmds = []

        for dvc in self.devices:
            if dvc.serial_response:
                flags = dvc.serial_response.system_status_flags

                if flags and len(flags) == 8 and int(flags[0]):
                    cmd = Action(ActionType.M511, dvc.device_id)
                    cmds.append(cmd)

        if cmds:
            return self.send_now(*cmds)

        return False

    def _do_imaging(self, batch_size=2, resuming=False) -> None:
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

    def _do_homing(self, batch_size=1) -> None:
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

    # --------------------------------------------------------------------------
    # Action and device data methods
    # --------------------------------------------------------------------------

    def add_action(self, atype: ActionType, device: int, *args) -> bool:
        """TODO: validate args given atype"""
        new = Action(atype, device, len(args), list(args))

        self._actions.append(new)

        # if certain type, broadcast that positions are modified
        if atype in (ActionType.G0, ActionType.G1, ActionType.G2, ActionType.G3):
            dispatcher.send('core_a_list_changed')

        return True

    def remove_action(self, index: int) -> Action:
        """Removes an action given action list index."""
        action = self._actions.pop(index)
        dispatcher.send('core_a_list_changed')
        return action

    def clear_action(self) -> None:
        """Removes all actions from actions list."""
        self._actions.clear()
        dispatcher.send('core_a_list_changed')

    @property
    def actions(self) -> List[Action]:
        return self._actions

    @property
    def devices(self) -> List[Device]:
        return self._devices

    @property
    def objects(self) -> List[Object3D]:
        return self._objects

    @property
    def selected_device(self) -> int:
        return self._selected_device

    @property
    def selected_points(self) -> List[int]:
        return self._selected_points

    def select_device(self, index: int) -> None:
        """Select device given index in devices list."""
        if index < 0:
            self._selected_device = -1
            dispatcher.send('core_d_deselected')

        elif index < len(self._devices):
            self._selected_device = index
            self.select_point(-1)
            dispatcher.send('core_o_deselected')
            dispatcher.send('core_d_selected', device=self._devices[index])

        else:
            print_error_msg(self.console, f'invalid device index {index}.')

    def select_point(self, index: int, clear: bool = True) -> None:
        """Add point to points list given index in actions list.

        Args:
            index: An integer representing index of action to be selected.
            clear: A boolean representing whether to clear the list before
                selecting the new point or not.
        """
        if index == -1:
            self._selected_points.clear()
            dispatcher.send('core_a_deselected')
            return

        if index >= len(self._actions):
            return

        if clear:
            self._selected_points.clear()

        if index not in self._selected_points:
            self._selected_points.append(index)
            self.select_device(-1)
            dispatcher.send('core_o_deselected')
            dispatcher.send('core_a_selected', points=self._selected_points)

    def deselect_point(self, index: int) -> None:
        """Remove point from selected points given index in actions list."""
        try:
            self._selected_points.remove(index)
            dispatcher.send('core_a_deselected')
        except ValueError:
            return

    def update_selected_points(self, args) -> None:
        """Update position of points in selected points list."""
        args = create_action_args(args)
        for id_ in self.selected_points:
            for i in range(min(len(self.actions[id_].args), len(args))):
                self.actions[id_].args[i] = args[i]

        dispatcher.send('core_a_list_changed')

    def export_actions(self, filename: str = None) -> list:
        """Serialize action list and write to file.

        TODO: Expand to include not just G0 and C0 actions
        """

        lines = []

        for action in self._actions:
            line = serialize_command(action)
            lines.append(line)

        if filename is not None:
            with open(filename, 'w') as file:
                file.write('\n'.join(lines))

        dispatcher.send('core_a_exported', filename=filename)
        return lines

    # --------------------------------------------------------------------------
    # Canon EDSDK methods
    # --------------------------------------------------------------------------

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

    # --------------------------------------------------------------------------
    # Serial methods
    # --------------------------------------------------------------------------

    def init_serial(self) -> None:
        """Initializes the serial controller."""
        if self._is_serial_enabled:
            return

        self._serial = serial_controller
        self._serial.initialize(self.console, self._is_dev_env)
        self._is_serial_enabled = True

    def terminate_serial(self):
        """Disconnects all serial connections; and terminates all serial threading activity."""
        if self._is_serial_enabled:
            for read_thread in self.read_threads:
                read_thread.stop = True
                if threading.current_thread() != read_thread.thread:
                    read_thread.thread.join()

            self.read_threads.clear()

            if self.imaging_thread:
                self.is_imaging = False
                self.imaging_thread.join()
                self.imaging_thread = None

            if self.homing_thread:
                self.is_homing = False
                self.homing_thread.join()
                self.homing_thread = None

            self._stop_sender()

        self.is_imaging = False
        self.is_homing = False

        if self._is_serial_enabled:
            self._serial.terminate()
            time.sleep(self._YIELD_TIMEOUT * 5)

    @locked
    def select_serial_port(self, name: str) -> bool:
        """Sets the active serial port to the provided one."""
        selected = self._serial.select_port(name)
        if not selected:
            print_error_msg(self.console, 'Unable to select serial port.')

        return selected

    def update_serial_ports(self) -> None:
        """Updates the serial ports list."""
        self._serial.update_port_list()

    def _get_active_serial_port_name(self):
        port = next(
                filter(lambda p: p.is_active, self.serial_port_list), None
            )
        return port.name if port else None


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
        """Return a flag indicating whether the active serial port is connected."""
        return self._serial.is_port_open

    @property
    def is_dev_env(self):
        """Return a flag indicating whether we are in a dev environment."""
        return self._is_dev_env
