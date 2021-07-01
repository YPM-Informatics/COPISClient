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
import logging
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

from .command_processor import deserialize_command, serialize_command
from .coms import serial_controller
from .helpers import create_action_args, print_timestamped
from .globals import ActionType, ComStatus, DebugEnv
from .classes import (
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
        core_error: Any copiscore access errors.
    """

    _YIELD_TIMEOUT = .001 # 1 millisecond
    _G_COMMANDS = [ActionType.G0, ActionType.G1, ActionType.G2, ActionType.G3,
            ActionType.G4, ActionType.G17, ActionType.G18, ActionType.G19,
            ActionType.G90, ActionType.G91, ActionType.G92]
    _C_COMMANDS = [ActionType.C0, ActionType.C1]

    def __init__(self, parent) -> None:
        """Initialize a CopisCore instance."""
        self.config = parent.config
        self._is_dev_env = self.config.settings.debug_env == DebugEnv.DEV.value

        self._is_edsdk_enabled = False
        self._edsdk = None
        self.evf_thread = None

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

        # logging
        self.sentlines = {}
        self.sent = []

        self.read_threads = []
        self.send_thread = None
        self.stop_send_thread = False
        self.imaging_thread = None
        self.homing_thread = None

        self._mainqueue = None
        self._sidequeue = Queue(0)

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

        dispatcher.send('core_message', message=f'Disconnected from device {port_name}')

    @locked
    def connect(self, baud: int = serial_controller.BAUDS[-1]) -> bool:
        """Connects to the active serial port."""
        if not self._is_serial_enabled:
            dispatcher.send('core_message', message='Serial is not enabled')
        else:
            connected = self._serial.open_port(baud)

            if connected:
                port_name = next(
                        filter(lambda p: p.is_connected and p.is_active, self.serial_port_list)
                    ).name

                read_thread = threading.Thread(
                    target=self._listen,
                    name=f'read thread {port_name}')

                self.read_threads.append(ReadThread(thread=read_thread, port=port_name))
                read_thread.start()

                self._start_sender()

                dispatcher.send('core_message', message=f'Connected to device {port_name}')
            else:
                dispatcher.send('core_message', message='Unable to connect to device')

        return connected

    def _listen(self) -> None:
        read_thread = \
            next(filter(lambda t: t.thread == threading.current_thread(), self.read_threads))
        continue_listening = lambda t = read_thread: not t.stop

        while continue_listening():
            time.sleep(self._YIELD_TIMEOUT)
            #if not self._edsdk.is_waiting_for_image:
            resp = self._serial.read(read_thread.port)

            if resp:
                if isinstance(resp, SerialResponse):
                    dvc = self._get_device(resp.device_id)

                    self._print_debug_msg('Before setting device response - ' +
                        f'is machine idle> {self.is_machine_idle}')

                    if dvc:
                        dvc.serial_response = resp

                        self._print_debug_msg('After setting device response - ' +
                            f'is machine idle> {self.is_machine_idle}')
                else:
                    if resp == 'COPIS_READY':
                        cmds = []
                        self._ensure_absolute_move_mode(cmds)

                        for cmd in cmds:
                            self.send_now(cmd)
                            if cmd.atype == ActionType.G90:
                                dvc = self._get_device(cmd.device)
                                dvc.is_move_absolute = True
                                dvc.is_homed = False

                                self._print_debug_msg('Reset - device serial status> ' +
                                    f'{dvc.serial_status}')

                        self._print_debug_msg(f'Reset - is machine idle> {self.is_machine_idle}')

                    dispatcher.send('core_message', message=resp)

                self._clear_to_send = self.is_machine_idle

                self._print_debug_msg('Set clear to send - is machine idle> ' +
                    f'{self.is_machine_idle} - clear to send> {self._clear_to_send}')

    def _get_device(self, device_id):
        return next(filter(lambda d: d.device_id == device_id, self.devices), None)

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
        while not self.stop_send_thread:
            try:
                command = self._sidequeue.get(True, 0.1)
            except QueueEmpty:
                continue

            while self.is_serial_port_connected and not self._clear_to_send:
                time.sleep(self._YIELD_TIMEOUT)

            self._send(command)

            while self.is_serial_port_connected and not self._clear_to_send:
                time.sleep(self._YIELD_TIMEOUT)

    def start_imaging(self, startindex=0) -> bool:
        """Starts the imaging sequence, following the define action path."""

        if not self.is_serial_port_connected:
            dispatcher.send('core_error',
                message='The machine needs to be connected before imaging can start.')
            return False

        if self.is_homing:
            dispatcher.send('core_error',
                message='Cannot image while homing the machine.')
            return False

        if self.is_imaging:
            dispatcher.send('core_error',
                message='Imaging already in progress.')
            return False

        if not self.is_machine_idle:
            dispatcher.send('core_error',
                message='The machine needs to be homed before imaging can start.')
            return False

        self._mainqueue = self._actions.copy()
        self.is_imaging = True

        self._clear_to_send = True
        self.imaging_thread = threading.Thread(
            target=self._do_imaging,
            name='imaging thread',
            kwargs={"resuming": True}
        )
        self.imaging_thread.start()
        dispatcher.send('core_message', message='Imaging started')
        return True

    def start_homing(self) -> bool:
        """Start the homing sequence, following the steps in the configuration."""
        if not self.is_serial_port_connected:
            dispatcher.send('core_error',
                message='The machine needs to be connected before homing can start.')
            return False

        if self.is_imaging:
            dispatcher.send('core_error',
                message='Cannot home the machine while imaging.')
            return False

        if self.is_homing:
            dispatcher.send('core_error',
                message='Homing already in progress.')
            return False

        homing_actions = self.config.machine_settings.machine.homing_actions.copy()

        if not homing_actions or len(homing_actions) == 0:
            dispatcher.send('core_error',
                message='No homing sequence to provided.')
            return False

        homing_cmds = []
        # Ensure we are in absolute motion mode.
        device_ids = self._ensure_absolute_move_mode(homing_cmds)

        # Only send homing commands for connected devices.
        homing_actions = filter(lambda c: c.device in device_ids, homing_actions)

        homing_cmds.extend(homing_actions)

        self._mainqueue = homing_cmds
        self.is_homing = True

        self._clear_to_send = True
        self.homing_thread = threading.Thread(
            target=self._do_homing,
            name='homing thread'
        )
        self.homing_thread.start()
        dispatcher.send('core_message', message='Homing started')
        return True

    def set_ready(self):
        """Send the gentries to their ready positions;
        which is the position they are in after homing."""
        cmds = []
        actions = []
        device_ids = self._ensure_absolute_move_mode(cmds)

        for device_id in device_ids:
            cmd_str = ''

            if device_id == 0:
                cmd_str = 'G1X-280Y-364.5Z300P0T0'
            elif device_id == 1:
                cmd_str = f'>{device_id}G1X0Y0Z300P0T0'
            elif device_id == 2:
                cmd_str = f'>{device_id}G1X300Y364.5Z300P0T0'

            actions.append(deserialize_command(cmd_str))

        actions.reverse()
        cmds.extend(actions)

        for cmd in cmds:
            self.send_now(cmd)
            if cmd.atype == ActionType.G90:
                dvc = self._get_device(cmd.device)
                dvc.is_move_absolute = True

    def cancel_imaging(self) -> None:
        """Stops the imaging sequence."""

        self.pause()
        self.is_paused = False
        self._mainqueue = None
        self._clear_to_send = True
        dispatcher.send('core_message', message='Imaging stopped')

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

        self.is_paused = False
        self.is_imaging = True
        self.imaging_thread = threading.Thread(
            target=self._do_imaging,
            name='imaging thread',
            kwargs={"resuming": True}
        )
        self.imaging_thread.start()
        dispatcher.send('core_message', message='Imaging resumed')
        return True

    def send_now(self, command):
        """Send a command to machine ahead of the command queue."""
        # Don't send now if imaging and G or C commands are sent.
        # No jogging while homing or imaging is in process.
        if self.is_machine_busy and command.atype in self._G_COMMANDS + self._C_COMMANDS:
            dispatcher.send('core_error', message='Action commands not allowed when busy.')
            return

        if self.is_serial_port_connected:
            self._sidequeue.put_nowait(command)
        else:
            logging.error("Not connected to device.")

    def _ensure_absolute_move_mode(self, cmd_list):
        device_ids = []

        for dvc in self.devices:
            if not dvc.is_move_absolute:
                cmd_list.append(Action(ActionType.G90, dvc.device_id))

            device_ids.append(dvc.device_id)

        return device_ids

    def _do_imaging(self, resuming=False) -> None:
        self._stop_sender()

        try:
            while self.is_imaging and self.is_serial_port_connected:
                self._send_next()

            self.sentlines = {}
            self.sent = []

        except AttributeError as err:
            logging.error(f"Imaging thread died. {err.args[0]}")

        finally:
            self.imaging_thread = None
            self.is_imaging = False
            dispatcher.send('core_message', message='Imaging ended')

            if len(self.read_threads) > 0:
                self._start_sender()

    def _do_homing(self) -> None:
        self._stop_sender()

        try:
            while self.is_homing and self.is_serial_port_connected:
                self._send_next()

            self.sentlines = {}
            self.sent = []

            for dvc in self.devices:
                resp = dvc.serial_response
                dvc.is_homed = isinstance(resp, SerialResponse) and resp.is_idle

                dvc.is_move_absolute = True

        except AttributeError as err:
            logging.error(f"Homing thread died. {err.args[0]}")

        finally:
            self.homing_thread = None
            self.is_homing = False
            dispatcher.send('core_message', message='Homing ended')

            if len(self.read_threads) > 0:
                self._start_sender()

    def _send_next(self):
        if not self.is_serial_port_connected:
            return

        self._print_debug_msg('Waiting in send next - clear to send> ' +
            f'{self._clear_to_send} - is machine idle> {self.is_machine_idle}')

        # Wait until we get the ok from listener.
        while self.is_serial_port_connected and not self._clear_to_send:
            time.sleep(self._YIELD_TIMEOUT)

        self._print_debug_msg('Done waiting in send next - clear to send> ' +
            f'{self._clear_to_send} - is machine idle> {self.is_machine_idle}')

        if not self._sidequeue.empty():
            self._send(self._sidequeue.get_nowait())
            self._sidequeue.task_done()
            return

        if self.is_machine_busy and self._mainqueue:
            curr = self._mainqueue.pop(0)

            self._print_debug_msg('In send next, sending current - clear to send> ' +
                f'{self._clear_to_send} - is machine idle> {self.is_machine_idle} ' +
                    f'- current> {curr}')

            self._send(curr)
            self._clear_to_send = False

        else:
            self.is_imaging = False
            self.is_homing = False
            self._clear_to_send = True

    def _send(self, command):
        """Send command to machine."""

        if not self.is_serial_port_connected:
            return

        # log sent command
        self.sent.append(command)

        dvc = self._get_device(command.device)
        cmd = serialize_command(command)

        if self._serial.is_port_open:

            self._print_debug_msg('Before write, setting is_writing - clear to send> ' +
                f'{self._clear_to_send} - is machine idle> {self.is_machine_idle} ' +
                    f'Writing> [{cmd}] to device {dvc.device_id}')

            dvc.is_writing = True

            self._print_debug_msg('Before write, is_writing set - clear to send> ' +
                f'{self._clear_to_send} - is machine idle: {self.is_machine_idle}')

            self._serial.write(cmd)

            # Give the controller time to spit out a response.
            time.sleep(self._YIELD_TIMEOUT * 100)
            dvc.is_writing = False

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
        """Remove an action given action list index."""
        action = self._actions.pop(index)
        dispatcher.send('core_a_list_changed')
        return action

    def clear_action(self) -> None:
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
            dispatcher.send('core_error', message=f'invalid device index {index}')

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
        self._edsdk.initialize(ConsoleOutput())

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
        self._serial.initialize(ConsoleOutput(), self._is_dev_env)
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
            dispatcher.send('core_message', message='Unable to select serial port')

        return selected

    def update_serial_ports(self) -> None:
        """Updates the serial ports list."""
        self._serial.update_port_list()

    def _get_active_serial_port_name(self):
        port = next(
                filter(lambda p: p.is_active, self.serial_port_list), None
            )
        return port.name if port else None

    def _print_debug_msg(self, msg):
        if self._is_dev_env:
            print_timestamped(msg)


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


class ConsoleOutput:
    """Implement console output operations."""

    def __init__(self):
        return

    def print(self, msg: str) -> None:
        """Dispatch a message to the console."""
        dispatcher.send('core_message', message=msg)
