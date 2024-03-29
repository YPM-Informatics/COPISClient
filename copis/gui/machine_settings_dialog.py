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

import wx


class MachineSettingsDialog(wx.Dialog):
    """Dialog TODO"""

    def __init__(self, parent, *args, **kwargs):
        """Initialize SettingsDialog with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Settings')
        self.parent = parent

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.Layout()
        self.Fit()
        # TODO: design settings interface
