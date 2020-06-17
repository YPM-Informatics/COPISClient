import wx
from PIL import Image
import io

class EvfPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(EvfPanel, self).__init__(parent, wx.ID_ANY, size=wx.Size(600, 420))
        self.parent = parent
        self.timer = wx.CallLater(15, self.update)
        self.cam =  self.parent.cam_list.selected_camera
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.update()

    def update(self):
        self.cam.download_evf()
        self.Refresh()
        self.Update()
        self.timer.Start()

    def get_bitmap(self):
        if  self.cam.img_byte_data:
            img = (Image.open(io.BytesIO(self.cam.img_byte_data)))
            img.resize(self.GetSize())
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