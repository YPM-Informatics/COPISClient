#!/usr/bin/env python3

import wx


class AboutDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title='About', pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.Size(200, 100), wx.DefaultSize)

        sizer = wx.BoxSizer(wx.VERTICAL)

        statictext = wx.StaticText(self, wx.ID_ANY, 'Under Construction', wx.DefaultPosition, wx.DefaultSize, 0)
        sizer.Add(statictext, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()

    def __del__(self):
          pass
