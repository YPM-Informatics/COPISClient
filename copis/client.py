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
        self.config = Config()
        self.core = COPISCore(self)

        # pylint: disable=invalid-name
        self.AppName = 'COPIS Interface'
        dims_list = self._parse_chamber_dimensions()

        self.mainwindow = MainWindow(
            dims_list,
            None,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
            title='COPIS',
            size=(self.config.settings.app_window_width, self.config.settings.app_window_height)
        )
        self.mainwindow.Show()

    def _parse_chamber_dimensions(self) -> list:
        _STACK_INDEX = 2

        sizes = [c.dimensions.to_list() for c in self.config.machine_settings.chambers]
        origins = [c.dimensions.get_origin() for c in self.config.machine_settings.chambers]

        size = sizes[0]
        origin = origins[0]

        if len(sizes) > 1:
            size_sum = [sum(s) for s in zip(*sizes)]
            origin_sum = [sum(s) for s in zip(*origins)]

            # Z stack the chambers
            size[_STACK_INDEX] = size_sum[_STACK_INDEX]
            origin[_STACK_INDEX] = origin_sum[_STACK_INDEX]
        else:
            origin[_STACK_INDEX] = 0

        size.extend(origin)
        return size
