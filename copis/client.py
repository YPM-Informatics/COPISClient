#!/usr/bin/env python3

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

"""Main COPIS App (GUI)."""

import wx
# TODO: good example of singleton: F12 on inspection.
import wx.lib.inspection

from .config import Config
from .core import COPISCore
from .gui.main_frame import MainWindow


class COPISApp(wx.App):
    """Main wxPython app.

    Initializes COPISCore and main frame.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.is_gui_loaded = False

        displays = (wx.Display(i) for i in range(wx.Display.GetCount()))
        main_d = next(filter(lambda d: d.IsPrimary, displays))
        display_size = main_d.GetGeometry().GetSize()

        self.config = Config(display_size)
        self.core = COPISCore(self)

        # pylint: disable=invalid-name
        self.AppName = 'COPIS Interface'
        dimensions_list = self._parse_chamber_dimensions()

        x, y, width, height = self.config.application_settings.window_geometry

        self.mainwindow = MainWindow(
            dimensions_list,
            None,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
            title='COPIS',
            pos=(x, y),
            size=(width, height)
        )
        self.mainwindow.Show()

        self.is_gui_loaded = True

    def _parse_chamber_dimensions(self) -> list:
        size = list(self.config.machine_settings.dimensions)
        origin = list(self.config.machine_settings.origin)

        dimensions = []
        dimensions.extend(size)
        dimensions.extend(origin)

        return dimensions
