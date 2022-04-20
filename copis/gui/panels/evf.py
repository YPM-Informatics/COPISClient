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

import io
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
        self.timer = wx.CallLater(10, self._update)

        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_LEFT_DCLICK, self._on_left_dclick)

        self._parent.core.start_edsdk_live_view()
        self._update()

    def _update(self):
        if self:
            if self._parent.core.is_edsdk_connected:
                self.Refresh()
                self.Update()
                self.timer.Start()
            else:
                self._parent.remove_evf_pane()

    def _get_bitmap(self):
        img_bytes = self._parent.core.download_edsdk_evf_data()

        if img_bytes:
            img = Image.open(io.BytesIO(img_bytes))
            img = img.resize(self.Size)
            width, height = img.size
            buffer = img.convert('RGB').tobytes()
            bitmap = wx.Bitmap.FromBuffer(width, height, buffer)
            return bitmap

        return None

    def _on_paint(self, _):
        bitmap = self._get_bitmap()
        if bitmap:
            dc = wx.AutoBufferedPaintDC(self)
            dc.DrawBitmap(bitmap, 0, 0)

    def _on_left_dclick(self, _):
        self._parent.core.do_edsdk_focus()

    def on_close(self):
        """Handles EVF panel close event."""
        self.timer.Stop()
        self._parent.core.end_edsdk_live_view()
        self._parent.core.disconnect_edsdk()
