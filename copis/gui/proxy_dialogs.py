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

"""Proxy object dialogs."""

import wx

from copis.gui.wxutils import (
    FancyTextCtrl, simple_statictext)
from copis.helpers import xyz_units


class ProxygenCylinder(wx.Dialog):
    """Dialog to generate a cylinder proxy object."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes ProxygenCylinder with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Cylinder Proxy Object', size=(200, -1))
        self.parent = parent

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        options_grid = wx.FlexGridSizer(7, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.start_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.start_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.start_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.end_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.end_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.end_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=100, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.radius_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=50, max_precision=0, default_unit='mm', unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Start X:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.start_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.start_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.start_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'End X:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.end_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.end_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.end_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Radius:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.radius_ctrl, 0, wx.EXPAND, 0),
        ])

        self.Sizer.Add(options_grid, 1, wx.ALL|wx.EXPAND, 4)
        self.Sizer.AddSpacer(8)

        # ---

        button_sizer = self.CreateStdDialogButtonSizer(0)
        self._affirmative_button = wx.Button(self, wx.ID_OK)
        # self._affirmative_button.Disable()
        button_sizer.SetAffirmativeButton(self._affirmative_button)
        button_sizer.SetCancelButton(wx.Button(self, wx.ID_CANCEL))
        button_sizer.Realize()

        self.Sizer.Add(button_sizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 4)

        self.Layout()
        self.SetMinSize((200, -1))
        self.Fit()

class ProxygenAABB(wx.Dialog):
    """Dialog to generate an axis-aligned box proxy object."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes ProxygenAABB with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Box Proxy Object', size=(250, -1))
        self.parent = parent

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        options_grid = wx.FlexGridSizer(6, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.lower_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=-50, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.lower_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=-50, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.lower_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.upper_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=50, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.upper_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=50, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.upper_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=100, max_precision=0, default_unit='mm', unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Lower Corner X:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.lower_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lower_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lower_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Upper Corner X:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.upper_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.upper_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.upper_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
        ])

        self.Sizer.Add(options_grid, 1, wx.ALL|wx.EXPAND, 4)
        self.Sizer.AddSpacer(8)

        # ---

        button_sizer = self.CreateStdDialogButtonSizer(0)
        self._affirmative_button = wx.Button(self, wx.ID_OK)
        # self._affirmative_button.Disable()
        button_sizer.SetAffirmativeButton(self._affirmative_button)
        button_sizer.SetCancelButton(wx.Button(self, wx.ID_CANCEL))
        button_sizer.Realize()

        self.Sizer.Add(button_sizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 4)

        self.Layout()
        self.SetMinSize((250, -1))
        self.Fit()
