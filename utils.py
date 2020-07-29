#!/usr/bin/env python3

import wx
import wx.svg as svg


def set_dialog(msg):
    dialog = wx.MessageDialog(None, msg, 'Confirm Exit', wx.OK)
    dialog.ShowModal()
    dialog.Destroy()


def create_scaled_bitmap(bmp_name, px_cnt=16):
    image = svg.SVGimage.CreateFromFile('img/' + bmp_name + '.svg').ConvertToScaledBitmap((px_cnt, px_cnt))
    return image
