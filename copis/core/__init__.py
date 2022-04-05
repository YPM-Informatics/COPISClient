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

"""COPIS Application Core functions."""

__version__ = ""

# pylint: disable=using-constant-test
import sys
from typing import List, Tuple

if sys.version_info.major < 3:
    print("You need to run this on Python 3")
    sys.exit(-1)

# pylint: disable=wrong-import-position
import threading
import time
import warnings

from itertools import zip_longest
from glm import vec2, vec3
from pydispatch import dispatcher

from copis.command_processor import serialize_command
from copis.helpers import (point5_to_dict, get_timestamp, print_error_msg, print_debug_msg,
    print_info_msg)
from copis.globals import ActionType, ComStatus, DebugEnv, WorkType
from copis.config import Config
from copis.project import Project
from copis.classes import MonitoredList
from copis.store import load_json_2, save_json_2

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
    """COPISCore. Connects and interacts with devices in system."""

    _YIELD_TIMEOUT = .001 # 1 millisecond

    def __init__(self, parent=None) -> None:
        """Initializes a COPISCore instance."""
        self.config = parent.config if parent else Config(vec2(800, 600))

        self.project = Project()
        self.project.start()

        self._evf_thread = None

        self.console = ConsoleOutput(parent)

        self._is_dev_env = self.config.application_settings.debug_env == DebugEnv.DEV
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
        self._work_type = None

        self._read_threads = []
        self._working_thread = None

        self._mainqueue = []
        self._pose_set_offset_start: int = -1
        self._pose_set_offset_end: int = -1
        self._current_mainqueue_item: int = -1
        self._imaged_pose_sets: List[int] = MonitoredList('ntf_i_list_changed', [])
        self._selected_pose: int = -1
        self._selected_pose_set: int = -1
        self._selected_proxy: int = -1
        self._selected_device: int = -1

        self._imaging_target: vec3 = vec3()
        self._imaging_session_path = None
        self._imaging_session_queue = None
        self._save_imaging_session = False



    @property
    def imaged_pose_sets(self):
        """Returns a list of pose set indexes that have been imaged
            in the current run."""
        return self._imaged_pose_sets

    @property
    def work_type_name(self):
        """Returns the name of the work in progress."""
        return self._work_type.name.lower().capitalize().replace('_', ' ') \
            if self._work_type else ''

    @property
    def is_dev_env(self):
        """Returns a flag indicating whether we are in a dev environment."""
        return self._is_dev_env

    def _check_configs(self) -> None:
        warn = self._is_dev_env
        msg = None
        machine_config = self.config.machine_settings

        if machine_config is None:
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

            packet_size = len(packet)
            if isinstance(packet, tuple) and list(map(type, packet)) == [int, list]:
                packet_size = len(packet[1])
            print_debug_msg(self.console, f'Packet size is: {packet_size}',
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
        current_pose_set = -1

        if isinstance(commands, tuple) and \
            list(map(type, commands)) == [int, list]:
            current_pose_set = commands[0]
            commands = commands[1]

        for command in commands:
            if not any(d.device_id == command.device for d in dvcs):
                dvcs.append(self._get_device(command.device))

            cmds.append(serialize_command(command))

        cmd_lines = '\r'.join(cmds)

        if self._serial.is_port_open:
            img_start_time = get_timestamp(True)

            if cmd_lines:
                print_debug_msg(self.console, 'Writing> [{0}] to device{1} '
                        .format(cmd_lines.replace("\r", "\\r"), "s" if len(dvcs) > 1 else "") +
                    f'{", ".join([str(d.device_id) for d in dvcs])}.', self._is_dev_env)

                for dvc in dvcs:
                    dvc.set_is_writing()

                if self._save_imaging_session:
                    for command in commands:
                        if command.atype == ActionType.C0:
                            device = self._get_device(command.device)
                            file_name = \
                                f'IMG_C_{command.device}_{current_pose_set + 1}.json'

                            data = {}
                            data['position'] = point5_to_dict(device.position)
                            data['start time'] = img_start_time

                            save_json_2(self._imaging_session_path, file_name, data)
                            self._imaging_session_queue.append((command.device, file_name))

                self._serial.write(cmd_lines)
            else:
                print_debug_msg(self.console, 'Not writing empty packet.', self._is_dev_env)

            if self._work_type == WorkType.IMAGING:
                if self._pose_set_offset_start <= self._current_mainqueue_item and \
                    self._current_mainqueue_item <= self._pose_set_offset_end:
                    previous_pose_set = current_pose_set - 1

                    if previous_pose_set > -1:
                        self._imaged_pose_sets.append(previous_pose_set)

                    self.select_pose_set(current_pose_set)
                else:
                    if self._current_mainqueue_item == self._pose_set_offset_end + 1:
                        self._imaged_pose_sets.append(current_pose_set)

                    self.select_pose_set(-1)

                self._current_mainqueue_item = self._current_mainqueue_item + 1

    def _update_recent_projects(self, path) -> None:
        recent_projects = list(map(str.lower,
            self.config.application_settings.recent_projects))

        if path.lower() not in recent_projects:
            self.config.update_recent_projects(path)

    def _on_device_updated(self, device):
        if len(self._imaging_session_queue) and not device.is_writing and \
            device.serial_status == ComStatus.IDLE and \
            device.device_id == self._imaging_session_queue[0][0]:
            _, file_name = self._imaging_session_queue.pop(0)

            data = load_json_2(self._imaging_session_path, file_name)
            data['end time'] = get_timestamp(True)

            save_json_2(self._imaging_session_path, file_name, data)
            printed = 'test'

    def start_new_project(self) -> None:
        """Starts a new project with defaults."""
        self.select_pose(-1)
        self.select_device(-1)
        self.select_proxy(-1)
        self._pose_set_offset_start = -1
        self._pose_set_offset_end = -1
        self._current_mainqueue_item = -1
        self.select_pose_set(-1)
        self._imaged_pose_sets.clear()

        last_dvc_statuses = [(d.device_id, d.is_homed, d.serial_response)
            for d in self.project.devices]

        self.project.start()

        self._reconcile_machine(last_dvc_statuses)

    def open_project(self, path) -> Tuple:
        """Opens an existing project."""
        self.select_pose(-1)
        self.select_device(-1)
        self.select_proxy(-1)
        self._pose_set_offset_start = -1
        self._pose_set_offset_end = -1
        self._current_mainqueue_item = -1
        self.select_pose_set(-1)
        self._imaged_pose_sets.clear()

        last_dvc_statuses = [(d.device_id, d.is_homed, d.serial_response)
            for d in self.project.devices]

        resp = self.project.open(path)
        did_open, _ = resp

        if did_open:
            self._update_recent_projects(path)

        self._reconcile_machine(last_dvc_statuses)
        return resp

    def save_project(self, path) -> None:
        """Saves a project and update recent projects."""
        self.project.save(path)

        self._update_recent_projects(path)

    def start_imaging(self, save_path, keep_last_path) -> bool:
        """Starts the imaging sequence, following the define action path."""
        def imaging_callback():
            if self._save_imaging_session:
                dispatcher.disconnect(self._on_device_updated, signal='ntf_device_updated')
                self._save_imaging_session = False

        def process_pose_sets():
            packets = []

            for i, p_set in enumerate(self.project.pose_sets):
                zipped = [(i, [val for val in tup if val is not None]) for tup in
                    zip_longest(*[p.get_seq_actions() for p in p_set])]
                packets.extend(zipped)

            return packets

        if not self.is_serial_port_connected:
            print_error_msg(self.console,
                'The machine needs to be connected before imaging can start.')
            return False

        if self._is_machine_busy:
            print_error_msg(self.console, 'Cannot image. The machine is busy.')
            return False

        if not self.is_machine_idle:
            print_error_msg(self.console, 'The machine needs to be homed before imaging can start.')
            return False

        if keep_last_path:
            self._save_imaging_session = False
        else:
            self._imaging_session_path = save_path
            self._save_imaging_session = bool(self._imaging_session_path)

        if self._save_imaging_session:
            self._imaging_session_queue = []
            dispatcher.connect(self._on_device_updated, signal='ntf_device_updated')

        header = self._get_move_commands(True, *[dvc.device_id for dvc in self.project.devices])
        body = process_pose_sets()
        footer = self._get_initialization_commands(ActionType.G1)
        footer.extend(self._disengage_motors_commands)

        self._mainqueue = []
        self._mainqueue.extend(header)
        self._mainqueue.extend(body)
        self._mainqueue.extend(footer)
        self._pose_set_offset_start = len(header)
        self._pose_set_offset_end = self._pose_set_offset_start + len(body) - 1
        self._current_mainqueue_item = 0
        self._work_type = WorkType.IMAGING

        self._keep_working = True
        self._clear_to_send = True
        self._working_thread = threading.Thread(
            target=self._worker,
            name='working thread',
            kwargs={
                "extra_callback": imaging_callback
            }
        )
        self._working_thread.start()
        return True

    def start_homing(self) -> bool:
        """Start the homing sequence, following the steps in the configuration."""
        def homing_callback():
            for dvc in self.project.devices:
                dvc.set_is_homed()

        if not self.is_serial_port_connected:
            print_error_msg(self.console,
                'The machine needs to be connected before homing can start.')
            return False

        if self._is_machine_busy:
            print_error_msg(self.console, 'Cannot home. The machine is busy.')
            return False

        homing_actions = self.project.homing_actions

        if not homing_actions or len(homing_actions) == 0:
            print_error_msg(self.console, 'No homing sequence to provided.')
            return False

        # Only send homing commands for connected devices.
        all_device_ids = [d.device_id for d in self.project.devices]
        homing_actions = list(filter(lambda c: c.device in all_device_ids, homing_actions))

        device_ids = list(set(a.device for a in homing_actions))
        batch_size = len(device_ids)

        header = self._get_move_commands(True, *device_ids)
        body = _chunk_actions(batch_size, homing_actions)
        footer = self._get_initialization_commands(ActionType.G1)
        footer.extend(self._disengage_motors_commands)

        self._mainqueue = []
        self._mainqueue.extend(header)
        self._mainqueue.extend(body)
        self._mainqueue.extend(footer)
        self._work_type = WorkType.HOMING

        self._keep_working = True
        self._clear_to_send = True
        self._working_thread = threading.Thread(
            target=self._worker,
            name='working thread',
            kwargs={
                "extra_callback": homing_callback
            }
        )
        self._working_thread.start()
        return True

    def stop_work(self) -> None:
        """Stops work in progress."""

        if self.pause_work():
            self._mainqueue = []
            self._is_machine_paused = False
            self._clear_to_send = True
            self._pose_set_offset_start = -1
            self._pose_set_offset_end = -1
            self._current_mainqueue_item = -1
            self.select_pose_set(-1)
            self._imaged_pose_sets.clear()
            self._work_type = None

            print_info_msg(self.console, f'{self.work_type_name} stopped')

    def pause_work(self) -> bool:
        """Pause work in progress, saving the current position."""

        if not self._working_thread:
            print_error_msg(self.console, 'Cannot pause. The machine is not busy.')
            return False

        self._is_machine_paused = True
        self._keep_working = False

        # try joining the print thread: enclose it in try/except because we
        # might be calling it from the thread itself
        try:
            self._working_thread.join()
            self._working_thread = None
            print_info_msg(self.console, f'{self.work_type_name} paused.')
            return True
        except RuntimeError as err:
            print_error_msg(self.console, f'Cannot join working thread: {err.args[0]}')
            return False

    def resume_work(self) -> bool:
        """Resume the current run."""

        if not self._is_machine_paused:
            print_error_msg(self.console, 'Cannot resume; machine is not paused.')
            return False

        self._is_machine_paused = False
        self._keep_working = True
        self._clear_to_send = True
        self._working_thread = threading.Thread(
            target=self._worker,
            name='working thread',
            kwargs={
                "resume": True
            }
        )
        self._working_thread.start()
        return True


def _chunk_actions(batch_size, actions):
    chunks = []

    for i in range(0, len(actions), batch_size):
        chunk = actions[i:i + batch_size]
        chunks.append(chunk)

    return chunks
