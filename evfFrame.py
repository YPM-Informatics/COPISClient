import wx

class EvfFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Live View")
        self.panel = wx.Panel(self, style = wx.BORDER_SUNKEN)
        self.initPanel()
        self.panel.SetFocus()
        self.Centre()

    def initPanel(self):
        playImg = wx.Image('img/play.png')
        self.image = wx.StaticBitmap(self.panel, bitmap = wx.Bitmap(playImg))