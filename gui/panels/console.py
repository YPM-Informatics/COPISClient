"""TODO"""

import wx


class ConsolePanel(wx.Panel):
    """TODO"""

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits ConsolePanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)

        self.parent = parent
        self.init_gui()

    def init_gui(self) -> None:
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.console = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_CHARWRAP)
        vbox.Add(self.console, 1, wx.EXPAND)

        self.writer = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)


        self.writer.Bind(wx.EVT_TEXT_ENTER, self.on_command_entered)
        vbox.Add(self.writer, 0.5, wx.EXPAND)
        self.SetSizerAndFit(vbox)

    def on_command_entered(self, event) -> None:
        """On EVT_TEXT_ENTER, process entered console command."""
        if not event.String:
            return
        self.console.AppendText(f'$ {event.String}\n')
        self.writer.ChangeValue('')

    def print(self, msg) -> None:
        self.console.AppendText(msg + '\n')
