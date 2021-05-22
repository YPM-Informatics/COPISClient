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

import wx

from pydispatch import dispatcher

from .command_processor import _CommandProcessor
from copis.gui.wxutils import create_scaled_bitmap


class ConsolePanel(wx.Panel):
    """Console panel.

    Args:
        parent: Pointer to a parent wx.Frame.
    """

    def __init__(self, parent) -> None:
        """Inits ConsolePanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self.core = self.parent.core

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self._console = None
        self._console_writer = None

        self.init_gui()
        self.Layout()
        self._cmd_processor = _CommandProcessor(self)

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

        self._cmd_processor.process(cmd)

    def on_command_cleared(self, _event: wx.CommandEvent = None) -> None:
        """When the clear button is pressed, clear the console writer."""
        self._console_writer.ChangeValue('')

    def print(self, msg: str) -> None:
        """Add message to console."""

        # TODO: Is there a better way to handle this?
        # Like first finding out if _console (wx.TxtCtrl) is disposed of?
        try:
            self._console.AppendText(f'{msg}\n')
        except RuntimeError:
            print(f'{msg}\n')

    def on_notification(self, signal: str, message: str = '') -> None:
        """Prints any pydispatch signals."""
        self.print(f'{signal}: {message}')

    def on_action_export(self, filename: str) -> None:
        """Prints action exported message."""
        self.print(f'Exported actions to file {filename}')