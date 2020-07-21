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

        # Build settings box
        build_settings_box = wx.BoxSizer(wx.VERTICAL)
        build_settings_label = wx.StaticText(self.panel, wx.ID_ANY, label='Customize your build settings', style=wx.ALIGN_LEFT)
        build_settings_label.SetFont(self.font)
        build_settings_box.Add(build_settings_label, 1, flag=wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

        # Dimensions Box
        dims_box = wx.BoxSizer(wx.VERTICAL)
        dims_label = wx.StaticText(self.panel, wx.ID_ANY, label='Dimensions', style=wx.ALIGN_LEFT)
        dims_box.Add(dims_label, 1, flag = wx.BOTTOM, border=5)

        width_box = wx.BoxSizer()
        width_label = wx.StaticText(self.panel, wx.ID_ANY, label='Width: ')
        width_box.Add(width_label)
        self.width_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        width_box.Add(self.width_sc)

        length_box = wx.BoxSizer()
        length_label = wx.StaticText(self.panel, wx.ID_ANY, label='Length: ')
        length_box.Add(length_label)
        self.length_sc= wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        length_box.Add(self.length_sc)

        height_box = wx.BoxSizer()
        height_label =  wx.StaticText(self.panel, wx.ID_ANY, label='Height: ')
        height_box.Add(height_label)
        self.height_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        height_box.Add(self.height_sc)

        dims_box.Add(width_box)
        dims_box.Add(length_box)
        dims_box.Add(height_box)

        # Origin Box


        build_settings_box.Add(dims_box)

        self.vbox1.Add(build_settings_box, 1)

        self.panel.SetSizer(self.vbox1)