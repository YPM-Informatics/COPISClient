"""EvfPanel class."""

import io
import wx
from PIL import Image


class EvfPanel(wx.Panel):
    """Electronic viewfinder panel. Shows live feed of connected camera.

    Args:
        parent: Pointer to a parent wx.Frame.
    """

    def __init__(self, parent, *args, **kwargs):
        """Inits EvfPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT, size=wx.Size(600, 420))
        self.parent = parent
        self.timer = wx.CallLater(15, self.update)

        self.BackgroundStyle = wx.BG_STYLE_CUSTOM
        self.Bind(wx.EVT_PAINT, self.on_paint)

        self.cam = self.parent.get_selected_camera()
        self.cam.connect()
        self.cam.startEvf()

        self.update()

    def update(self):
        self.cam.download_evf()
        self.Refresh()
        self.Update()
        self.timer.Start()

    def get_bitmap(self):
        # self.cam.download_evf()
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

    def on_destroy(self):
        self.cam.end_evf()
        self.timer.Stop()
