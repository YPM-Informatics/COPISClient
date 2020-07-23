#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TODO: Fill in docstring"""

import wx
from gui.main_frame import MainFrame


class COPISApp(wx.App):
    main_window = None

    def __init__(self, *args, **kwargs):
        super(COPISApp, self).__init__(*args, **kwargs)
        self.SetAppName('COPIS')
        self.locale = wx.Locale(wx.Locale.GetSystemLanguage())
        self.main_window = MainFrame(
            None,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
            title='COPIS',
            size=(1000, 900))
        self.main_window.Show()


if __name__ == '__main__':
    app = COPISApp()
    try:
        app.MainLoop()
    except KeyboardInterrupt:
        pass

    if app.frame.is_edsdk_on:
        app.frame.terminateEDSDK()

    del app
