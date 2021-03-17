# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

"""ConsolePanel class."""

import shlex

import wx
from gui.wxutils import create_scaled_bitmap
from pydispatch import dispatcher


class ConsolePanel(wx.Panel):
    """Console panel.

    Args:
        parent: Pointer to a parent wx.Frame.
    """

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits ConsolePanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self.core = self.parent.core

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
        """Parse and process entered console command.

        Can connect, disconnect, and image devices.
        """
        cmd = event.String

        if not cmd:
            return

        self.print(f'$ {cmd}')
        self.on_command_cleared()

        try:
            # try parsing command
            argv = shlex.split(cmd)
            argc = len(argv)
        except Exception as e:
            self.print(f'invalid command: {e}')
            return

        # NOTE: this is temporary, just a way to test edsdk functions.
        if argv[0] == 'connect':
            if argc == 2 and argv[1].isdigit():
                self.core.edsdk.connect(int(argv[1]))
            elif argc == 1:
                self.core.edsdk.connect()
            else:
                self.print('usage: connect [INDEX]')

        elif argv[0] == 'disconnect':
            if argc == 1:
                self.core.edsdk.disconnect()
            else:
                self.print('usage: disconnect')

        elif argv[0] == 'shoot':
            if argc == 2 and argv[1].isdigit():
                if self.core.edsdk.connect(int(argv[1])):
                    self.core.edsdk.take_picture()
            elif argc == 1:
                self.core.edsdk.take_picture()
            else:
                self.print('usage: shoot [INDEX]')

        else:
            self.print(f'invalid command: {argv[0]}')

    def on_command_cleared(self, event: wx.CommandEvent = None) -> None:
        """When the clear button is pressed, clear the console writer."""
        self._console_writer.ChangeValue('')

    def print(self, msg: str) -> None:
        """Add message to console."""
        self._console.AppendText(f'{msg}\n')

    def on_notification(self, signal: str, message: str = '') -> None:
        """Print any pydispatch signals."""
        self.print(f'{signal}: {message}')

    def on_action_export(self, filename: str) -> None:
        self.print(f'Exported actions to file {filename}')
