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
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""EvfPanel class."""

from concurrent.futures import thread
import io
import time
import wx
from PIL import Image


class EvfPanel(wx.Panel):
    """Electronic viewfinder panel. Shows live feed of connected device.

    Args:
        parent: Pointer to a parent wx.Frame.
    """

    def __init__(self, parent, *args, **kwargs):
        """Initializes EvfPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_THEME, *args, **kwargs)
        self._parent = parent
        self.BackgroundStyle = wx.BG_STYLE_CUSTOM
        self.timer = wx.CallLater(10, self.update)

        self.Bind(wx.EVT_PAINT, self.on_paint)

        self._parent.core._edsdk.start_liveview()
        self.update()

    def update(self):
        if self:
            self.Refresh()
            self.Update()
            self.timer.Start()

    def get_bitmap(self):
        img_bytes = self._parent.core._edsdk.download_evf_data()
        if img_bytes:
            img = Image.open(io.BytesIO(img_bytes))
            img = img.resize(self.Size)
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
        self.timer.Stop()
        self._parent.core._edsdk.end_liveview()
        self._parent.core._edsdk.disconnect()
