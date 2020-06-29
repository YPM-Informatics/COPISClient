import wx

class ConsolePanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(ConsolePanel, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.console = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.console, 1, wx.EXPAND)

        self.writer = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.writer.Bind(wx.EVT_TEXT_ENTER, self.onPublishCmd)
        vbox.Add(self.writer, 0.5, wx.EXPAND)
        self.SetSizerAndFit(vbox)

    def onPublishCmd(self, event):
        self.console.AppendText(">>" + event.String + "\n")
        self.writer.SetValue("")

    def print(self, msg):
        self.console.AppendText(msg + "\n")