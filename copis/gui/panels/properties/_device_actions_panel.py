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

"""COPIS device actions properties panel."""

import wx

from pydispatch import dispatcher

from copis.classes import Device
from copis.globals import ToolIds
from copis.gui.wxutils import prompt_for_imaging_session_path, show_msg_dialog
from copis.store import path_exists


class DeviceActionsPanel(wx.Panel):
    """Show device actions properties panel."""

    def __init__(self, parent) -> None:
        super().__init__(parent, style=wx.BORDER_NONE)
        self._parent = parent
        self._device = None

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self._serial_box_sizer = wx.StaticBoxSizer(
            wx.StaticBox(self, label='Serial Actions'), wx.VERTICAL)
        self._edsdk_box_sizer = wx.StaticBoxSizer(
            wx.StaticBox(self, label='EDSDK Actions'), wx.VERTICAL)

        self._init_gui()

        # Bind listeners.
        dispatcher.connect(self._on_device_homed, signal='ntf_device_homed')

        # Bind events.
        self._start_live_view_btn.Bind(wx.EVT_BUTTON, self._on_start_live_view)
        self._edsdk_take_pic_btn.Bind(wx.EVT_BUTTON, self._on_snap_edsdk_picture)
        self._serial_take_pic_btn.Bind(wx.EVT_BUTTON, self._on_snap_serial_picture)
        self._edsdk_transfer_pics_btn.Bind(wx.EVT_BUTTON, self._on_transfer_edsdk_pictures)
        self._edsdk_step_focus_near_btn.Bind(wx.EVT_BUTTON, self._on_edsdk_focus)
        self._edsdk_step_focus_far_btn.Bind(wx.EVT_BUTTON, self._on_edsdk_focus)

    def _init_gui(self):
        edsdk_grid = wx.FlexGridSizer(2, 3, 0, 0)
        self._serial_grid = wx.FlexGridSizer(1, 3, 0, 0)
        for i in range(3):
            edsdk_grid.AddGrowableCol(i, 0)
            if i != 1:
                self._serial_grid.AddGrowableCol(i, 0)

        self._start_live_view_btn = wx.Button(
            self._edsdk_box_sizer.StaticBox, wx.ID_ANY, label='Start Live View')
        self._edsdk_transfer_pics_btn = wx.Button(
            self._edsdk_box_sizer.StaticBox, wx.ID_ANY, label='Transfer Pictures')

        edsdk_shot_ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._edsdk_take_pic_btn = wx.Button(self._edsdk_box_sizer.StaticBox, wx.ID_ANY,
            label='Snap a Shot', size=(70, -1))
        self._af_option = wx.CheckBox(self._edsdk_box_sizer.StaticBox, wx.ID_ANY,
            label='AF')
        self._af_option.Value = True
        edsdk_shot_ctrl_sizer.AddMany([
            (self._edsdk_take_pic_btn, 0, wx.EXPAND, 0),
            (self._af_option, 0, wx.EXPAND, 0)
        ])

        self._edsdk_step_focus_near_btn = wx.Button(self._edsdk_box_sizer.StaticBox,
            wx.ID_ANY, label='Focus Near', name='near_focus')
        self._edsdk_step_focus_far_btn = wx.Button(self._edsdk_box_sizer.StaticBox,
            wx.ID_ANY, label='Focus Far', name='far_focus')
        self._edsdk_focus_step_choice = wx.SpinCtrl(
            self._edsdk_box_sizer.StaticBox, wx.ID_ANY, min=1, max=3, initial=1,
            name='focus_step')

        serial_shot_ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._serial_take_pic_btn = wx.Button(self._serial_box_sizer.StaticBox, wx.ID_ANY,
            label='Snap a Shot', size=(70, -1))
        self._shutter_release_times = wx.SpinCtrlDouble(self._serial_box_sizer.StaticBox,
            wx.ID_ANY, min=0, max=5, initial=0, inc=.1, size=(45, -1))
        serial_shot_ctrl_sizer.AddMany([
            (self._serial_take_pic_btn, 0, wx.EXPAND, 0),
            (self._shutter_release_times, 0, wx.EXPAND, 0)
        ])
        self._serial_take_pic_btn.Disable()
        self._shutter_release_times.Disable()

        edsdk_grid.AddMany([
            (self._start_live_view_btn, 0, wx.EXPAND, 0),
            (edsdk_shot_ctrl_sizer, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 0),
            (self._edsdk_transfer_pics_btn, 0, wx.EXPAND, 0),
            (self._edsdk_step_focus_near_btn, 0, wx.EXPAND, 0),
            (self._edsdk_focus_step_choice, 0,
                wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0),
            (self._edsdk_step_focus_far_btn, 0, wx.EXPAND, 0)
        ])

        self._serial_grid.AddMany([
            (0, 0),
            (serial_shot_ctrl_sizer, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 0),
            (0, 0)
        ])

        self._edsdk_box_sizer.Add(
            edsdk_grid, 0, wx.LEFT|wx.TOP|wx.RIGHT|wx.EXPAND, 5)
        self._serial_box_sizer.Add(
            self._serial_grid, 0, wx.LEFT|wx.BOTTOM|wx.RIGHT|wx.EXPAND, 5)
        self.Sizer.Add(self._serial_box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.Sizer.Add(self._edsdk_box_sizer, 0, wx.ALL|wx.EXPAND, 5)

        self.Layout()

    def _on_edsdk_focus(self, event: wx.CommandEvent) -> None:
        if self._parent.parent.evf_panel:
            name = event.EventObject.Name
            step = int(self._edsdk_focus_step_choice.Value)

            if name == 'near_focus':
                step = -(step)

            self._parent.core.edsdk_step_focus(step)
        else:
            show_msg_dialog('Please start live view before stepping focus.',
                'Step Focus')

    def _on_start_live_view(self, _) -> None:
        self._parent.parent.remove_evf_pane()

        if self._parent.core.connect_edsdk(self._device.device_id):
            self._parent.parent.add_evf_pane()
        else:
            show_msg_dialog('Please connect the camera to start live view.',
                'Start Live View')

    def _on_snap_edsdk_picture(self, event: wx.CommandEvent) -> None:
        if self._parent.core.connect_edsdk(self._device.device_id):
            if self._parent.use_last_save_session_choice:
                proceed = True
                path = self._parent.core.imaging_session_path
                keep_last = self._parent.Parent.keep_last_session_imaging_path
            else:
                proceed, path, keep_last = prompt_for_imaging_session_path(
                    self._parent.core.imaging_session_path)
                self._parent.Parent.keep_last_session_imaging_path = keep_last

            if not proceed:
                return

            pos = event.GetEventObject().GetScreenPosition()

            def snap_shot_handler():
                self._parent.core.snap_edsdk_picture(self._af_option.Value, path, keep_last)
                self._parent.Parent.hide_imaging_toolbar()

            actions = [(ToolIds.SNAP_SHOT, True, snap_shot_handler)]
            self._parent.Parent.show_imaging_toolbar(pos, actions)
        else:
            show_msg_dialog('Please connect the camera to take a picture via EDSDK.',
                'Take a Picture - EDSDK')

    def _on_snap_serial_picture(self, event: wx.CommandEvent) -> None:
        can_snap = self._parent.core.is_serial_port_connected

        if can_snap:
            if self._parent.use_last_save_session_choice:
                proceed = True
                path = self._parent.core.imaging_session_path
                keep_last = self._parent.Parent.keep_last_session_imaging_path
            else:
                proceed, path, keep_last = prompt_for_imaging_session_path(
                    self._parent.core.imaging_session_path)
                self._parent.Parent.keep_last_session_imaging_path = keep_last

            if not proceed:
                return

            pos = event.GetEventObject().GetScreenPosition()
            shutter_release_time = max(0, float(self._shutter_release_times.Value))

            def snap_shot_handler():
                self._parent.core.snap_serial_picture(shutter_release_time,
                    self._device.device_id, path, keep_last)
                self._parent.Parent.hide_imaging_toolbar()

            actions = [(ToolIds.SNAP_SHOT, True, snap_shot_handler)]
            self._parent.Parent.show_imaging_toolbar(pos, actions)
        else:
            show_msg_dialog('Please connect the machine to take a picture via serial.',
                'Take a Picture - Serial')

    def _on_transfer_edsdk_pictures(self, _) -> None:
        if self._parent.core.connect_edsdk(self._device.device_id):
            if self._parent.use_last_save_session_choice:
                proceed = True
                path = self._parent.core.imaging_session_path
                keep_last = self._parent.Parent.keep_last_session_imaging_path
            else:
                proceed, path, keep_last = prompt_for_imaging_session_path(
                    self._parent.core.imaging_session_path)
                self._parent.Parent.keep_last_session_imaging_path = keep_last

            if not proceed:
                return

            if not path:
                show_msg_dialog('Please provide a destination folder for the pictures.',
                    'Transfer Pictures - EDSDK')
            elif not path_exists(path):
                show_msg_dialog(f'Destination folder {path} does not exist.',
                    'Transfer Pictures - EDSDK')
            else:
                label = self._edsdk_transfer_pics_btn.Label
                self._edsdk_transfer_pics_btn.Label = 'Transferring...'
                self._edsdk_transfer_pics_btn.Disable()

                try:
                    self._parent.core.transfer_edsdk_pictures(path, keep_last)
                finally:
                    wx.GetApp().Yield()
                    self._edsdk_transfer_pics_btn.Enable()
                    self._edsdk_transfer_pics_btn.Label = label
        else:
            show_msg_dialog('Please connect the camera to transfer pictures via EDSDK.',
                'Transfer Pictures - EDSDK')

    def _on_device_homed(self):
        self._serial_take_pic_btn.Enable()
        self._shutter_release_times.Enable()

    def set_device(self, device: Device) -> None:
        """Parses the selected device into the panel."""
        self._device = device
