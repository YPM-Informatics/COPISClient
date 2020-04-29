import wx

class ConsolePanel(wx.Panel):
    def __init__(self, parent):
        super(ConsolePanel, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        hbox = wx.BoxSizer()
        self.console = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        hbox.Add(self.console, 1, wx.EXPAND)
        self.SetSizerAndFit(hbox)