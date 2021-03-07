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

"""EvfPanel class."""

import io
import wx
from PIL import Image


class EvfPanel(wx.Panel):
    """Electronic viewfinder panel. Shows live feed of connected device.

    Args:
        parent: Pointer to a parent wx.Frame.
    """

    def __init__(self, parent, *args, **kwargs):
        """Inits EvfPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT, size=wx.Size(600, 420))
        self.parent = parent
        self.c = self.parent.c
        # self.timer = wx.CallLater(10, self.update)

        self.BackgroundStyle = wx.BG_STYLE_CUSTOM
        # self.Bind(wx.EVT_PAINT, self.on_paint)

        self.c.edsdk.connect(0)

        # self.update()

    def update(self):
        self.Refresh()
        self.Update()
        self.timer.Start()

    def get_bitmap(self):
        self.cam.download_evf()
        if self.cam.img_byte_data:
            img = (Image.open(io.BytesIO(self.cam.img_byte_data)))
            img.resize(self.Size)
            width, height = img.size
            buffer = img.convert('RGB').tobytes()
            bitmap = wx.Bitmap.FromBuffer(width, height, buffer)
            return bitmap
        return None

    def on_paint(self, event):
        bitmap = self.get_bitmap()
        dc = wx.AutoBufferedPaintDC(self)
        dc.DrawBitmap(bitmap, 0, 0)

    def on_close(self):
        # self.cam.end_evf()
        self.c.edsdk.end_evf()
        self.timer.Stop()
