import wx

class StatusBar(wx.StatusBar):
    def __init__(self, parent):
        super(StatusBar, self).__init__(parent)
        self.SetStatusText('Ready')


