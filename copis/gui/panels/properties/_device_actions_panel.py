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

from copis.gui.wxutils import simple_statictext


class DeviceActionsPanel(wx.Panel):
    """Show device actions properties panel."""

    def __init__(self, parent) -> None:
        super().__init__(parent, style=wx.BORDER_NONE)
        self._parent = parent
        self._device = None

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Actions'), wx.VERTICAL)

        grid = wx.FlexGridSizer(4, 2, 0, 0)
        grid.AddGrowableCol(1, 0)

        grid.AddMany([
            (simple_statictext(self, 'Test:', 80), 0, wx.EXPAND, 0),
            (wx.StaticText(self, label='Coming soon...'), 0, wx.EXPAND, 0)
        ])

        box_sizer.Add(grid, 0, wx.ALL|wx.EXPAND, 5)
        self.Sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.Layout()
