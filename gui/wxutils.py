# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

"""wxPython util functions."""

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
