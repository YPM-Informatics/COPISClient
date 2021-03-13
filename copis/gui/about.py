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
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

import wx


class AboutDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title='About', pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.Size(200, 100), wx.DefaultSize)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        statictext = wx.StaticText(self, wx.ID_ANY, 'Under Construction', wx.DefaultPosition, wx.DefaultSize, 0)
        self.Sizer.Add(statictext, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

        self.Layout()

    def __del__(self):
          pass
