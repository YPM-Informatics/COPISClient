#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main COPIS App (GUI)."""

import wx
import wx.lib.inspection

from appconfig import AppConfig
from copiscore import COPISCore
from gui.main_frame import MainWindow

import copisconsole
import copiscore

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
                  self.appconfig.config.getint('General', 'windowheight')))
        self.mainwindow.Show()

    def init_appconfig(self) -> None:
        """Init AppConfig."""
        if self.appconfig is None:
            self.appconfig = AppConfig()

        self.appconfig_exists = self.appconfig.exists()
        if self.appconfig_exists:
            self.appconfig.load()


if __name__ == '__main__':
    app = COPISApp()
    try:
        # debug window:
        # wx.lib.inspection.InspectionTool().Show()
        app.MainLoop()
    except KeyboardInterrupt:
        pass

    if app.c.edsdk_enabled:
        app.c.terminate_edsdk()

    del app
