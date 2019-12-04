#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import wx
import sys
from mainFrame import MainFrame

APP_EXIT = 1

class COPISApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None)
        frame.Show()
        return True

if __name__ == '__main__':
    app = COPISApp()
    app.MainLoop()
