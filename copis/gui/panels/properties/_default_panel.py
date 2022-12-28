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

from pydispatch import dispatcher

from copis.gui.wxutils import FancyTextCtrl, simple_statictext, EVT_FANCY_TEXT_UPDATED_EVENT
from copis.helpers import time_units


class DefaultPanel(wx.Panel):
    """Show default properties panel."""

    _TIME_UNIT = 'ms'
    _POST_SHUTTER_DELAY_KEY = 'post_shutter_delay_ms'
    _PRE_SHUTTER_DELAY_KEY = 'pre_shutter_delay_ms'

    def __init__(self, parent) -> None:
        super().__init__(parent, style=wx.BORDER_NONE)
        self._parent = parent
        self._core = parent.core

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self._options_box_sizer = wx.StaticBoxSizer(
            wx.StaticBox(self, label='Options'), wx.VERTICAL)

        self._init_gui()
        self._toggle_options(False)

        # Bind listeners.
        dispatcher.connect(self._toggle_options, signal='ntf_imaging_path_selection_changed')

        # Binds events.
        for ctrl in (self._pre_shutter_delay, self._post_shutter_delay):
            ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_ctrl_text_updated)

    def _on_optimize_pan_angles_btn_clicked(self, _):
        self._core.optimize_all_poses_pan_angles()

    def _on_ctrl_text_updated(self, event: wx.Event):
        ctrl = event.GetEventObject()
        self._core.project.update_imaging_option(ctrl.Name, ctrl.num_value)

    def _toggle_options(self, is_selected):
        self.Sizer.Show(0, is_selected)

        if is_selected:
            post_shutter_delay = 0
            pre_shutter_delay = 0

            if self._POST_SHUTTER_DELAY_KEY in self._core.project.options:
                post_shutter_delay = self._core.project.options[self._POST_SHUTTER_DELAY_KEY]

            if self._PRE_SHUTTER_DELAY_KEY in self._core.project.options:
                pre_shutter_delay = self._core.project.options[self._PRE_SHUTTER_DELAY_KEY]

            self._post_shutter_delay.num_value = post_shutter_delay
            self._pre_shutter_delay.num_value = pre_shutter_delay

        self.Sizer.RepositionChildren(self.Sizer.MinSize)
        self._parent.SetVirtualSize(self._parent.Sizer.MinSize)

    def _init_gui(self):
        shutter_delay_options_grid = wx.FlexGridSizer(2, 2, 0, 0)
        shutter_delay_options_grid.AddGrowableCol(0)

        pan_angles_options_grid = wx.FlexGridSizer(1, 1, 0, 0)
        pan_angles_options_grid.AddGrowableCol(0)

        self._post_shutter_delay = FancyTextCtrl(self, size=(80, -1), num_value=0,
            name=self._POST_SHUTTER_DELAY_KEY, default_unit=self._TIME_UNIT, unit_conversions=time_units)
        self._pre_shutter_delay = FancyTextCtrl(self, size=(80, -1), num_value=0,
            name=self._PRE_SHUTTER_DELAY_KEY, default_unit=self._TIME_UNIT, unit_conversions=time_units)
        self._optimize_pan_angles_btn = wx.Button(self, label='Optimize Pan Angles')
        self.Bind(wx.EVT_BUTTON, self._on_optimize_pan_angles_btn_clicked)

        shutter_delay_options_grid.AddMany([
            (simple_statictext(self, f'Post Shutter Delay ({self._TIME_UNIT}):', 80), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 20),
            (self._post_shutter_delay, 0, wx.EXPAND, 0),
            (simple_statictext(self, f'Pre Shutter Delay ({self._TIME_UNIT}):', 80), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 20),
            (self._pre_shutter_delay, 0, wx.EXPAND, 0)
        ])

        pan_angles_options_grid.Add(self._optimize_pan_angles_btn, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0)

        self._options_box_sizer.Add(shutter_delay_options_grid, 0, wx.ALL|wx.EXPAND, 5)
        self._options_box_sizer.Add(wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 0)
        self._options_box_sizer.Add(pan_angles_options_grid, 0, wx.TOP|wx.EXPAND, 3)

        self.Sizer.Add(self._options_box_sizer, 0, wx.ALL|wx.EXPAND, 5)
