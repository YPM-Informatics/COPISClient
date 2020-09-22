#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main COPIS App (GUI)."""

import wx
import wx.lib.inspection

from appconfig import AppConfig
from copiscore import COPISCore
from gui.main_frame import MainFrame


class COPISApp(wx.App):
    """Main wxPython app.

    Initializes COPISCore and main frame.
    """

    mainframe = None

    def __init__(self, *args, **kwargs) -> None:
        super(COPISApp, self).__init__(*args, **kwargs)

        self.core = COPISCore()

        self.appconfig = None
        self.appconfig_exists = False
        self.init_appconfig()

        self.AppName = 'COPIS'
        self.locale = wx.Locale(wx.Locale.GetSystemLanguage())
        self.mainframe = MainFrame(
            None,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
            title='COPIS',
            size=(self.appconfig.config.getint('General', 'windowwidth'),
                  self.appconfig.config.getint('General', 'windowheight')))
        self.mainframe.Show()

    def init_appconfig(self) -> None:
        """Init AppConfig."""
        if self.appconfig is None:
            self.appconfig = AppConfig()

        self.appconfig_exists = self.appconfig.exists()
        if self.appconfig_exists:
            self.appconfig.load()

    def dark_mode(self) -> None:
        wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWFRAME)


if __name__ == '__main__':
    app = COPISApp()
    try:
        # debug window:
        # wx.lib.inspection.InspectionTool().Show()
        app.MainLoop()
    except KeyboardInterrupt:
        pass

    if app.mainframe.is_edsdk_on:
        app.mainframe.terminate_edsdk()

    del app
