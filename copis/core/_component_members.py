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

    @property
    def devices(self) -> List[Device]:
        """Returns the core device list."""
        return self._devices

    @property
    def objects(self) -> List[Object3D]:
        """Returns the core object list."""
        return self._objects

    @property
    def selected_device(self) -> int:
        """Returns the selected device."""
        return self._selected_device

    @property
    def selected_points(self) -> List[int]:
        """Returns the selected points."""
        return self._selected_points

    def _get_device(self, device_id):
        return next(filter(lambda d: d.device_id == device_id, self.devices), None)

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

    def select_device(self, index: int) -> None:
        """Select device given index in devices list."""
        if index < 0:
            self._selected_device = -1
            dispatcher.send('ntf_d_deselected')

        elif index < len(self._devices):
            self._selected_device = index
            self.select_point(-1)
            dispatcher.send('ntf_o_deselected')
            dispatcher.send('ntf_d_selected', device=self._devices[index])

        else:
            print_error_msg(self.console, f'invalid device index {index}.')

    def select_point(self, index: int, clear: bool = True) -> None:
        """Add point to points list given index in actions list.

        Args:
            index: An integer representing index of action to be selected.
            clear: A boolean representing whether to clear the list before
                selecting the new point or not.
        """
        if index == -1:
            self._selected_points.clear()
            dispatcher.send('ntf_a_deselected')
            return

        if index >= len(self._actions):
            return

        if clear:
            self._selected_points.clear()

        if index not in self._selected_points:
            self._selected_points.append(index)
            self.select_device(-1)
            dispatcher.send('ntf_o_deselected')
            dispatcher.send('ntf_a_selected', points=self._selected_points)

    def deselect_point(self, index: int) -> None:
        """Remove point from selected points given index in actions list."""
        try:
            self._selected_points.remove(index)
            dispatcher.send('ntf_a_deselected')
        except ValueError:
            return

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
