#!/usr/bin/env python3

import wx

class StatusBar(wx.StatusBar):
    def __init__(self, parent, *args, **kwargs):
        super(StatusBar, self).__init__(parent)
        self.SetStatusText('Ready')
        # TODO: think about how to utilize status bar
