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

from copis.classes.action import Action
from copis.command_processor import deserialize_command
from copis.globals import ActionType, ComStatus
from copis.helpers import print_debug_msg, print_info_msg


class MachineMembersMixin:
    """Implement COPIS Core machine related class members using mixins."""
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

    def _query_devices(self):
        print_debug_msg(self.console, '**** Querying machine ****', self._is_dev_env)
        cmd_list = []

        for dvc in self.devices:
            cmd_list.append(Action(ActionType.G0, dvc.device_id))

        self.send_now(*cmd_list)
        self._clear_to_send = True

    def _unlock_controllers(self):
        print_debug_msg(self.console, '**** Unlocking machine ****', self._is_dev_env)
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
