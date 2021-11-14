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

"""COPIS Core machine related class members."""

import threading

from copis.classes.action import Action
from copis.command_processor import deserialize_command
from copis.globals import ActionType, ComStatus, WorkType
from copis.helpers import print_debug_msg, print_error_msg


class MachineMembersMixin:
    """Implement COPIS Core machine related class members using mixins."""
    @property
    def _is_machine_busy(self):
        return self._working_thread is not None or self._is_machine_paused
    @property
    def _machine_status(self):
        status = 'unknown'
        statuses = list(set(dvc.serial_status for dvc in self.devices))

        if len(statuses) == 1 and statuses[0]:
            status = statuses[0].name.lower()
        elif len(statuses) > 1:
            status = 'mixed'

        return status

    @property
    def _machine_last_reported_on(self):
        reports = [dvc.last_reported_on for dvc in self.devices if dvc.last_reported_on]
        return max(reports) if len(reports) > 0 else None

    @property
    def _is_machine_locked(self):
        for dvc in self.devices:
            if dvc.serial_response:
                flags = dvc.serial_response.system_status_flags

                if flags and len(flags) == 8 and int(flags[0]):
                    return True

        return False

    @property
    def _has_machine_reported(self):
        if any(not dvc.serial_response for dvc in self.devices):
            return False

        return all(dvc.serial_status != ComStatus.UNKNOWN for dvc in self.devices)

    @property
    def _absolute_move_commands(self):
        cmds = []
        for dvc in self.devices:
            cmds.append(Action(ActionType.G90, dvc.device_id))

        actions = []
        actions.append(cmds)
        return actions

    @property
    def _disengage_motors_commands(self):
        cmds = []
        for dvc in self.devices:
            cmds.append(Action(ActionType.M18, dvc.device_id))

        actions = []
        actions.append(cmds)
        return actions

    @property
    def is_machine_idle(self):
        """Returns a value indicating whether the machine is idle."""
        return all(dvc.serial_status == ComStatus.IDLE for dvc in self.devices)

    @property
    def is_machine_homed(self):
        """Returns a value indicating whether the machine is homed."""
        return all(dvc.is_homed for dvc in self.devices)

    def _query_machine(self):
        print_debug_msg(self.console, '**** Querying machine ****', self._is_dev_env)
        cmds = []

        if self._is_machine_busy:
            print_error_msg(self.console, 'Cannot query. The machine is busy.')
            return

        for dvc in self.devices:
            cmds.append(Action(ActionType.G0, dvc.device_id))

        if cmds:
            self._keep_working = True
            self._clear_to_send = True
            self._mainqueue = []
            self._mainqueue.append(cmds)
            self._send_next()
            self._keep_working = False

    def _chunk_actions(self, batch_size, actions=None):
        cmds = actions if actions else self._actions
        return [cmds[i:i + batch_size] for i in range(0, len(cmds), batch_size)]

    def _unlock_machine(self):
        print_debug_msg(self.console, '**** Unlocking machine ****', self._is_dev_env)
        cmds = []

        if self._is_machine_busy:
            print_error_msg(self.console, 'Cannot unlock. The machine is busy.')
            return False

        for dvc in self.devices:
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

        for dvc in self.devices:
            device_id = dvc.device_id
            cmd_str_1 = ''
            cmd_str_2 = ''
            x, y, z, p, t = self._get_device(device_id).initial_position

            if device_id == 0:
                cmd_str_1 = f'{g_code}Z{z}'
                cmd_str_2 = f'{g_code}X{x}Y{y}P{p}T{t}'
            elif device_id == 1:
                cmd_str_1 = f'>{device_id}{g_code}Z{z}'
                cmd_str_2 = f'>{device_id}{g_code}X{x}Y{y}P{p}T{t}'
            elif device_id == 2:
                cmd_str_1 = f'>{device_id}{g_code}Z{z}'
                cmd_str_2 = f'>{device_id}{g_code}X{x}Y{y}P{p}T{t}'

            step_1.append(deserialize_command(cmd_str_1))
            step_2.append(deserialize_command(cmd_str_2))

        actions.append(step_1)
        actions.append(step_2)
        return actions

    def set_ready(self):
        """Initializes the gantries to their current positions."""
        def set_ready_callback():
            for dvc in self.devices:
                dvc.is_homed = True

        if self._is_machine_busy:
            print_error_msg(self.console, 'Cannot set or go to ready. The machine is busy.')
            return

        cmds = self._get_initialization_commands(ActionType.G92)

        if cmds:
            self._mainqueue = []
            self._mainqueue.extend(cmds)
            self._mainqueue.extend(self._disengage_motors_commands)

            self._keep_working = True
            self._clear_to_send = True
            self._working_thread = threading.Thread(
                target=self._worker,
                name='working thread',
                kwargs={
                    "work_type": WorkType.SET_READY,
                    "extra_callback": set_ready_callback
                }
            )
            self._working_thread.start()
