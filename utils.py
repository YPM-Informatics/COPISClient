#!/usr/bin/env python3

import wx
import wx.svg as svg

def set_dialog(msg):
    dialog = wx.MessageDialog(None, msg, 'Confirm Exit', wx.OK)
    dialog.ShowModal()
    dialog.Destroy()


def svgbmp(svgimg, size):
    # size = 64
    image = svg.SVGimage.CreateFromFile(svgimg).ConvertToScaledBitmap((size, size))
    return image
