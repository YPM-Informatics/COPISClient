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
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""ConsolePanel class."""

import wx

from pydispatch import dispatcher

from copis import console

from .command_processor import _CommandProcessor
from copis.helpers import get_notification_msg, get_timestamped
from copis.gui.wxutils import create_scaled_bitmap


class ConsolePanel(wx.Panel):
    """Console panel.

    Args:
        parent: Pointer to a parent wx.Frame.
    """

    def __init__(self, parent, *args, **kwargs) -> None:
        """Initialize ConsolePanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self.core = self.parent.core

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        font = wx.Font(9, family = wx.FONTFAMILY_MODERN, style = 0, weight = 90,
            underline = False, faceName ='Consolas', encoding = wx.FONTENCODING_DEFAULT)
        self.SetFont(font)

        self._console = None
        self._console_writer = None

        self.init_gui()
        self.Layout()
        self._cmd_processor = _CommandProcessor(self.core)

        # Bind listeners.
        dispatcher.connect(self.on_notification, signal='ntf_a_list_changed')
        dispatcher.connect(self.on_notification, signal='ntf_d_list_changed')
        dispatcher.connect(self.on_notification, signal='ntf_o_list_changed')
        dispatcher.connect(self.on_notification, signal='ntf_a_selected')
        dispatcher.connect(self.on_notification, signal='ntf_a_deselected')
        dispatcher.connect(self.on_notification, signal='ntf_s_selected')
        dispatcher.connect(self.on_notification, signal='ntf_s_deselected')
        dispatcher.connect(self.on_notification, signal='ntf_d_selected')
        dispatcher.connect(self.on_notification, signal='ntf_d_deselected')
        dispatcher.connect(self.on_notification, signal='ntf_o_selected')
        dispatcher.connect(self.on_notification, signal='ntf_o_deselected')

        dispatcher.connect(self.on_notification, signal='msg_error')
        dispatcher.connect(self.on_notification, signal='msg_info')
        dispatcher.connect(self.on_notification, signal='msg_debug')
        dispatcher.connect(self.on_notification, signal='msg_raw')
        dispatcher.connect(self.on_notification, signal='msg_echo')

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

        self.on_command_cleared()
        self._cmd_processor.process(cmd)

    def on_command_cleared(self, _event: wx.CommandEvent = None) -> None:
        """When the clear button is pressed, clear the console writer."""
        self._console_writer.ChangeValue('')

    def print(self, msg: str) -> None:
        """Add message to console."""

        try:
            if self._console:
                # Call the specified function after the current and pending event handlers have been completed.
                # This is good for making GUI method calls from non-GUI threads, in order to prevent hangs.
                wx.CallAfter(self._console.AppendText, f'{msg}\n')
            else:
                print(msg)
        except Exception as err:
            print(f'intended to print: {msg}')
            print(f'instead, got error : {err.args[0]}')

    def on_notification(self, signal: str, message: str = '') -> None:
        """Print any pydispatch signals."""
        notification = message

        if signal.startswith('ntf_'):
            if self.core.is_dev_env:
                parts = signal.split('_')
                signal = 'msg_debug'

                if parts[1] == 'a':
                    message = 'Action'
                elif parts[1] == 'd':
                    message = 'Device'
                elif parts[1] == 'o':
                    message = 'Proxy object'
                elif parts[1] == 's':
                    message = 'Pose set'

                for i in range(2, len(parts)):
                    message = f'{message} {parts[i]}'

                notification = get_notification_msg(signal, get_timestamped(message))
                self.print(notification)
        else:
            notification = get_notification_msg(signal, message)
            self.print(notification)

