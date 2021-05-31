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

import sys

if sys.version_info.major < 3:
    print("You need to run this on Python 3")
    sys.exit(-1)

# pylint: disable=wrong-import-position
import logging
import threading
import time
import warnings

from importlib import import_module
from functools import wraps
from queue import Empty as QueueEmpty
from queue import Queue
from typing import List, Optional, Tuple
from glm import vec3

from pydispatch import dispatcher

import copis.coms.serial_controller as serial_controller

from .enums import ActionType, DebugEnv
from .helpers import Point5
from .classes import (
    Action, Device, MonitoredList, Object3D, CylinderObject3D, AABBObject3D,
    OBJObject3D)

MAX_ID = 16777214


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

    def __init__(self, parent) -> None:
        """Initialize a CopisCore instance."""
        self.config = parent.config

        self._is_edsdk_enabled = False
        self._edsdk = None
        self.evf_thread = None

        self._is_serial_enabled = False
        self._serial = None

        self.init_edsdk()
        self.init_serial()

        self._check_configs()

        # serial instance connected to the machine, None when disconnected
        self._machine = None
        # clear to send, enabled after responses
        self._clear = False
        # printer responded to initial command and is active
        self._online = False
        # True if sending actions, false if paused
        self.imaging = False
        self.paused = False

        # logging
        self.sentlines = {}
        self.sent = []

        self.read_thread = None
        self.stop_read_thread = False
        self.send_thread = None
        self.stop_send_thread = False
        self.imaging_thread = None

        self._mainqueue = None
        self._sidequeue = Queue(0)

        # TODO: this might not exist after testing machine.
        # self.offset_devices(*self.config.machine_settings.devices)

        self._actions: List[Action] = MonitoredList('core_a_list_changed')
        self._devices: List[Device] = MonitoredList('core_d_list_changed',
            iterable=self.config.machine_settings.devices)

        self._objects: List[Object3D] = MonitoredList('core_o_list_changed',
            iterable=[
                AABBObject3D(vec3(-130, -120, -20), vec3(-50, -60, 50)),
                OBJObject3D('model/handsome_dan.obj', scale=vec3(20, 20, 20)),
                CylinderObject3D(vec3(100, 100, 0), vec3(100, -50, 0), 35),
            ])

        self._selected_points: List[int] = []
        self._selected_device: int = -1

    def _check_configs(self) -> None:
        warn = self.config.settings.debug_env == DebugEnv.DEV.value
        msg = None
        machine_config = self.config.machine_settings

        if len(machine_config.chambers) == 0:
            msg = 'No chambers configured.'
        elif len(machine_config.chambers) > 2:
            msg = '2 chambers maximum exceeded.'
        # TODO:
        # - Check 3 cameras per chamber max.
        # - Check all cameras assigned to a chamber.
        # - Check cameras within chamber bounds.

        if msg is not None:
            warning = UserWarning(msg)
            if warn:
                warnings.warn(warning)
            else:
                raise warning

    # TODO: this might not exist after testing machine.
    # def offset_devices(self, *devices) -> None:
    #     """Take a list of devices and applies the chamber offsets to their coordinates."""

    #     for device in devices:
    #         chamber = next(filter(lambda c, d = device : c.name == d.chamber_name,
    #         self.config.machine_settings.chambers))

    #         new_position = Point5(
    #             device.position.x + chamber.offsets.x,
    #             device.position.y + chamber.offsets.y,
    #             device.position.z + chamber.offsets.z,
    #             device.position.p, device.position.t)

    #         device.position = new_position

    @locked
    def disconnect(self):
        """TODO: implement camera disconnect."""
        if self._machine:
            if self.read_thread:
                self.stop_read_thread = True
                if threading.current_thread() != self.read_thread:
                    self.read_thread.join()
                self.read_thread = None
            if self.imaging_thread:
                self.imaging = False
                self.imaging_thread.join()
            self._stop_sender()

        self._machine = None
        self._online = False
        self.imaging = False

        dispatcher.send('core_message', message='Disconnected from device')

    @locked
    def connect(self):
        """TODO: implement serial connection."""
        self.stop_read_thread = False
        self.read_thread = threading.Thread(
            target=self._listen,
            name='read thread')
        self.read_thread.start()
        self._start_sender()

        dispatcher.send('core_message', message='Connected to device')

    def reset(self) -> None:
        """Reset the machine."""
        return

    def _listen_can_continue(self):
        return not self.stop_read_thread

    def _listen(self) -> None:
        while self._listen_can_continue():
            time.sleep(0.001)
            if not self.edsdk.is_waiting_for_image:
                self._clear = True

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

            while self._machine and self.imaging and not self._clear:
                time.sleep(0.001)

            self._send(command)

            while self._machine and self.imaging and not self._clear:
                time.sleep(0.001)

    def start_imaging(self, startindex=0) -> bool:
        """TODO"""

        ##### Workaround because we don't have serial implemented yet
        self._machine = True
        self._online = True
        #####

        if self.imaging or not self._online or not self._machine:
            return False

        # TODO: setup machine before starting

        self._mainqueue = self._actions.copy()
        self.imaging = True

        self._clear = False
        self.imaging_thread = threading.Thread(
            target=self._image,
            name='imaging thread',
            kwargs={"resuming": True}
        )
        self.imaging_thread.start()
        dispatcher.send('core_message', message='Imaging started')
        return True

    def cancel_imaging(self) -> None:
        """TODO"""

        self.pause()
        self.paused = False
        self._mainqueue = None
        self._clear = True
        dispatcher.send('core_message', message='Imaging stopped')

    def pause(self) -> bool:
        """Pause the current run, saving the current position."""

        if not self.imaging:
            return False

        self.paused = True
        self.imaging = False

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

        if not self.paused:
            return False

        # send commands to resume printing

        self.paused = False
        self.imaging = True
        self.imaging_thread = threading.Thread(
            target=self._image,
            name='imaging thread',
            kwargs={"resuming": True}
        )
        self.imaging_thread.start()
        dispatcher.send('core_message', message='Imaging resumed')
        return True

    def send_now(self, command):
        """Send a command to machine ahead of the command queue."""
        if self._online:
            self._sidequeue.put_nowait(command)
        else:
            logging.error("Not connected to device.")

    def _image(self, resuming=False) -> None:
        """TODO"""
        self._stop_sender()

        try:
            while self.imaging and self._machine and self._online:
                self._send_next()

            self.sentlines = {}
            self.sent = []

        except:
            logging.error("Print thread died")

        finally:
            self.imaging_thread = None
            self._start_sender()

    def _send_next(self):
        if not self._machine:
            return

        # wait until we get the ok from listener
        while self._machine and self.imaging and not self._clear:
            time.sleep(0.001)

        if not self._sidequeue.empty():
            self._send(self._sidequeue.get_nowait())
            self._sidequeue.task_done()
            return

        if self.imaging and self._mainqueue:
            curr = self._mainqueue.pop(0)
            self._send(curr)
            self._clear = False

        else:
            self.imaging = False
            self._clear = True

    def _send(self, command):
        """Send command to machine."""

        if not self._machine:
            return

        # log sent command
        self.sent.append(command)

        # debug command
        logging.debug(command)

        if command.atype in (
            ActionType.G0, ActionType.G1, ActionType.G2, ActionType.G3,
            ActionType.G4, ActionType.G17, ActionType.G18, ActionType.G19,
            ActionType.G90, ActionType.G91, ActionType.G92):

            # try writing to printer
            # ser.write(command.encode())
            pass

        elif command.atype == ActionType.C0:
            if self.edsdk.connect(command.device):
                self.edsdk.take_picture()

        elif command.atype == ActionType.C1:
            pass

        elif command.atype == ActionType.M24:
            pass

        elif command.atype == ActionType.M17:
            pass

        elif command.atype == ActionType.M18:
            pass

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

    def update_selected_points(self, argc, args) -> None:
        """Update position of points in selected points list."""
        for id_ in self.selected_points:
            self.actions[id_].argc = argc
            self.actions[id_].args = args

        dispatcher.send('core_a_list_changed')

    def export_actions(self, filename: str = None) -> list:
        """Serialize action list and write to file.

        TODO: Expand to include not just G0 and C0 actions
        """

        get_g_code = lambda input: str(input).split('.')[1]
        lines = []

        for action in self._actions:
            g_code = get_g_code(action.atype)
            dest = '' if action.device == 0 else f'>{action.device}'
            line = f'{dest}{g_code}'
            g_cmd = ''

            if g_code[0] == 'G':
                pos = [f'{c:.3f}' for c in action.args]
                g_cmd = f'X{pos[0]}Y{pos[0]}Z{pos[0]}P{pos[0]}T{pos[0]}'
            elif g_code[0] == 'C':
                g_cmd = 'P500'

            line += g_cmd
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
        """Initialize Canon EDSDK connection."""
        if self._is_edsdk_enabled:
            return

        self._edsdk = import_module('copis.coms.edsdk_controller')
        self._edsdk.initialize(ConsoleOutput())

        self._is_edsdk_enabled = self._edsdk.is_enabled

    def terminate_edsdk(self):
        """Terminate Canon EDSDK connection."""
        if self._is_edsdk_enabled:
            self._edsdk.terminate()

    # --------------------------------------------------------------------------
    # Serial methods
    # --------------------------------------------------------------------------

    def init_serial(self) -> None:
        """Initialize serial connection."""
        if self._is_serial_enabled:
            return
        is_dev_env = self.config.settings.debug_env == DebugEnv.DEV.value
        self._serial = serial_controller
        self._serial.initialize(ConsoleOutput(), is_dev_env)
        self._is_serial_enabled = True

    def terminate_serial(self):
        """Terminate serial connection."""
        if self._is_serial_enabled:
            self._serial.terminate()

    @property
    def edsdk(self):
        """Get EDSDK."""
        return self._edsdk

    @property
    def serial(self):
        """Get serial."""
        return self._serial


class ConsoleOutput:
    """Implement console output operations."""

    def __init__(self):
        return

    def print(self, msg: str) -> None:
        """Dispatch a message to the console."""
        dispatcher.send('core_message', message=msg)
