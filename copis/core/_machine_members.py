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

# from math import cos, sin

from copis.classes import Action
from copis.command_processor import deserialize_command
from copis.globals import ActionType, ComStatus, WorkType # , Point5
from copis.helpers import print_debug_msg, print_error_msg # , print_info_msg, dd_to_rad,
    # rad_to_dd, sanitize_number)


class MachineMembersMixin:
    """Implement COPIS Core machine related class members using mixins."""
    @property
    def _is_machine_busy(self):
        return self._working_thread is not None or self._is_machine_paused
    @property
    def _machine_status(self):
        status = 'unknown'
        statuses = list(set(dvc.serial_status for dvc in self.project.devices))

        if len(statuses) == 1 and statuses[0]:
            status = statuses[0].name.lower()
        elif len(statuses) > 1:
            status = 'mixed'

        return status

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
    def is_machine_idle(self):
        """Returns a value indicating whether the machine is idle."""
        return all(dvc.serial_status == ComStatus.IDLE for dvc in self.project.devices)

    @property
    def is_machine_homed(self):
        """Returns a value indicating whether the machine is homed."""
        return all(dvc.is_homed for dvc in self.project.devices)

    # def _back_off(self, device_360):
    #     device_id = device_360[0]
    #     # TODO: make this: device radius - (dist(cam/proxy) - proxy object radius).
    #     dist = 25
    #     dvc = self._get_device(device_id)

    #     pos1 = dvc.serial_response.position
    #     pos2 = Point5(*[float(arg[1]) for arg in device_360[1].args])

    #     # The right formula for this is new_x = x + (dist * cos(pan)) &
    #     # new_y = y + (dist * cos(pan)). but since our pan angle is measured
    #     # relative to the positive y axis, we have to flip sine and cosine.
    #     x1 = sanitize_number(pos1.x + (dist * sin(dd_to_rad(pos1.p))))
    #     y1 = sanitize_number(pos1.y + (dist * cos(dd_to_rad(pos1.p))))
    #     z1 = pos1.z

    #     x2 = sanitize_number(pos2.x + (dist * sin(pos2.p)))
    #     y2 = sanitize_number(pos2.y + (dist * cos(pos2.p)))
    #     z2 = pos2.z

    #     pt1 = Point5(x1, y1, z1, dd_to_rad(pos1.p), dd_to_rad(pos1.t))
    #     pt2 = Point5(x2, y2, z2, pos2.p, pos2.t)

    #     return[pt1, pt2]

    # def _get_imminent_360s(self, actions):
    #     device_ids = list(set(a.device for a in actions))
    #     move_codes = [ActionType.G0, ActionType.G1]

    #     results = []
    #     for did in device_ids:
    #         dvc = self._get_device(did)
    #         move_actions = [a for a in actions if a.device == did and a.atype in move_codes]
    #         move_action = move_actions[0] if len(move_actions) > 0 else None

    #         if move_action and dvc.serial_response:
    #             last_pan = dvc.serial_response.position.p
    #             pan_arg = [a for a in move_action.args if a[0].lower() == 'p']
    #             next_pan = rad_to_dd(float(pan_arg[0][1])) if pan_arg else None

    #             if next_pan is not None and abs(next_pan - last_pan) > 180:
    #                 print_info_msg(self.console, f'last: {last_pan}, next: {next_pan}, diff: {next_pan - last_pan}')
    #                 results.append((did, move_action))

    #     return results

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

        for dvc in self.project.devices:
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
        actions = []

        for i in range(0, len(cmds), batch_size):
            chunk = cmds[i:i + batch_size]
            chunk_actions = []

            for pose in chunk:
                chunk_actions.extend(pose.get_actions())

            actions.append(chunk_actions)

        return actions

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
            cmd_str_1 = ''
            cmd_str_2 = ''
            x, y, z, p, t = self._get_device(device_id).home_position

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
        if self._is_machine_busy:
            print_error_msg(self.console, 'Cannot jog. The machine is busy.')
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
