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

"""COPIS machine info properties panel."""

import wx


class MachineInfo(wx.Panel):
    """Show information related to the machine, in the properties panel."""

    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Machine info'), wx.VERTICAL)

        machine_grid = wx.FlexGridSizer(2, 2, 2, 6)
        machine_grid.AddGrowableCol(1, 0)

        devices = self.parent.core.project.devices
        device_grid = wx.FlexGridSizer(6, len(devices), 0, 0)
        device_grid.AddGrowableCol(0, 0)
