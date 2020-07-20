#!/usr/bin/env python3

import wx
# from wx.lib.pubsub import Publisher


class PreferenceFrame(wx.Frame):
    def __init__(self, main_frame=None):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Preferences')
        self.main_frame = main_frame
        self.font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(15)

        self.init_panel()
        self.Centre()

    def init_panel(self):
        self.panel = wx.Panel(self, style=wx.BORDER_SUNKEN)

        self.vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.vbox1.Add((0,0))

        build_dims_box = wx.BoxSizer
        build_dims_label = wx.StaticText(self.panel, wx.ID_ANY, label='Set build dimensions', style=wx.ALIGN_LEFT)
        build_dims_label.SetFont(self.font)
        self.vbox1.Add(build_dims_label, 1, flag=wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

        self.panel.SetSizer(self.vbox1)