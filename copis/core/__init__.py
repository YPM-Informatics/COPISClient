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

import sys

# pylint: disable=wrong-import-position
if sys.version_info.major < 3:
    print("You need to run this on Python 3")
    sys.exit(-1)

import time
import threading
import warnings
import uuid

from random import shuffle as rand_shuffle
from typing import List, Tuple
from datetime import datetime
from itertools import groupby, zip_longest
from glm import vec2, vec3
from pydispatch import dispatcher

from copis.command_processor import serialize_command
from copis.helpers import get_atype_kind, print_error_msg, print_debug_msg, print_info_msg, create_action_args, get_action_args_values, get_end_position, get_heading, sanitize_number
from copis.globals import ActionType, ComStatus, DebugEnv, Point5, WorkType
from copis.config import Config
from copis.project import Project
from copis.classes import Action, MonitoredList, SerialResponse
from copis import store
from copis.classes.sys_db import SysDB
from copis.mathutils import optimize_rotation_move_to_angle

from ._console_output import ConsoleOutput
from ._machine_members import MachineMembersMixin
from ._communication_members import CommunicationMembersMixin


class COPISCore(
    MachineMembersMixin,
    CommunicationMembersMixin):
    """COPISCore. Connects and interacts with devices in system."""

    _YIELD_TIMEOUT = .001 # 1 millisecond
    _IMAGING_MANIFEST_FILE_NAME = 'copis_imaging_manifest.json'
    MOVE_COMMANDS = [ActionType.G0, ActionType.G1]
    F_STACK_COMMANDS = [ActionType.HST_F_STACK, ActionType.EDS_F_STACK]
    SNAP_COMMANDS = [ActionType.C0, ActionType.EDS_SNAP]
    FOCUS_COMMANDS = [ActionType.C1, ActionType.EDS_FOCUS]
    LENS_COMMANDS = SNAP_COMMANDS + FOCUS_COMMANDS

    def __init__(self, parent=None) -> None:
        """Initializes a COPISCore instance."""
        self.config = parent.config if parent else Config(vec2(800, 600))
        print ("using config:", store.get_ini_path())
        print ("using profile: ", store.get_profile_path())

        self.sys_db = SysDB()
        self._session_id = self.sys_db.last_session_id() +1
        self._session_guid = str(uuid.uuid4()) # Global session if, useful is merging dbs.

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
        self._serial._instance.attach_sys_db(self.sys_db)
        self._edsdk._instance.attach_sys_db(self.sys_db)
        #attach serial
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

        self._ressetable_send_delay_ms = 0 #delay time in milliseconds before sending a serial command after recieiving idle/CTS

    @property
    def save_imaging_session(self) -> str:
        """Returns a flag indicating whether to save the imaging session."""
        return self._save_imaging_session

    @property
    def imaging_session_path(self) -> str:
        """Returns the user-defined imaging session folder location."""
        return self._imaging_session_path

    @property
    def imaging_target(self) -> vec3:
        """Returns the coordinates of the last target; (0,0,0) if application just started."""
        return self._imaging_target

    @imaging_target.setter
    def imaging_target(self, value: vec3) -> None:
        self._imaging_target = value

    @property
    def selected_pose(self) -> int:
        """Returns the selected pose's ID."""
        return self._selected_pose

    @property
    def selected_pose_set(self) -> int:
        """Returns the selected pose set's ID."""
        return self._selected_pose_set

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

    def _get_device(self, device_id):
        return next(filter(lambda d: d.device_id == device_id, self.project.devices), None)

    def _listener(self) -> None:
        """Implements a listening thread."""
        read_thread = next(filter(lambda t: t.thread == threading.current_thread(), self._read_threads))

        continue_listening = lambda t = read_thread: not t.stop

        machine_queried = False

        print_debug_msg(self.console, f'{read_thread.thread.name.capitalize()} started', self._is_dev_env)

        while continue_listening():
            time.sleep(self._YIELD_TIMEOUT)
            resp = self._serial.read(read_thread.port)
            controllers_unlocked = False

            if resp:
                if isinstance(resp, SerialResponse):
                    dvc = self._get_device(resp.device_id)

                    if dvc:
                        dvc.set_serial_response(resp)

                if self._keep_working and self._is_machine_locked:

                    print_debug_msg(self.console,
                        '**** Machine error-locked. stopping imaging!! ****', self._is_dev_env)

                    self.stop_work()
                else:
                    self._clear_to_send = controllers_unlocked or self.is_machine_idle

                if self.is_machine_idle:
                    print_debug_msg(self.console, '**** Machine is clear ****', self._is_dev_env)

                    if len(self._mainqueue) <= 0:
                        print_debug_msg(self.console, '**** Machine is idle ****',
                            self._is_dev_env)
                        dispatcher.send('ntf_machine_idle')

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
                            f'Machine status stale (last: {self.machine_status}).',
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
                        print_debug_msg(self.console, f'Machine status stale (last: {self.machine_status}) for {round(no_report_span, 2)} seconds.',
                            self._is_dev_env)

                    # If no device has reported for 1 second since connecting, query the devices.
                    if not machine_queried and no_report_span > 1:
                        self._query_machine()
                        machine_queried = True

        print_debug_msg(self.console,
            f'{read_thread.thread.name.capitalize()} stopped', self._is_dev_env)

    def _worker(self, resuming=False, extra_callback=None) -> None:
        """Implements a worker thread."""
        t_name = self.work_type_name

        state = "resumed" if resuming else "started"
        print_debug_msg(self.console, f'{t_name} thread {state}', self._is_dev_env)

        def callback():
            if extra_callback:
                extra_callback()
            print_info_msg(self.console, f'{t_name} ended')  #where stepping ended was being generated

        dispatcher.connect(callback, signal='ntf_machine_idle')

        print_info_msg(self.console, f'{t_name} {state}')

        had_error = False
        try:
            while self._keep_working and \
                (self.is_serial_port_connected or self._is_edsdk_enabled):
                self._send_next()

        except AttributeError as err:
            print_error_msg(self.console, f'{t_name} thread stopped unexpectedly: {err.args[0]}')
            had_error = True

        finally:
            self._working_thread = None
            self._keep_working = False

            if not self._is_machine_paused:
                if self._work_type == WorkType.IMAGING:
                    self._current_mainqueue_item = -1
                    self.select_pose_set(-1)
                    self._imaged_pose_sets.clear()
                    self._session_id = self.sys_db.last_session_id() +1

                self._work_type = None

            if not had_error:
                print_debug_msg(self.console, f'{t_name} thread stopped', self._is_dev_env)

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
        if not store.path_exists_2(self._imaging_session_path, self._IMAGING_MANIFEST_FILE_NAME):
            manifest = self._imaging_session_manifest.pop(-1)
            self._imaging_session_manifest.clear()
            self._imaging_session_manifest.append(manifest)

        for key, value in pairs:
            self._imaging_session_manifest[-1][key] = value

        if pairs:
            store.save_json_2(self._imaging_session_path,
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
                        self._edsdk.take_picture(do_af) ## add auto disconnect
                    elif cmd.atype == ActionType.EDS_FOCUS:
                        shutter_release_time = value if key == 'S' else 0
                        self._edsdk.focus(shutter_release_time) ## add auto disconnect
                    else:
                        print_error_msg(self.console,
                            f"Host command '{cmd.atype.name}' not yet handled.")
                    #dvc.is_writing_eds = False
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
                # Temporary shoehorn of a post shutter delay.
                # We set a delay via _send_delay_ms when a shutter command is sent,
                # then reset it to zero after subsequent command is ready to send.
                if self._ressetable_send_delay_ms > 0:
                    start_timestamp_ms = round(time.time() * 1000)
                    print_debug_msg(self.console, 'begin post shutter delay', True)
                    while round(time.time() * 1000) - start_timestamp_ms < self._ressetable_send_delay_ms:
                        #could do something during delay
                        pass
                    self._ressetable_send_delay_ms = 0
                    print_debug_msg(self.console, 'end post shutter delay', True)
                self._send(*packet)
                self._clear_to_send = False #why is this set after the send and not before?
            else:
                print_debug_msg(self.console, 'Not writing empty packet.', self._is_dev_env)

        else:
            self._keep_working = False
            self._clear_to_send = True

    def _send(self, *commands):
        """Send command to machine."""
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
            print_debug_msg(self.console, 'Writing> [{0}] to device{1} '.format(cmd_lines.replace("\r", "\\r"), "s" if len(dvcs) > 1 else "") +
                f'{", ".join([str(d.device_id) for d in dvcs])}.', self._is_dev_env)

            pre_shutter_delay_completed = False
            for command in commands:
                if command.atype in self.SNAP_COMMANDS:
                    device = self._get_device(command.device)
                    method = 'remote shutter' if get_atype_kind(command.atype) == 'SER' else 'EDSDK'
                    #shoe-horning a mechanism for adding a pause before and after taking pictures
                    if not pre_shutter_delay_completed and 'pre_shutter_delay_ms' in self.project.options:
                        print_debug_msg(self.console, 'begin pre shutter delay', True)
                        time_delay_ms = self.project.options['pre_shutter_delay_ms']
                        start_timestamp_ms = round(time.time() * 1000)
                        while round(time.time() * 1000) - start_timestamp_ms < time_delay_ms:
                            #could do something while delay is happening
                            pass
                        pre_shutter_delay_completed = True
                        print_debug_msg(self.console, 'end pre shutter delay', True)
                    if 'post_shutter_delay_ms' in self.project.options:
                        self._ressetable_send_delay_ms = self.project.options['post_shutter_delay_ms']
                    self.sys_db.start_pose(device, method, session_id = self._session_id)

            if not is_edsdk_needed:
                for dvc in dvcs:
                    dvc.set_is_writing_ser() #why do we wait this long to se the is writing flag? What is the flag and how is it used?
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
        if device.serial_status == ComStatus.IDLE:
            self.sys_db.end_pose(device)

    def _on_device_eds_updated(self, device):
        if not device.is_writing_eds:
            self.sys_db.end_pose(device)

    def _imaging_callback(self):
        #self._session_id +=1
        dispatcher.disconnect(self._on_device_ser_updated, signal='ntf_device_ser_updated')
        dispatcher.disconnect(self._on_device_eds_updated, signal='ntf_device_eds_updated')

    def select_proxy(self, index) -> None:
        """Selects proxy given index in proxy list."""
        if index < 0:
            if self._selected_proxy >= 0:
                self._selected_proxy = -1

                dispatcher.send('ntf_o_deselected')
        elif index < len(self.project.proxies):
            self.select_device(-1)
            self.select_pose(-1)
            self.select_pose_set(-1)

            self._selected_proxy = index

            dispatcher.send('ntf_o_selected', object=self._selected_proxy)
        else:
            print_error_msg(self.console, f'Proxy object index {index} is out of range.')

    def select_device(self, index: int) -> None:
        """Selects device given index in device list."""
        if index < 0:
            if self._selected_device >= 0:
                self._selected_device = -1

                dispatcher.send('ntf_d_deselected')
        elif index < len(self.project.devices):
            self.select_proxy(-1)
            self.select_pose(-1)
            self.select_device(-1)
            self.select_pose_set(-1)

            self._selected_device = index

            dispatcher.send('ntf_d_selected', device=self.project.devices[self._selected_device])
        else:
            print_error_msg(self.console, f'Device index {index} is out of range.')

    def select_pose_set(self, index: int) -> None:
        """Highlights poses in a set given pose set index."""
        if index < 0:
            selected = self._selected_pose_set
            if self._selected_pose_set >= 0:
                self._selected_pose_set = -1

                dispatcher.send('ntf_s_deselected', set_index=selected)
        elif index < len(self.project.pose_sets):
            self.select_device(-1)
            self.select_proxy(-1)
            self.select_pose(-1)
            self.select_pose_set(-1)

            self._selected_pose_set = index

            dispatcher.send('ntf_s_selected', set_index=self._selected_pose_set)
        else:
            print_error_msg(self.console, f'Pose set index {index} is out of range.')

    def select_pose(self, index: int) -> None:
        """Selects pose given index in pose list."""
        if index < 0:
            selected = self._selected_pose
            if self._selected_pose >= 0:
                self._selected_pose = -1
                dispatcher.send('ntf_a_deselected', pose_index=selected)
        elif index < len(self.project.poses):
            self.select_device(-1)
            self.select_proxy(-1)
            self.select_pose(-1)
            self.select_pose_set(-1)

            self._selected_pose = index

            dispatcher.send('ntf_a_selected', pose_index=self._selected_pose)
        else:
            print_error_msg(self.console, f'Pose index {index} is out of range.')

    def update_selected_pose_position(self, args) -> None:
        """Update position of selected pose."""
        args = create_action_args(args)
        pose_position = self.project.poses[self._selected_pose].position
        argc = min(len(pose_position.args), len(args))

        for i in range(argc):
            pose_position.args[i] = args[i]

        pose_position.argc = argc
        pose_position.update()

        dispatcher.send('ntf_a_list_changed')

    def re_target_all_poses(self) -> None:
        """Re-targets all the poses with the given heading."""
        for pose in self.project.poses:
            pose_position = pose.position
            args = get_action_args_values(pose_position.args)
            end_pan, end_tilt = get_heading(vec3(args[:3]), self.imaging_target)

            args[3] = sanitize_number(end_pan)
            args[4] = sanitize_number(end_tilt)
            args = create_action_args(args)

            argc = min(len(pose_position.args), len(args))

            for i in range(argc):
                pose_position.args[i] = args[i]

            pose_position.argc = argc
            pose_position.update()

        dispatcher.send('ntf_a_list_changed')

    def target_vector_step_all_poses(self, distance) -> None:
        """Steps all poses towards/away from the target."""
        for pose in self.project.poses:
            pose_position = pose.position
            args = get_action_args_values(pose_position.args)

            end = get_end_position(Point5(*args[:5]), distance)
            end_pan, end_tilt = get_heading(end, self.imaging_target)

            args[0] = end.x
            args[1] = end.y
            args[2] = end.z
            args[3] = sanitize_number(end_pan)
            args[4] = sanitize_number(end_tilt)
            args = create_action_args(args)

            argc = min(len(pose_position.args), len(args))

            for i in range(argc):
                pose_position.args[i] = args[i]

            pose_position.argc = argc
            pose_position.update()

        dispatcher.send('ntf_a_list_changed')

    def add_to_selected_pose_payload(self, item: Action) -> bool:
        """Appends an action to the selected pose's payload."""
        pose = self.project.poses[self._selected_pose]
        pose.payload.append(item)

        dispatcher.send('ntf_a_list_changed')

        return True

    def delete_from_selected_pose_payload(self, index: int) -> bool:
        """Deletes an action from the selected pose's payload, given an index."""
        pose = self.project.poses[self._selected_pose]
        pose.payload.pop(index)

        dispatcher.send('ntf_a_list_changed')

        return True

    def export_poses(self, filename: str = None) -> list:
        """Serialize action list and write to file.

        TODO: Expand to include not just G0 and C0 actions
        """

        lines = []

        for pose in self.project.poses:
            line = serialize_command(pose)
            lines.append(line)

        if filename is not None:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write('\n'.join(lines))

        dispatcher.send('ntf_a_exported', filename=filename)
        return lines

    def optimize_all_poses_pan_angles(self) -> None:
        """Optimizes all the poses to minimize panning motion cost."""
        last_position_by_id = {}
        for pose in self.project.poses:
            pose_position = pose.position
            device_id = pose[0].device
            args = get_action_args_values(pose_position.args)
            pt = Point5(*args[:5])
            if device_id not in last_position_by_id:
                last_position_by_id[device_id] = pt
            else:
                optimized_pan_angle = optimize_rotation_move_to_angle(last_position_by_id[device_id].p, pt.p)
                args[3] = sanitize_number(optimized_pan_angle)
                args = create_action_args(args)
                argc = min(len(pose_position.args), len(args))
                for i in range(argc):
                    pose_position.args[i] = args[i]
                pose_position.argc = argc
                pose_position.update()
                args = get_action_args_values(pose_position.args)
                pt = Point5(*args[:5])
                last_position_by_id[device_id] = pt
        dispatcher.send('ntf_a_list_changed')
        #self.select_pose(self.selected_pose) # Reselect the current selected pose (if one was selected) to update variables in transform panel.

    def optimize_all_poses_randomize(self) -> None:
        """Optimizes all the poses to minimize panning motion cost."""
        rand_shuffle(self.project.pose_sets)
        dispatcher.send('ntf_a_list_changed')

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

    def start_imaging(self) -> bool:
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

        dispatcher.connect(self._on_device_ser_updated, signal='ntf_device_ser_updated')
        dispatcher.connect(self._on_device_eds_updated, signal='ntf_device_eds_updated')

        header = self._get_move_commands(True, *[dvc.device_id for dvc in self.project.devices])
        body = process_pose_sets()

        ### Revised footer to only send the disengage motors such that cams do not return to "ready" upon completion of an imaging session.
        # Uncomment next two lines and comment third to reenable.
        # footer = self._get_initialization_commands(ActionType.G1)
        # footer.extend(self._disengage_motors_commands)
        footer = self._disengage_motors_commands

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
        self._session_id = self.sys_db.last_session_id() +1
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

        # Join the working thread of finish work if we are it.
        if threading.current_thread() != self._working_thread:
            self._working_thread.join()

        self._working_thread = None
        print_info_msg(self.console, f'{self.work_type_name} paused')
        return True

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
