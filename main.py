#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TODO: Fill in docstring"""

import wx
from appconfig import AppConfig
from gui.main_frame import MainFrame


class COPISApp(wx.App):
    main_window = None

    def __init__(self, *args, **kwargs):
        super(COPISApp, self).__init__(*args, **kwargs)

        self.app_config = None
        self.app_config_exists = False
        self.init_app_config()

        self.SetAppName('COPIS')
        self.locale = wx.Locale(wx.Locale.GetSystemLanguage())
        self.main_window = MainFrame(
            None,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
            title='COPIS',
            size=(1200, 900))
        self.main_window.Show()

    def init_app_config(self):
        if self.app_config is None:
            self.app_config = AppConfig()

        self.app_config_exists = self.app_config.exists()
        if self.app_config_exists:
            self.app_config.load()


if __name__ == '__main__':
    app = COPISApp()
    try:
        app.MainLoop()
    except KeyboardInterrupt:
        pass

    if app.frame.is_edsdk_on:
        app.frame.terminateEDSDK()

    del app
