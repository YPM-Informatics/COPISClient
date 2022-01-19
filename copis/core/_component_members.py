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

"""COPIS Core component (actions, points, devices, proxy objects) related class members."""

from typing import List
from pydispatch import dispatcher

from copis.classes import Action, Device, Object3D, Pose
from copis.command_processor import serialize_command
from copis.globals import ActionType
from copis.helpers import create_action_args, print_error_msg


class ComponentMembersMixin:
    """Implement COPIS Core component (actions, points, devices, proxy objects)
        related class members using mixins."""
    @property
    def actions(self) -> List[Pose]:
        """Returns the core action list."""
        return self._actions

    # @property
    # def selected_device(self) -> int:
    #     """Returns the selected device's ID."""
    #     return self._selected_device

    # @property
    # def selected_pose(self) -> int:
    #     """Returns the selected pose's ID."""
    #     return self._selected_pose

    # @property
    # def selected_proxy(self) -> int:
    #     """Returns the selected proxy object's ID."""
    #     return self._selected_proxy

    def _get_device(self, device_id):
        return next(filter(lambda d: d.device_id == device_id, self.project.devices), None)

    def add_action(self, atype: ActionType, device: int, *args) -> bool:
        """TODO: validate args given atype"""
        new = Action(atype, device, len(args), list(args))

        self._actions.append(new)

        # if certain type, broadcast that positions are modified
        if atype in (ActionType.G0, ActionType.G1, ActionType.G2, ActionType.G3):
            dispatcher.send('ntf_a_list_changed')

        return True

    def remove_action(self, index: int) -> Action:
        """Removes an action given action list index."""
        action = self._actions.pop(index)
        dispatcher.send('ntf_a_list_changed')
        return action

    def clear_action(self) -> None:
        """Removes all actions from actions list."""
        self._actions.clear()
        dispatcher.send('ntf_a_list_changed')

    def select_proxy(self, index) -> None:
        """Selects proxy given index in proxy list."""
        self._selected_proxies.append(index)
        if index < 0 and self.selected_device >= 0:
            self._selected_device = -1

            dispatcher.send('ntf_d_deselected')

    def select_device(self, index: int) -> None:
        """Selects device given index in d."""
        if index < 0 and self.selected_device >= 0:
            self._selected_device = -1

            dispatcher.send('ntf_d_deselected')
        elif index < len(self.project.devices):
            self.select_proxy(-1)
            self.select_pose(-1)

            self._selected_device = index

            dispatcher.send('ntf_d_selected', device=self._selected_device)

        else:
            print_error_msg(self.console, f'Device index {index} is out of range.')

    def select_pose(self, index: int) -> None:
        """Selects pose given index in pose list."""
        if index < 0 and self._selected_pose >= 0:
            self._selected_pose = -1

            dispatcher.send('ntf_a_deselected')
        elif index < len (self._actions):
            self.select_device(-1)
            self.select_proxy(-1)

            self._selected_pose = index

            dispatcher.send('ntf_a_selected', pose=self._selected_pose)

        else:
            print_error_msg(self.console, f'Pose index {index} is out of range.')

    def update_selected_points(self, args) -> None:
        """Update position of points in selected points list."""
        args = create_action_args(args)
        for id_ in self.selected_points:
            action = self.actions[id_].position
            for i in range(min(len(action.args), len(args))):
                action.args[i] = args[i]

        dispatcher.send('ntf_a_list_changed')

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

        dispatcher.send('ntf_a_exported', filename=filename)
        return lines
