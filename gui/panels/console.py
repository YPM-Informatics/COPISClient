"""ConsolePanel class."""

import wx
from pydispatch import dispatcher

from gui.wxutils import create_scaled_bitmap
from utils import Point5


class ConsolePanel(wx.Panel):
    """Console panel.

    Args:
        parent: Pointer to a parent wx.Frame.
    """

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits ConsolePanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self.c = self.parent.c

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self._console = None
        self._console_writer = None

        self.init_gui()
        self.Layout()

        # bind copiscore listeners
        dispatcher.connect(self.on_notification, signal='core_a_list_changed')
        dispatcher.connect(self.on_notification, signal='core_d_list_changed')
        dispatcher.connect(self.on_notification, signal='core_p_selected')
        dispatcher.connect(self.on_notification, signal='core_p_deselected')
        dispatcher.connect(self.on_notification, signal='core_d_selected')
        dispatcher.connect(self.on_notification, signal='core_d_deselected')
        dispatcher.connect(self.on_notification, signal='core_error')
        dispatcher.connect(self.on_notification, signal='core_message')
        dispatcher.connect(self.on_action_export, signal='core_a_exported')

    def init_gui(self) -> None:
        """Initialize gui elements."""
        self._console = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CHARWRAP)
        self.Sizer.Add(self._console, 1, wx.EXPAND)

        command_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._console_writer = wx.TextCtrl(self, size=(-1, 22), style=wx.TE_PROCESS_ENTER)
        self._console_writer.Hint = 'Enter a command...'
        self._console_writer.Bind(wx.EVT_TEXT_ENTER, self.on_command_entered)
        clear_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('clear'), size=(-1, -1))
        clear_btn.Bind(wx.EVT_BUTTON, self.on_command_cleared)

        command_sizer.AddMany([
            (self._console_writer, 1, 0, 0),
            (clear_btn, 0, wx.ALL, -1),
        ])

        self.Sizer.Add(command_sizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 2)

    def on_command_entered(self, event: wx.CommandEvent) -> None:
        """On EVT_TEXT_ENTER, process entered console command.

        Currently only selects camera if entered a valid id.
        TODO: When implemented, connect to actual console or some parser.
        """
        if not event.String:
            return

        self.print(f'$ {event.String}')
        self.on_command_cleared()

        self.c.select_device(int(event.String))

    def on_command_cleared(self, event: wx.CommandEvent = None) -> None:
        """When the clear button is pressed, clear the console writer."""
        self._console_writer.ChangeValue('')

    def print(self, msg: str) -> None:
        """Add message to console."""
        self._console.AppendText(f'{msg}\n')

    def on_notification(self, signal: str, message: str = '') -> None:
        """Print any pydispatch signals."""
        self.print(f'notification: {signal} {message}')

    def on_action_export(self, filename: str) -> None:
        self.print(f'Exported actions to file {filename}')
