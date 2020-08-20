"""Util functions."""

from functools import wraps
from time import time
from typing import Callable

import wx
import wx.svg as svg


def set_dialog(msg: str) -> None:
    """Show a wx.MessageDialog with msg as the message."""
    dialog = wx.MessageDialog(None, msg, 'Confirm Exit', wx.OK)
    dialog.ShowModal()
    dialog.Destroy()


def create_scaled_bitmap(bmp_name: str,
                         px_cnt: int = 16) -> wx.Bitmap:
    """Return scaled wx.Bitmap from svg file name.

    Args:
        bmp_name: A string representing the svg image to convert.
        px_cnt: Optional; Size to scale to, with aspect ratio 1. Defaults to 16.
    """
    image = svg.SVGimage.CreateFromFile(
        'img/' + bmp_name + '.svg').ConvertToScaledBitmap((px_cnt, px_cnt))
    return image


def timing(f: Callable) -> Callable:
    """Time a function."""
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print(
            f'func:{f.__name__} args:[{args}, {kw}] took: {(te-ts)*1000:.4f}ms')
        return result
    return wrap
