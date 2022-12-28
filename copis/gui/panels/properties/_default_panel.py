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


class DefaultPanel(wx.Panel):
    """Show default properties panel."""

    def __init__(self, parent) -> None:
        super().__init__(parent, style=wx.BORDER_NONE)
        self._parent = parent

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self._options_box_sizer = wx.StaticBoxSizer(
            wx.StaticBox(self, label='Options'), wx.VERTICAL)

        self._init_gui()

    def _init_gui(self):
        options_grid = wx.FlexGridSizer(1, 3, 0, 0)
        options_grid.AddGrowableCol(1, 0)



        self._options_box_sizer.Add(options_grid, 0, wx.ALL|wx.EXPAND, 5)
        self.Sizer.Add(self._options_box_sizer, 0, wx.ALL | wx.EXPAND, 5)

