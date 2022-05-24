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

"""COPIS pose payload properties panel."""

import wx

from copis.classes import Action, Pose

from copis.globals import ActionType
from copis.gui.wxutils import simple_statictext
from copis.helpers import create_action_args, print_info_msg


class PayloadPanel(wx.Panel):
    """Show pose payload properties panel."""

    _BTN_SIZE = (45, -1)

    def __init__(self, parent) -> None:
        super().__init__(parent, style=wx.BORDER_NONE)
        self._parent = parent
        self._core = parent.core
        self._pose = None

        self._box_sizer = None
        self._add_btn = None
        self._toggles = None
        self._payload_dlg = None

    def _init_layout(self):
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self._box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Payload'), wx.VERTICAL)

        grid = wx.FlexGridSizer(1, 2, 0, 0)
        grid.AddGrowableCol(0)

        self._add_btn = wx.Button(self, label='Add', size=self._BTN_SIZE, name='add')
        self._add_btn.Bind(wx.EVT_BUTTON, self._on_add_payload)

        grid.AddMany([
            (0, 0),
            (self._add_btn, 0, wx.EXPAND, 0)
        ])

        self._box_sizer.Add(grid, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)

        self.Sizer.Add(self._box_sizer, 0, wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, 5)
        self.Layout()

    def _build_serial_shot_ctrl(self):
        sizer = wx.FlexGridSizer(2, 1, 2, 0)
        sizer.AddGrowableCol(0, 0)
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)

        shutter_release_times = wx.SpinCtrlDouble(self._payload_dlg, wx.ID_ANY,
            min=0, max=5, initial=0, inc=.1, size=(45, -1))
        add_btn = wx.Button(self._payload_dlg, wx.ID_ANY,
            label='Add')

        ctrl_sizer.AddMany([
            (simple_statictext(self._payload_dlg, 'Release shutter in (seconds): ', -1),
                0, wx.EXPAND, 0),
            (shutter_release_times, 0, wx.EXPAND, 0)
        ])

        sizer.AddMany([
            (ctrl_sizer, 0, wx.ALIGN_CENTER, 0),
            (add_btn, 0, wx.ALIGN_RIGHT|wx.EXPAND, 0)
        ])

        return sizer

    def _build_serial_focus_ctrl(self):
        sizer = wx.FlexGridSizer(2, 1, 2, 0)
        sizer.AddGrowableCol(0, 0)
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)

        shutter_release_times = wx.SpinCtrlDouble(self._payload_dlg, wx.ID_ANY,
            min=0, max=5, initial=0, inc=.1, size=(45, -1))
        add_btn = wx.Button(self._payload_dlg, wx.ID_ANY,
            label='Add')

        ctrl_sizer.AddMany([
            (simple_statictext(self._payload_dlg, 'Release shutter in (seconds): ', -1),
                0, wx.EXPAND, 0),
            (shutter_release_times, 0, wx.EXPAND, 0)
        ])

        sizer.AddMany([
            (ctrl_sizer, 0, wx.ALIGN_CENTER, 0),
            (add_btn, 0, wx.ALIGN_RIGHT|wx.EXPAND, 0)
        ])

        return sizer

    def _build_edsdk_shot_ctrl(self):
        sizer = wx.FlexGridSizer(2, 1, 0, 0)
        sizer.AddGrowableCol(0, 0)

        af_option = wx.CheckBox(self._payload_dlg, wx.ID_ANY,
            label='Do auto focus')
        add_btn = wx.Button(self._payload_dlg, wx.ID_ANY,
            label='Add')

        sizer.AddMany([
            (af_option, 0, wx.ALIGN_CENTER, 0),
            (add_btn, 0, wx.ALIGN_RIGHT|wx.EXPAND, 0)
        ])

        return sizer

    def _build_edsdk_focus_ctrl(self):
        sizer = wx.FlexGridSizer(2, 1, 2, 0)
        sizer.AddGrowableCol(0, 0)
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)

        shutter_release_times = wx.SpinCtrlDouble(self._payload_dlg, wx.ID_ANY,
            min=0, max=5, initial=0, inc=.1, size=(45, -1))
        add_btn = wx.Button(self._payload_dlg, wx.ID_ANY,
            label='Add')

        ctrl_sizer.AddMany([
            (simple_statictext(self._payload_dlg, 'Release shutter in (seconds): ', -1),
                0, wx.EXPAND, 0),
            (shutter_release_times, 0, wx.EXPAND, 0)
        ])

        sizer.AddMany([
            (ctrl_sizer, 0, wx.ALIGN_CENTER, 0),
            (add_btn, 0, wx.ALIGN_RIGHT|wx.EXPAND, 0)
        ])

        return sizer

    def _on_add_payload(self, _):
        dlg_size = (100, -1)
        pos = self.GetScreenPosition()
        self._payload_dlg = wx.Dialog(self, wx.ID_ANY, 'Add Payload Item', size=dlg_size, pos=pos)
        self._payload_dlg.Sizer = wx.BoxSizer(wx.VERTICAL)
        header_sizer = wx.FlexGridSizer(1, 2, 0, 5)
        serial_sizer = wx.StaticBoxSizer(wx.StaticBox(self._payload_dlg,
            label='Serial'), wx.VERTICAL)
        edsdk_sizer = wx.StaticBoxSizer(wx.StaticBox(self._payload_dlg,
            label='EDSDK'), wx.VERTICAL)

        header_sizer.AddMany([
            (serial_sizer, 0, wx.EXPAND, 0),
            (edsdk_sizer, 0, wx.EXPAND, 0)
        ])

        add_edsdk_shot_btn = wx.ToggleButton(self._payload_dlg, wx.ID_ANY,
            label='Add Shot', name='add_shot_edsdk')
        add_edsdk_focus_btn = wx.ToggleButton(self._payload_dlg, wx.ID_ANY,
            label='Add Focus', name='add_focus_edsdk')
        add_edsdk_stack_btn = wx.ToggleButton(self._payload_dlg, wx.ID_ANY,
            label='Add Focus-Stacked Shots', name='add_stack_edsdk')
        add_serial_shot_btn = wx.ToggleButton(self._payload_dlg, wx.ID_ANY,
            label='Add Shot', name='add_shot_serial')
        add_serial_focus_btn= wx.ToggleButton(self._payload_dlg, wx.ID_ANY,
            label='Add Focus', name='add_focus_serial')
        add_serial_stack_btn = wx.ToggleButton(self._payload_dlg, wx.ID_ANY,
            label='Add Focus-Stacked Shots', name='add_stack_serial')

        self._toggles = [add_edsdk_shot_btn, add_edsdk_focus_btn, add_edsdk_stack_btn,
            add_serial_shot_btn, add_serial_focus_btn, add_serial_stack_btn]

        for toggle in self._toggles:
            toggle.Bind(wx.EVT_TOGGLEBUTTON, self._on_toggled)

        serial_sizer.AddMany([
            (add_serial_shot_btn, 0, wx.EXPAND, 0),
            (add_serial_focus_btn, 0, wx.EXPAND, 0),
            (add_serial_stack_btn, 0, wx.EXPAND, 0)
        ])

        edsdk_sizer.AddMany([
            (add_edsdk_shot_btn, 0, wx.EXPAND, 0),
            (add_edsdk_focus_btn, 0, wx.EXPAND, 0),
            (add_edsdk_stack_btn, 0, wx.EXPAND, 0)
        ])

        self._payload_dlg.Sizer.AddMany([
            (header_sizer, 0, wx.ALL|wx.EXPAND, 5),
            (self._build_serial_shot_ctrl(), 0, wx.ALL|wx.EXPAND, 5),
            (self._build_edsdk_focus_ctrl(), 0, wx.ALL|wx.EXPAND, 5),
            (self._build_edsdk_shot_ctrl(), 0, wx.ALL|wx.EXPAND, 5),
            (self._build_edsdk_focus_ctrl(), 0, wx.ALL|wx.EXPAND, 5)
        ])
        self._payload_dlg.Layout()
        self._payload_dlg.SetMinSize(dlg_size)
        self._payload_dlg.Fit()

        self._payload_dlg.ShowModal()
        # c_args = create_action_args([1.5], 'S')
        # payload_item = Action(ActionType.C0, self._pose.position.device,
        #     len(c_args), c_args)

        # if self._core.add_to_selected_pose_payload(payload_item):
        #     pose = self._core.project.poses[self._core.selected_pose]
        #     self.set_pose(pose)

    def _on_toggled(self, event: wx.CommandEvent):
        toggled = event.EventObject
        for toggle in self._toggles:
            if toggle.Name != toggled.Name:
                toggle.SetValue(False)

    def _on_delete_payload_item(self, event: wx.CommandEvent):
        payload_index = event.EventObject.payload_index

        if self._core.delete_from_selected_pose_payload(payload_index):
            pose = self._core.project.poses[self._core.selected_pose]
            self.set_pose(pose)

    def _on_edit_payload_item(self, event: wx.CommandEvent):
        payload_index = event.EventObject.payload_index

        print_info_msg(self._core.console, f'edit payload item @ index: {payload_index}')

    def set_pose(self, pose: Pose):
        """Parses the selected pose into the panel."""
        self._pose = pose

        self.DestroyChildren()
        self._init_layout()

        grid = wx.FlexGridSizer(len(pose.payload) * 2, 1, 0, 0)
        grid.AddGrowableCol(0, 0)

        for i, action in enumerate(pose.payload):
            delete_btn = wx.Button(self, label='Delete', size=self._BTN_SIZE, name='delete')
            delete_btn.payload_index = i
            delete_btn.Bind(wx.EVT_BUTTON, self._on_delete_payload_item)

            edit_btn = wx.Button(self, label='Edit', size=self._BTN_SIZE, name='edit')
            edit_btn.payload_index = i
            edit_btn.Bind(wx.EVT_BUTTON, self._on_edit_payload_item)

            caption = _get_payload_item_caption(action)

            crud_sizer = wx.BoxSizer(wx.HORIZONTAL)
            crud_sizer.AddMany([
                (edit_btn, 0, wx.EXPAND, 0),
                (delete_btn, 0, wx.EXPAND, 0)
            ])

            item_grid = wx.FlexGridSizer(1, 2, 0, 0)
            item_grid.AddGrowableCol(0, 0)
            item_grid.AddMany([
                (simple_statictext(self, caption), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
                (crud_sizer, 0, wx.EXPAND, 0)
            ])

            grid.AddMany([
                (wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.TOP, 1),
                (item_grid, 0, wx.EXPAND, 0)
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
        caption = 'Release shutter in'
        key, value = action.args[0]

        if key in time_args:
            caption = f'{caption} {value} {time_args[key]}{"s" if value != 1 else ""}'
        else:
            caption = f'{caption} {value} <invalid time unit>'

    return caption
