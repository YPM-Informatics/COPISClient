#!/usr/bin/env python3
"""TODO: Fill in docstring"""

import wx

class StatusBar(wx.StatusBar):
    def __init__(self, parent):
        super(StatusBar, self).__init__(parent)
        self.SetStatusText('Ready')

        # TODO: think about how to utilize status bar


