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

import logging
import signal

import wx
import wx.lib.inspection

import copisconsole
import copiscore
from appconfig import AppConfig
from copiscore import COPISCore
from gui.main_frame import MainWindow

# class COPISWindow(MainWindow, copisconsole.COPISConsole):
#     def __init__(self, *args, **kwargs):
#         copisconsole.COPISConsole.__init__(self)
#         MainWindow.__init__(self, *args, **kwargs)


class COPISApp(wx.App):
    """Main wxPython app.

    Initializes COPISCore and main frame.
    """

    mainwindow = None

    def __init__(self, *args, **kwargs) -> None:
        super(COPISApp, self).__init__(*args, **kwargs)
        self.c = COPISCore()
        self.appconfig = None
        self.appconfig_exists = False
        self.init_appconfig()

        self.AppName = 'COPIS Interface'
        self.locale = wx.Locale(wx.Locale.GetSystemLanguage())
        self.mainwindow = MainWindow(
            None,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
            title='COPIS',
            size=(self.appconfig.config.getint('General', 'windowwidth'),
                  self.appconfig.config.getint('General', 'windowheight'))
        )
        self.mainwindow.Show()

    def init_appconfig(self) -> None:
        """Init AppConfig."""
        if self.appconfig is None:
            self.appconfig = AppConfig()

        self.appconfig_exists = self.appconfig.exists()
        if self.appconfig_exists:
            self.appconfig.load()


if __name__ == '__main__':

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    app = COPISApp()
    try:
        # wx.lib.inspection.InspectionTool().Show() # debug
        app.MainLoop()
    except KeyboardInterrupt:
        print("helo")
        pass

    app.c.terminate_edsdk()
    del app
