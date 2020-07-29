#!/usr/bin/env python3

import wx


class SettingsFrame(wx.Frame):
    def __init__(self, parent, *args, **kwargs):
        super(SettingsFrame, self).__init__(parent, wx.ID_ANY, 'Settings')
        # TODO: design settings interface
