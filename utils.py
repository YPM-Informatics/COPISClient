#!/usr/bin/env python3

from functools import wraps
from time import time

import wx
import wx.svg as svg


def set_dialog(msg):
    dialog = wx.MessageDialog(None, msg, 'Confirm Exit', wx.OK)
    dialog.ShowModal()
    dialog.Destroy()


def create_scaled_bitmap(bmp_name, px_cnt=16):
    image = svg.SVGimage.CreateFromFile('img/' + bmp_name + '.svg').ConvertToScaledBitmap((px_cnt, px_cnt))
    return image


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print(f'func:{f.__name__} args:[{args}, {kw}] took: {(te-ts)*1000:.4f}ms')
        return result
    return wrap
