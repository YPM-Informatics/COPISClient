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
        super(COPISApp, self).__init__(*args, **kwargs)
        self.core = COPISCore()
        self.config = Config()

        # pylint: disable=invalid-name
        self.AppName = 'COPIS Interface'
        self.mainwindow = MainWindow(
            # self.chamberdims,
            None,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
            title='COPIS',
            size=(self.config.settings.app_window_width, self.config.settings.app_window_height)
        )
        self.mainwindow.Show()
