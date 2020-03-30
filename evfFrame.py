import wx

class evfFrame(wx.Frame):
    def __init__(self):
        super(MainFrame, self).__init__(style = wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE, title = "Live View")

        self.panel = wx.Panel(self, style = wx.BORDER_SUNKEN)
        self.initPanel()
        self.panel.SetFocus()
        self.Centre()

    def initPanel(self):
        pass