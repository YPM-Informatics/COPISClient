#!/usr/bin/env python3

import wx


def set_dialog(msg):
    dialog = wx.MessageDialog(None, msg, 'Confirm Exit', wx.OK)
    dialog.ShowModal()
    dialog.Destroy()
