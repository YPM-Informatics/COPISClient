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

"""COPIS Application GUI statistics panel."""

import wx
import wx.lib.scrolledpanel as scrolled

from pydispatch import dispatcher

from ._machine_stats import MachineStats
from ._path_stats import PathStats


class StatsPanel(scrolled.ScrolledPanel):
    """Stats panel. Shows various COPIS features' stats."""

    def __init__(self, parent) -> None:
        """Initialize StatsPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)

        self.parent = parent
        self.core = self.parent.core

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self._stats_panels = {}
        self._font = wx.Font(7, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_MAX, wx.FONTWEIGHT_BOLD)

        self.build_panels()

        self.SetupScrolling(scroll_x=False)
        self.Layout()

        # Bind listeners.
        dispatcher.connect(self.on_path_changed, signal='ntf_a_list_changed')

    @property
    def font(self):
        """Returns the stats panel font."""
        return self._font

    def _sync_path_stats_panel(self):
        is_shown = bool(self.core.project.pose_sets)

        if self._stats_panels['path_stats'].IsShown() != is_shown:
            self._stats_panels['path_stats'].Show(is_shown)

        self.Sizer.RepositionChildren(self.Sizer.MinSize)
        self.parent.update_right_dock()

    def build_panels(self) -> None:
        """Initialize all stats panels."""
        self._stats_panels['path_stats'] = PathStats(self)
        self._stats_panels['path_stats'].Hide()
        self._stats_panels['machine_stats'] = MachineStats(self)

        for _, panel in self._stats_panels.items():
            self.Sizer.Add(panel, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 0)

    def on_path_changed(self):
        """Handles path change event."""
        # Call the specified function after the current and pending event handlers have been completed.
        # This is good for making GUI method calls from non-GUI threads, in order to prevent hangs.
        wx.CallAfter(self._sync_path_stats_panel)
