"""TODO"""

import wx
from pydispatch import dispatcher

from gui.wxutils import create_scaled_bitmap
from utils import Point5


class ConsolePanel(wx.Panel):
    """TODO"""

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits ConsolePanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.console = None
        self.console_writer = None

        self.init_gui()

        self.Layout()

        # bind copiscore listeners
        dispatcher.connect(self.on_notification, signal='core_point_list_changed')
        dispatcher.connect(self.on_notification, signal='core_device_list_changed')
        dispatcher.connect(self.on_notification, signal='core_point_selected')
        dispatcher.connect(self.on_notification, signal='core_point_deselected')
        dispatcher.connect(self.on_notification, signal='core_device_selected')
        dispatcher.connect(self.on_notification, signal='core_device_deselected')
        dispatcher.connect(self.on_notification, signal='core_error')

    def init_gui(self) -> None:
        self.console = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CHARWRAP)
        self.Sizer.Add(self.console, 1, wx.EXPAND)

        command_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.console_writer = wx.TextCtrl(self, size=(-1, 22), style=wx.TE_PROCESS_ENTER)
        self.console_writer.Bind(wx.EVT_TEXT_ENTER, self.on_command_entered)
        clear_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('clear'), size=(-1, -1))
        clear_btn.Bind(wx.EVT_BUTTON, self.on_command_cleared)

        command_sizer.AddMany([
            (self.console_writer, 1, 0, 0),
            (clear_btn, 0, wx.ALL, -1),
        ])

        self.Sizer.Add(command_sizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 2)

    def on_command_entered(self, event: wx.CommandEvent) -> None:
        """On EVT_TEXT_ENTER, process entered console command."""
        if not event.String:
            return

        self.console.AppendText(f'\n$ {event.String}')
        self.console_writer.ChangeValue('')

        wx.GetApp().core.select_point(int(event.String))

    def on_command_cleared(self, event: wx.CommandEvent) -> None:
        self.console_writer.ChangeValue('')

    def print(self, msg: str) -> None:
        self.console.AppendText(f'\n{msg}')

    def on_notification(self, signal: str, message: str = '') -> None:
        self.print(f'notification: {signal} {message}')
