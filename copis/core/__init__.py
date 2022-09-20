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

from itertools import groupby, zip_longest
from glm import vec2, vec3
from pydispatch import dispatcher

from copis.command_processor import serialize_command
from copis.helpers import (get_atype_kind, point5_to_dict, get_timestamp, print_error_msg,
    print_debug_msg, print_info_msg)
from copis.globals import ActionType, ComStatus, DebugEnv, WorkType
from copis.config import Config
from copis.project import Project
from copis.classes import MonitoredList
from copis.store import load_json_2, path_exists_2, save_json_2
from .__version__ import __version__

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
    _IMAGING_MANIFEST_FILE_NAME = 'copis_imaging_manifest.json'

    def __init__(self, parent=None) -> None:
        """Initializes a COPISCore instance."""
        self.config = parent.config if parent else Config(vec2(800, 600))

        self.project = Project()
        self.project.start()

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

        # Clear to send, enabled after responses.
        self._clear_to_send = False

        # True if sending actions, false if paused.
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
        self._imaging_session_manifest = None
        self._initialized_manifests = []
        self._save_imaging_session = False
        self._image_counters = {}

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

    def _get_next_img_rank(self, device_id):
        counter = 1

        if device_id in self._image_counters:
            counter = self._image_counters[device_id] + counter

        self._image_counters[device_id] = counter

        return counter

    def _get_image_counts(self, pose_list=None):
        c_key = lambda p: (p.position or p.payload[0]).device

        counts = {}
        poses = sorted(pose_list or self.project.poses, key=c_key)
        groups = groupby(poses, c_key)

        for key, group in groups:
            pics = [a for p in list(group) for a in p.get_actions()
                if a.atype in self.SNAP_COMMANDS]
            device = self._get_device(key)
            device_key = f'{device.name}_{device.type}_id_{device.device_id}'.lower()
            counts[device_key] = len(pics)

        return ('expected_image_counts', counts)

    def _update_imaging_manifest(self, pairs):
        if not path_exists_2(self._imaging_session_path, self._IMAGING_MANIFEST_FILE_NAME):
            manifest = self._imaging_session_manifest.pop(-1)
            self._imaging_session_manifest.clear()
            self._imaging_session_manifest.append(manifest)

        for key, value in pairs:
            self._imaging_session_manifest[-1][key] = value

        if pairs:
            save_json_2(self._imaging_session_path,
                self._IMAGING_MANIFEST_FILE_NAME,
                self._imaging_session_manifest)

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

    def _process_host_commands(self, commands):
        for cmd in commands:
            dvc = self._get_device(cmd.device)

            while dvc.status not in [ComStatus.IDLE, ComStatus.UNKNOWN]:
                time.sleep(self._YIELD_TIMEOUT)

            key, value = cmd.args[0]
            value = float(value)
            atype_kind = get_atype_kind(cmd.atype)

            if atype_kind == 'EDS':
                if self.connect_edsdk(dvc.device_id):
                    dvc.is_writing_eds = True

                    if cmd.atype == ActionType.EDS_SNAP:
                        do_af = bool(value) if key == 'V' else False
                        self._edsdk.take_picture(do_af)
                    elif cmd.atype == ActionType.EDS_FOCUS:
                        shutter_release_time = value if key == 'S' else 0
                        self._edsdk.focus(shutter_release_time)
                    else:
                        print_error_msg(self.console,
                            f"Host command '{cmd.atype.name}' not yet handled.")

                    dvc.is_writing_eds = False
                else:
                    print_error_msg(self.console,
                        f'Unable to connect to camera {dvc.device_id}.')
            else:
                print_error_msg(self.console,
                    f"Action type king '{atype_kind}' not yet handled.")

    def _send_next(self):
        if not (self.is_serial_port_connected or self._is_edsdk_enabled):
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

            if packet:
                self._send(*packet)
                self._clear_to_send = False
            else:
                print_debug_msg(self.console, 'Not writing empty packet.', self._is_dev_env)

        else:
            self._keep_working = False
            self._clear_to_send = True

    def _send(self, *commands):
        """Send command to machine."""

        img_start_time = get_timestamp(True)
        current_pose_set = -1

        if isinstance(commands, tuple) and \
            list(map(type, commands)) == [int, list]:
            current_pose_set = commands[0]
            commands = commands[1]

        is_serial_needed = any(get_atype_kind(c.atype) == 'SER' for c in commands)
        is_serial_checked = not is_serial_needed or self.is_serial_port_connected

        is_edsdk_needed = any(get_atype_kind(c.atype) == 'EDS' for c in commands)
        is_edsdk_checked = not is_edsdk_needed or self._is_edsdk_enabled

        are_requirements_met = is_serial_checked and is_edsdk_checked

        if not are_requirements_met:
            return

        dvcs = []
        cmds = []
        chunks = []

        for command in commands:
            if not any(d.device_id == command.device for d in dvcs):
                dvcs.append(self._get_device(command.device))

            if chunks and \
                any(get_atype_kind(c.atype) != get_atype_kind(command.atype) for c in chunks):
                cmds.append(chunks)
                chunks = []
                chunks.append(command)
            else:
                chunks.append(command)

        if chunks:
            cmds.append(chunks)

        cmd_lines = '\r'.join([serialize_command(i) for c in cmds for i in c])

        if cmd_lines:
            print_debug_msg(self.console, 'Writing> [{0}] to device{1} '
                    .format(cmd_lines.replace("\r", "\\r"), "s" if len(dvcs) > 1 else "") +
                f'{", ".join([str(d.device_id) for d in dvcs])}.', self._is_dev_env)

            if self._save_imaging_session:
                for command in commands:
                    if command.atype in self.SNAP_COMMANDS:
                        device = self._get_device(command.device)
                        rank = self._get_next_img_rank(command.device)
                        method = \
                            'remote shutter' if get_atype_kind(command.atype) == 'SER' else 'EDSDK'
                        file_name = \
                            f'cam_{command.device}_img_{rank}.json'

                        data = {}
                        data['file_name'] = file_name
                        data['device_type'] = device.type
                        data['device_name'] = device.name
                        data['device_id'] = device.device_id
                        data['imaging_method'] = method
                        data['position'] = point5_to_dict(
                            device.position) if device.is_homed else None
                        data['stack_id'] = None
                        data['stack_index'] = None
                        data['image_start_time'] = img_start_time

                        session_images = self._imaging_session_manifest[-1]['images']
                        image_index = len(session_images)

                        session_images.append(data)
                        self._update_imaging_manifest([('images', session_images)])
                        self._imaging_session_queue.append((command.device, method, image_index))

            if not is_edsdk_needed:
                for dvc in dvcs:
                    dvc.set_is_writing_ser()

                self._serial.write(cmd_lines)
            else:
                serial_cmds = []
                host_cmds = []
                check_chunk_kind = \
                    lambda items, kind: all(get_atype_kind(i.atype) == kind for i in items)

                while cmds:
                    chunk = cmds.pop(0)
                    if chunk:
                        if check_chunk_kind(chunk, 'SER'):
                            if host_cmds:
                                self._process_host_commands(host_cmds)
                                host_cmds = []
                            serial_cmds.extend(chunk)
                        elif check_chunk_kind(chunk, 'EDS'):
                            if serial_cmds:
                                for dvc in dvcs:
                                    if dvc.device_id in [c.device for c in serial_cmds]:
                                        dvc.set_is_writing_ser()

                                self._serial.write(
                                    '\r'.join([serialize_command(c) for c in serial_cmds]))
                                serial_cmds = []

                            host_cmds.extend(chunk)

                if serial_cmds:
                    self._serial.write(
                        '\r'.join([serialize_command(c) for c in serial_cmds]))
                if host_cmds:
                    self._process_host_commands(host_cmds)

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

    def _on_device_ser_updated(self, device):
        if device.serial_status == ComStatus.IDLE and len(self._imaging_session_queue):
            dvc_id, img_method, img_index = [None] * 3
            for i, data in enumerate(self._imaging_session_queue):
                if data[0] == device.device_id:
                    dvc_id, img_method, img_index = self._imaging_session_queue.pop(i)
                    break

            if dvc_id is not None:
                if img_method == 'remote shutter':
                    session_images = self._imaging_session_manifest[-1]['images']
                    session_images[img_index]['image_end_time'] = get_timestamp(True)

                    self._update_imaging_manifest([('images', session_images)])
                elif img_method == 'EDSDK':
                    # This should never be reached lest we have a bug.
                    print_error_msg(self.console,
                        f'Expected remote shutter imaging method for device {device.device_id} ' +
                        f'but found {img_method} instead.')
            else:
                # This should never be reached lest we have a bug.
                print_error_msg(self.console,
                    f'Could not find update data for camera {device.device_id}.')

    def _on_device_eds_updated(self, device):
        if not device.is_writing_eds and len(self._imaging_session_queue):
            dvc_id, img_method, img_index = [None] * 3
            for i, data in enumerate(self._imaging_session_queue):
                if data[0] == device.device_id:
                    dvc_id, img_method, img_index = self._imaging_session_queue.pop(i)
                    break

            if dvc_id is not None:
                if img_method == 'EDSDK':
                    session_images = self._imaging_session_manifest[-1]['images']
                    session_images[img_index]['image_end_time'] = get_timestamp(True)

                    self._update_imaging_manifest([('images', session_images)])
                elif img_method == 'remote shutter':
                    # This should never be reached lest we have a bug.
                    print_error_msg(self.console,
                        f'Expected EDSDK imaging method for device {device.device_id} ' +
                        f'but found {img_method} instead.')
            else:
                # This should never be reached lest we have a bug.
                print_error_msg(self.console,
                    f'Could not find update data for camera {device.device_id}.')

    def _add_manifest_section(self):
        def is_manifest_initialized(key):
            return self._initialized_manifests and key in self._initialized_manifests

        manifest_key = hash('|'.join(
            [self._imaging_session_path, self._IMAGING_MANIFEST_FILE_NAME]).lower())

        if not is_manifest_initialized(manifest_key):
            self._imaging_session_manifest = []

            if path_exists_2(self._imaging_session_path, self._IMAGING_MANIFEST_FILE_NAME):
                self._imaging_session_manifest.extend(
                    load_json_2(self._imaging_session_path, self._IMAGING_MANIFEST_FILE_NAME))

            self._initialized_manifests.append(manifest_key)

        self._imaging_session_manifest.append({})

    def _imaging_callback(self):
        if self._save_imaging_session:
            self._update_imaging_manifest(
                [('imaging_end_time', get_timestamp(True))])

            dispatcher.disconnect(
                self._on_device_ser_updated, signal='ntf_device_ser_updated')
            dispatcher.disconnect(
                self._on_device_eds_updated, signal='ntf_device_eds_updated')
            self._save_imaging_session = False

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

        self._update_recent_projects(path)
        self._reconcile_machine(last_dvc_statuses)

        return resp

    def save_project(self, path) -> None:
        """Saves a project and update recent projects."""
        self.project.save(path)

        self._update_recent_projects(path)

    def start_imaging(self, save_path, keep_last_path) -> bool:
        """Starts the imaging sequence, following the defined action path."""
        def process_pose_sets():
            packets = []

            for i, p_set in enumerate(self.project.pose_sets):
                zipped = [(i, [val for val in tup if val is not None]) for tup in
                    zip_longest(*[p.get_seq_actions() for p in p_set])]
                packets.extend(zipped)

            return packets

        if self._is_machine_paused:
            return self.resume_work()

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
            self._add_manifest_section()

            pairs = [('imaging_start_time', get_timestamp(True)),
                ('imaging_end_time', None)]
            pairs.append(self._get_image_counts())
            pairs.append(('images', []))

            self._update_imaging_manifest(pairs)

            dispatcher.connect(self._on_device_ser_updated, signal='ntf_device_ser_updated')
            dispatcher.connect(self._on_device_eds_updated, signal='ntf_device_eds_updated')

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
                "extra_callback": self._imaging_callback
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

        paused = self._is_machine_paused

        if paused or self.pause_work():
            self._mainqueue = []
            self._is_machine_paused = False
            self._clear_to_send = True
            self._pose_set_offset_start = -1
            self._pose_set_offset_end = -1
            self._current_mainqueue_item = -1
            self.select_pose_set(-1)
            self._imaged_pose_sets.clear()

            work_type_name = self.work_type_name
            self._work_type = None

            if paused:
                self._query_machine()

            print_info_msg(self.console, f'{work_type_name} stopped')

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
            print_info_msg(self.console, f'{self.work_type_name} paused')
            return True
        except RuntimeError as err:
            print_error_msg(self.console, f'Cannot join working thread: {err.args[0]}')
            return False

    def resume_work(self) -> bool:
        """Resume the current run."""

        if not self._is_machine_paused:
            print_error_msg(self.console, 'Cannot resume; machine is not paused.')
            return False

        kwargs = {
            "resuming": True
        }

        if self._work_type == WorkType.IMAGING:
            kwargs['extra_callback'] = self._imaging_callback

        self._is_machine_paused = False
        self._keep_working = True
        self._clear_to_send = True
        self._working_thread = threading.Thread(
            target=self._worker,
            name='working thread',
            kwargs=kwargs
        )

        self._working_thread.start()
        return True


def _chunk_actions(batch_size, actions):
    chunks = []

    for i in range(0, len(actions), batch_size):
        chunk = actions[i:i + batch_size]
        chunks.append(chunk)

    return chunks
