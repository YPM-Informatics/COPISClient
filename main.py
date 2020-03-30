#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import wx
import sys
from mainFrame import MainFrame
from camera import *

APP_EXIT = 1

class COPISApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None)
        self.frame.Show()
        return True

if __name__ == '__main__':
    app = COPISApp()
    app.MainLoop()

    #for camera in camera_models:
    #    del camera
    #
    #edsdk.EdsTerminateSDK()

