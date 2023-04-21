# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""COPIS device info properties panel."""

import wx

from copis.gui.wxutils import simple_statictext


class DeviceInfoPanel(wx.Panel):
    """Show device info properties panel."""

    def __init__(self, parent) -> None:
        super().__init__(parent, style=wx.BORDER_NONE)
        self._parent = parent
        self._device = None

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Info'), wx.VERTICAL)

        grid = wx.FlexGridSizer(4, 2, 0, 0)
        grid.AddGrowableCol(1, 0)

        self._id_text = wx.StaticText(self, label='')
        self._name_text = wx.StaticText(self, label='')
        self._type_text = wx.StaticText(self, label='')
        self._desc_text = wx.StaticText(self, label='')

        grid.AddMany([
            (simple_statictext(self, 'ID:', 80), 0, wx.EXPAND, 0),
            (self._id_text, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Type:', 80), 0, wx.EXPAND, 0),
            (self._type_text, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Name:', 80), 0, wx.EXPAND, 0),
            (self._name_text, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Description:', 80), 0, wx.EXPAND, 0),
            (self._desc_text, 0, wx.EXPAND, 0)
        ])

        box_sizer.Add(grid, 0, wx.ALL|wx.EXPAND, 5)
        self.Sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.Layout()

    def set_device(self, device):
        """Parses the selected device into the panel."""
        self._id_text.Label = str(device.device_id)
        self._name_text.Label = device.name
        self._type_text.Label = device.type
        self._desc_text.Label = device.description
