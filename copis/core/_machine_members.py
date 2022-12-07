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

"""COPIS Core machine related class members."""

import threading
import uuid
from typing import List
from pydispatch import dispatcher
from itertools import zip_longest

from copis.classes import Action, Pose
from copis.command_processor import deserialize_command
from copis.globals import ActionType, ComStatus, WorkType
from copis.helpers import get_atype_kind, get_timestamp, print_debug_msg, print_error_msg



class MachineMembersMixin:
    """Implement COPIS Core machine related class members using mixins."""
    @property
    def _is_machine_busy(self):
        return self._working_thread is not None or self._is_machine_paused

    @property
    def _machine_last_reported_on(self):
        reports = [dvc.last_reported_on for dvc in self.project.devices if dvc.last_reported_on]
        return max(reports) if len(reports) > 0 else None

    @property
    def _is_machine_locked(self):
        for dvc in self.project.devices:
            if dvc.serial_response:
                flags = dvc.serial_response.system_status_flags
                if flags and len(flags) == 8 and int(flags[0]):
                    return True

        return False

    @property
    def _has_machine_reported(self):
        if any(not dvc.serial_response for dvc in self.project.devices):
            return False

        return all(dvc.serial_status != ComStatus.UNKNOWN for dvc in self.project.devices)

    @property
    def _disengage_motors_commands(self):
        cmds = []
        for dvc in self.project.devices:
            cmds.append(Action(ActionType.M18, dvc.device_id))

        actions = []
        actions.append(cmds)
        return actions

    @property
    def machine_status(self):
        """Returns the machine's status."""
        status = 'unknown'

        if self._is_machine_paused:
            status = 'paused'
        else:
            statuses = list(set(dvc.status for dvc in self.project.devices))

            if len(statuses) == 1 and statuses[0]:
                status = statuses[0].name.lower()
            elif len(statuses) > 1:
                status = 'mixed'

        return status

    @property
    def is_machine_idle(self):
        """Returns a value indicating whether the machine is idle."""
        return all(dvc.status == ComStatus.IDLE for dvc in self.project.devices)

    @property
    def is_machine_homed(self):
        """Returns a value indicating whether the machine is homed."""
        return all(dvc.is_homed for dvc in self.project.devices)

    def _get_move_commands(self, is_absolute, *device_ids):
        actions = []
        all_device_ids = [dvc.device_id for dvc in self.project.devices]

        if device_ids and all(did in all_device_ids for did in device_ids):
            atype = ActionType.G90 if is_absolute else ActionType.G91
            cmds = []

            for did in device_ids:
                cmds.append(Action(atype, did))

            actions.append(cmds)

        return actions

    def _query_machine(self):
        print_debug_msg(self.console, '**** Querying machine ****', self._is_dev_env)
        cmds = []

        if self._is_machine_busy:
            print_error_msg(self.console, 'Cannot query. The machine is busy.')
            return

        cmds.append(Action(ActionType.M120, 0))

        if cmds:
            self._keep_working = True
            self._clear_to_send = True
            self._mainqueue = []
            self._mainqueue.append(cmds)
            self._send_next()
            self._keep_working = False

    def _unlock_machine(self):
        print_debug_msg(self.console, '**** Unlocking machine ****', self._is_dev_env)
        cmds = []

        if self._is_machine_busy:
            print_error_msg(self.console, 'Cannot unlock. The machine is busy.')
            return False

        for dvc in self.project.devices:
            if dvc.serial_response:
                flags = dvc.serial_response.system_status_flags

                if flags and len(flags) == 8 and int(flags[0]):
                    cmd = Action(ActionType.M511, dvc.device_id)
                    cmds.append(cmd)

        if cmds:
            self._keep_working = True
            self._clear_to_send = True
            self._mainqueue = []
            self._mainqueue.append(cmds)
            self._send_next()
            self._keep_working = False
            return True

        return False

    def _get_initialization_commands(self, atype: ActionType):
        step_1 = []
        step_2 = []
        actions = []
        g_code = str(atype).split('.')[1]

        for dvc in self.project.devices:
            device_id = dvc.device_id
            cmd_id = ''
            cmd_str_1 = ''
            cmd_str_2 = ''
            x, y, z, p, t = self._get_device(device_id).home_position

            if device_id > 0:
                cmd_id = f'>{device_id}'

            cmd_str_1 = f'{cmd_id}{g_code}Z{z}'
            cmd_str_2 = f'{cmd_id}{g_code}X{x}Y{y}P{p}T{t}'

            step_1.append(deserialize_command(cmd_str_1))
            step_2.append(deserialize_command(cmd_str_2))

        actions.append(step_1)
        actions.append(step_2)
        return actions

    def _reconcile_machine(self, dvc_statuses):
        for status in dvc_statuses:
            if status:
                did, is_homed, resp = status
                device = self._get_device(did)

                if is_homed and device and resp:
                    device.set_serial_response(resp)
                    device.set_is_homed()

    def set_ready(self):
        """Initializes the gantries to their current positions."""
        def set_ready_callback():
            for dvc in self.project.devices:
                dvc.set_is_homed()

        if self._is_machine_busy:
            print_error_msg(self.console, 'Cannot set or go to ready. The machine is busy.')
            return

        init_code = ActionType.G1 if self.is_machine_homed else ActionType.G92
        cmds = self._get_initialization_commands(init_code)

        if cmds:
            self._mainqueue = []
            self._mainqueue.extend(cmds)
            self._mainqueue.extend(self._disengage_motors_commands)
            self._work_type = WorkType.SET_READY

            self._keep_working = True
            self._clear_to_send = True
            self._working_thread = threading.Thread(
                target=self._worker,
                name='working thread',
                kwargs={
                    "extra_callback": set_ready_callback
                }
            )
            self._working_thread.start()

    def jog(self, action: Action):
        """Jogs the machine according to the provided action."""
        if not self.is_serial_port_connected:
            print_error_msg(self.console,
                'The machine needs to be connected before jogging can start.')
            return

        if self._is_machine_busy:
            print_error_msg(self.console, 'Cannot jog. The machine is busy.')
            return

        if not self.is_machine_idle:
            print_error_msg(self.console, 'The machine needs to be homed before jogging can start.')
            return

        header = self._get_move_commands(False, action.device)
        body = [action]
        footer = self._get_move_commands(True, action.device)

        self._mainqueue = []
        self._mainqueue.extend(header)
        self._mainqueue.append(body)
        self._mainqueue.extend(footer)
        self._work_type = WorkType.JOGGING

        self._keep_working = True
        self._clear_to_send = True
        self._working_thread = threading.Thread(
            target=self._worker,
            name='working thread'
        )
        self._working_thread.start()

    def play_poses(self, poses: List[Pose]):
        """Play the given pose set."""
        self._session_guid = str(uuid.uuid4())
        process_poses = lambda: [[val for val in tup if val is not None] for tup in
            zip_longest(*[p.get_seq_actions() for p in poses])]

        processed_poses = process_poses()
        commands = []
        commands.extend([c for p in processed_poses for c in p])
        is_serial_needed = any(get_atype_kind(p.atype) == 'SER' for p in commands)
        is_edsdk_needed = any(get_atype_kind(p.atype) == 'EDS' for p in commands)

        if is_serial_needed:
            if not self.is_serial_port_connected:
                print_error_msg(self.console,
                    'The machine needs to be connected before stepping can start.')
                return

            if self._is_machine_busy:
                print_error_msg(self.console, 'Cannot step. The machine is busy.')
                return

            if not self.is_machine_idle:
                print_error_msg(self.console,
                    'The machine needs to be homed before stepping can start.')
                return

        if is_edsdk_needed:
            if not self._is_edsdk_enabled:
                print_error_msg(self.console, 'EDSDK is not enabled.')
                return

        #if keep_last_path:
        #    self._save_imaging_session = False
        #else:
        #    self._imaging_session_path = save_path
        #    self._save_imaging_session = bool(self._imaging_session_path)

        #if self._save_imaging_session:
        #    self._imaging_session_queue = []
        #    self._add_manifest_section()
        #
        #    pairs = [('imaging_start_time', get_timestamp(True)),
        #        ('imaging_end_time', None)]
        #    pairs.append(self._get_image_counts(poses))
        #    pairs.append(('images', []))

        #    self._update_imaging_manifest(pairs)
        
        dispatcher.connect(self._on_device_ser_updated, signal='ntf_device_ser_updated') 
        dispatcher.connect(self._on_device_eds_updated, signal='ntf_device_eds_updated')

        self._mainqueue = []
        self._mainqueue.extend(processed_poses)
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
