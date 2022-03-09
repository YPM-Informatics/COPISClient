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

from pydispatch import dispatcher
from glm import vec3

from copis.classes import Action
from copis.command_processor import serialize_command
from copis.helpers import create_action_args, print_error_msg


class ComponentMembersMixin:
    """Implement COPIS Core component (actions, points, devices, proxy objects)
        related class members using mixins."""

    @property
    def imaging_target(self) -> vec3:
        """Returns the coordinates of the last target; (0,0,0) if application just started."""
        return self._imaging_target

    @imaging_target.setter
    def imaging_target(self, value: vec3) -> None:
        self._imaging_target = value


    # @property
    # def selected_device(self) -> int:
    #     """Returns the selected device's ID."""
    #     return self._selected_device

    @property
    def selected_pose(self) -> int:
        """Returns the selected pose's ID."""
        return self._selected_pose

    @property
    def selected_pose_set(self) -> int:
        """Returns the selected pose set's ID."""
        return self._selected_pose_set

    # @property
    # def selected_proxy(self) -> int:
    #     """Returns the selected proxy object's ID."""
    #     return self._selected_proxy

    def _get_device(self, device_id):
        return next(filter(lambda d: d.device_id == device_id, self.project.devices), None)

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
            with open(filename, 'w') as file:
                file.write('\n'.join(lines))

        dispatcher.send('ntf_a_exported', filename=filename)
        return lines
