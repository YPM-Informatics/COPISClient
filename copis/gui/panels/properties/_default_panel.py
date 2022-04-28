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

        self._save_session_dlg_opt = wx.CheckBox(self, label='&Use last save session choice',
            name='save_session_prompt')
        self._target_all_poses_opt = wx.CheckBox(self, label='&Apply target to all poses',
            name='apply_target')

        options_grid.AddMany([
            (self._save_session_dlg_opt, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 0),
            (0, 0),
            (self._target_all_poses_opt, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 0)
        ])

        self._options_box_sizer.Add(options_grid, 0, wx.ALL|wx.EXPAND, 5)
        self.Sizer.Add(self._options_box_sizer, 0, wx.ALL | wx.EXPAND, 5)

    @property
    def use_last_save_session_choice(self) -> bool:
        """Returns a flag indicating whether to prompt about saving the imaging session."""
        return self._save_session_dlg_opt.Value

    @property
    def apply_target_to_all_poses(self) -> bool:
        """Returns a flag indication whether to apply targetting to all poses."""
        return self._target_all_poses_opt.Value
