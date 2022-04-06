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
from copis.classes import Device

from copis.gui.wxutils import show_msg_dialog


class DeviceActionsPanel(wx.Panel):
    """Show device actions properties panel."""

    def __init__(self, parent) -> None:
        super().__init__(parent, style=wx.BORDER_NONE)
        self._parent = parent
        self._device = None

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Actions'), wx.VERTICAL)

        grid = wx.FlexGridSizer(4, 3, 0, 0)
        grid.AddGrowableCol(1, 0)

        self._live_view_btn = wx.Button(box_sizer.StaticBox, wx.ID_ANY, label='Live View')
        grid.Add(self._live_view_btn)
        self._live_view_btn.Bind(wx.EVT_BUTTON, self._on_live_view)

        box_sizer.Add(grid, 0, wx.ALL|wx.EXPAND, 5)
        self.Sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.Layout()

    def _on_live_view(self, _) -> None:
        self._parent.parent.remove_evf_pane()

        if self._parent.core.connect_edsdk(self._device.device_id):
            self._parent.parent.add_evf_pane()
        else:
            show_msg_dialog('Please connect the camera to start live view.', 'Start Live View')

    def set_device(self, device: Device) -> None:
        """Parses the selected device into the panel."""
        self._device = device
