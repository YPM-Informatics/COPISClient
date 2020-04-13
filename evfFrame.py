import wx

class EvfFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Live View")
        self.Centre()

    def onDrawImage(self, data):
        #playImg = wx.Image('img/play.png')
        self.image = wx.Bitmap().FromBuffer(self.Size.GetWidth(), self.Size.GetHeight(), data)

        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.image)