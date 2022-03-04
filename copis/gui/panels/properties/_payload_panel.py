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

"""COPIS default properties panel."""

import wx

from copis.classes import Action, Pose

from copis.globals import ActionType
from copis.gui.wxutils import simple_statictext
from copis.helpers import create_action_args


class PayloadPanel(wx.Panel):
    """Show default properties panel."""

    def __init__(self, parent) -> None:
        super().__init__(parent, style=wx.BORDER_NONE)
        self._parent = parent
        self._core = parent.core
        self._pose = None

        self._box_sizer = None
        self._add_btn = None

    def _init_layout(self):
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self._box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Payload'), wx.VERTICAL)

        grid = wx.FlexGridSizer(1, 2, 0, 0)
        grid.AddGrowableCol(0)

        self._add_btn = wx.Button(self, label='Add', size=(50, -1), name='add')
        self._add_btn.Bind(wx.EVT_BUTTON, self._on_add_payload)

        grid.AddMany([
            (0, 0),
            (self._add_btn, 0, wx.EXPAND, 0)
        ])

        self._box_sizer.Add(grid, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)

        self.Sizer.Add(self._box_sizer, 0, wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, 5)
        self.Layout()

    def _on_add_payload(self, _):
        c_args = create_action_args([1.5], 'S')
        payload_item = Action(ActionType.C0, self._pose.position.device,
            len(c_args), c_args)

        if self._core.add_to_selected_pose_payload(payload_item):
            pose = self._core.project.poses[self._core.selected_pose]
            self.set_pose(pose)

    def _on_delete_payload(self, event: wx.CommandEvent):
        payload_index = event.EventObject.payload_index

        if self._core.delete_from_selected_pose_payload(payload_index):
            pose = self._core.project.poses[self._core.selected_pose]
            self.set_pose(pose)

    def set_pose(self, pose: Pose):
        """Parses the selected pose into the panel."""
        self._pose = pose

        self.DestroyChildren()
        self._init_layout()

        grid = wx.FlexGridSizer(len(pose.payload) * 2, 2, 0, 0)
        grid.AddGrowableCol(0)

        if pose.payload:
            self._add_btn.Disable()
        else:
            self._add_btn.Enable()

        for i, action in enumerate(pose.payload):
            delete_btn = wx.Button(self, label='Delete', size=(50, -1), name='delete')
            delete_btn.payload_index = i
            delete_btn.Bind(wx.EVT_BUTTON, self._on_delete_payload)
            caption = _get_payload_item_caption(action)

            grid.AddMany([
                (wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL, 5),
                (wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                (simple_statictext(self, caption), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
                (delete_btn, 0, wx.EXPAND, 0)
            ])

        self._box_sizer.Add(grid, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

        self.Sizer.RepositionChildren(self.Sizer.MinSize)
        self._parent.SetVirtualSize(self._parent.Sizer.MinSize)


def _get_payload_item_caption(action):
    time_args = {
        'P': 'millisecond',
        'S': 'second',
        'X': 'second'
    }

    caption = '<not implemented>'

    if action.atype == ActionType.C0:
        caption = 'Snap picture within'
        key, value = action.args[0]

        if key in time_args:
            caption = f'{caption} {value} {time_args[key]}{"s" if value != 1 else ""}'
        else:
            caption = f'{caption} {value} <invalid time unit>'

    return caption
