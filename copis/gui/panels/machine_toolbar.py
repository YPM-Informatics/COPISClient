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

"""MachineToolbar class."""

import logging
import wx
import wx.lib.agw.aui as aui

from copis.enums import ToolIds
from copis.gui.machine_settings_dialog import MachineSettingsDialog
from copis.gui.wxutils import create_scaled_bitmap, set_dialog


class MachineToolbar(aui.AuiToolBar):
    """Manage AUI toolbar panel."""

    def __init__(self, parent, console = None) -> None:
        """Inits MachineToolbar with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT, agwStyle=
            aui.AUI_TB_PLAIN_BACKGROUND|aui.AUI_TB_OVERFLOW)
        self.parent = parent
        self.core = self.parent.core

        self._console = console

        self.port_cb = None
        self.baud_cb = None

        self.init_toolbar()
        self.update_ports()

        self.Bind(wx.EVT_TOOL, self.on_tool_selected)

    def init_toolbar(self) -> None:
        """Initialize and populate toolbar.

        Icons taken from https://material.io/resources/icons/?style=baseline.
        """
        # Add port, baud comboboxes.
        self.AddControl(wx.StaticText(self, label='Port', style=wx.ALIGN_LEFT))
        self.port_cb = wx.ComboBox(self, choices=[], style=wx.CB_READONLY, size=(75, -1))
        self.Bind(wx.EVT_COMBOBOX, self.on_select_port, self.AddControl(self.port_cb,
            label='Port combobox'))

        self.refresh_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('refresh', 20),
            size=(-1, -1))
        self.Bind(wx.EVT_BUTTON, self.on_refresh_ports, self.AddControl(self.refresh_btn,
            label='Refresh ports'))
        self.AddSpacer(8)
        self.AddControl(wx.StaticText(self, label='Baud', style=wx.ALIGN_LEFT))
        self.baud_cb = wx.ComboBox(self, choices=[], style=wx.CB_READONLY,
            size=(75, -1))
        self.AddControl(self.baud_cb, label='Baud combobox')
        self.AddSpacer(8)
        self.connect_btn = wx.Button(self, wx.ID_ANY, label='Connect', size=(75, -1))
        self.Bind(wx.EVT_BUTTON, self.on_connect, self.AddControl(self.connect_btn))

        self.AddSeparator()

        # Add play, pause, stop tools.
        _bmp = create_scaled_bitmap('play_arrow', 24)
        self.AddTool(ToolIds.PLAY.value, 'Play', _bmp, _bmp, aui.ITEM_NORMAL,
            short_help_string='Play simulation')
        _bmp = create_scaled_bitmap('pause', 24)
        self.AddTool(ToolIds.PAUSE.value, 'Pause', _bmp, _bmp, aui.ITEM_NORMAL,
            short_help_string='Pause simulation')
        _bmp = create_scaled_bitmap('stop', 24)
        self.AddTool(ToolIds.STOP.value, 'Stop', _bmp, _bmp, aui.ITEM_NORMAL,
            short_help_string='Stop and reset simulation')
        _bmp = create_scaled_bitmap('get_app', 24)
        self.AddTool(ToolIds.EXPORT.value, 'Export', _bmp, _bmp, aui.ITEM_NORMAL,
            short_help_string='Export actions as text')

        # TODO: implement settings dialog, uncomment below

        # self.AddSeparator()

        # # add settings tool
        # _bmp = create_scaled_bitmap('settings', 24)
        # self.AddTool(ToolIds.SETTINGS.value, 'Settings', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Edit simulation settings')

    def on_refresh_ports(self, event: wx.CommandEvent) -> None:
        """On refresh button pressed, update port list."""
        refresh_btn = self.FindControl(event.Id)
        refresh_btn.Disable()

        self.port_cb.Selection = -1
        self.baud_cb.Selection = -1
        self.baud_cb.Items = []
        self.connect_btn.Label = 'Connect'

        self._print('Refreshing serial ports...')
        self.core.serial.update_port_list()
        self._print('Serial ports refreshed.')

        self.update_ports()
        self.port_cb.Popup()
        refresh_btn.Enable()

    def on_select_port(self, event: wx.CommandEvent) -> None:
        """On port selected, populate the baud combo box"""
        if self.port_cb.Selection == -1:
            self.baud_cb.Selection = -1
            self.baud_cb.Items = []
        else:
            self.baud_cb.Items = [str(i) for i in self.core.serial.BAUDS]
            self.baud_cb.Selection = len(self.baud_cb.Items) - 1

            selection = self.port_cb.Selection
            p_name = self.port_cb.Items[selection]
            port = self.core.serial.select_port(p_name)
            self.connect_btn.Label = 'Disconnect' \
                if port.connection is not None and port.connection.is_open else 'Connect'

    def on_connect(self, event: wx.CommandEvent) -> None:
        """On connect button pressed, updates serial connection and button text"""
        connect_btn = self.FindControl(event.Id)
        if self.port_cb.Selection >= 0:
            selection = self.baud_cb.Selection
            baud = int(self.baud_cb.Items[selection]) \
                if selection >= 0 else self.core.serial.BAUDS[-1]

            if connect_btn.Label == 'Connect':
                if self.core.serial.open_port(baud):
                    connect_btn.Label = 'Disconnect'
                else:
                    connect_btn.Label = 'Connect'
                    set_dialog('Unable to connect.')
            else:
                self.core.serial.close_port()
                connect_btn.Label = 'Connect'
        else:
            set_dialog('Please select a port to connect to.')

    def update_ports(self) -> None:
        """Set port combobox to serial ports list."""
        self.port_cb.Items = [p.name for p in self.core.serial.port_list]

    def on_tool_selected(self, event: wx.CommandEvent) -> None:
        """On toolbar tool selected, check which and process accordingly.

        TODO: Link with copiscore when implemented.
        """
        if event.Id == ToolIds.PLAY.value:
            if self.core.paused:
                self.core.resume()
            else:
                self.core.start_imaging()

        elif event.Id == ToolIds.PAUSE.value:
            self.core.pause()

        elif event.Id == ToolIds.STOP.value:
            self.core.cancel_imaging()

        elif event.Id == ToolIds.SETTINGS.value:
            with MachineSettingsDialog(self) as dlg:
                logging.debug('Machine Settings opened')

        elif event.Id == ToolIds.EXPORT.value:
            self.core.export_actions('actions.txt')

    def _print(self, msg):
        if self._console is None:
            print(msg)
        else:
            self._console.print(msg)

    def __del__(self) -> None:
        pass
