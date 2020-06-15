#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TODO: Fill in docstring"""

import wx
from frames.mainFrame import MainFrame

APP_EXIT = 1


class COPISApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None)
        self.frame.Show()
        return True


if __name__ == '__main__':
    app = COPISApp()
    app.MainLoop()

    if app.frame.is_edsdk_on:
        app.frame.terminateEDSDK()
