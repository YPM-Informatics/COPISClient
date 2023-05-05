# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""MachineToolbar class."""


import wx
import wx.lib.agw.aui as aui
import uuid

from pydispatch import dispatcher

from copis.globals import ToolIds
from copis.gui.machine_settings_dialog import MachineSettingsDialog
from copis.gui.wxutils import create_scaled_bitmap, show_msg_dialog
from copis.helpers import print_debug_msg, print_info_msg


class MachineToolbar(aui.AuiToolBar):
    """Manage machine toolbar."""

    def __init__(self, parent) -> None:
        """Initialize MachineToolbar with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT, agwStyle=
            aui.AUI_TB_PLAIN_BACKGROUND)

        self._parent = parent
        self._core = self._parent.core

        self.port_cb = None
        self.baud_cb = None

        self.init_toolbar()
        self.update_ports()

        # Using the aui.AUI_TB_OVERFLOW style flag means that the overflow button always shows
        # when the toolbar is floating, even if all the items fit.
        # This allows the overflow button to be visible only when they don't;
        # no matter if the toolbar is floating or docked.
        self.Bind(wx.EVT_MOTION,
            lambda _: self.SetOverflowVisible(not self.GetToolBarFits()))

        # self.Bind(wx.EVT_TOOL, self.on_tool_selected)

    def init_toolbar(self) -> None:
        """Initialize and populate toolbar.

        Icons taken from https://material.io/resources/icons/?style=baseline.
        """
        # Add port, baud comboboxes.
        self.AddControl(wx.StaticText(self, label='Port', style=wx.ALIGN_LEFT))
        self.port_cb = wx.ComboBox(self, choices=[], style=wx.CB_READONLY, size=(75, -1))
        self.Bind(wx.EVT_COMBOBOX, self.on_select_port,
            self.AddControl(self.port_cb, label='Port combobox'))

        self.refresh_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('refresh', 20),
            size=(-1, -1))
        self.Bind(wx.EVT_BUTTON, self.on_refresh_ports,
            self.AddControl(self.refresh_btn, label='Refresh ports'))
        self.AddSpacer(5)
        self.AddControl(wx.StaticText(self, label='Baud', style=wx.ALIGN_LEFT))
        self.baud_cb = wx.ComboBox(
            self, choices=[], style=wx.CB_READONLY, size=(75, -1))
        self.AddControl(self.baud_cb, label='Baud combobox')
        self.AddSpacer(5)
        self.connect_serial_btn = wx.Button(self, wx.ID_ANY, label='Connect', size=(75, -1))
        self.Bind(wx.EVT_BUTTON, self.on_connect_serial, self.AddControl(self.connect_serial_btn))
        self.AddSpacer(5)
        self.home_btn = wx.Button(self, wx.ID_ANY, label='Home', size=(75, -1))
        self.Bind(wx.EVT_BUTTON, self.on_home, self.AddControl(self.home_btn))
        self.AddSpacer(5)
        self.ready_btn = wx.Button(self, wx.ID_ANY, label='Ready', size=(75, -1))
        self.Bind(wx.EVT_BUTTON, self.on_ready, self.AddControl(self.ready_btn))
        self.AddSpacer(5)

        self.home_btn.Enable(self._can_home())

        self.AddSeparator()
        self.AddSpacer(5)

        self.start_imaging_btn = wx.Button(self, wx.ID_ANY, label='Start Imaging', size=(95, -1))
        self.Bind(wx.EVT_BUTTON, self.on_start_imaging, self.AddControl(self.start_imaging_btn))

        _bmp = create_scaled_bitmap('export', 24)
        self.AddTool(ToolIds.EXPORT.value, 'Export actions', _bmp, _bmp, aui.ITEM_NORMAL,
            short_help_string='Export actions')

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
        self.connect_serial_btn.Label = 'Connect'

        self._core.update_serial_ports()
        print_info_msg(self._core.console, 'Serial ports refreshed.')

        self.update_ports()
        self.port_cb.Popup()
        refresh_btn.Enable()

    def on_select_port(self, event: wx.CommandEvent) -> None:
        """On port selected, populate the baud combo box"""
        if self.port_cb.Selection == -1:
            self.baud_cb.Selection = -1
            self.baud_cb.Items = []
        else:
            self.baud_cb.Items = [str(i) for i in self._core.serial_bauds]
            self.baud_cb.Selection = len(self.baud_cb.Items) - 1

            selection = self.port_cb.Selection
            selected_port = self.port_cb.Items[selection]
            if self._core.select_serial_port(selected_port):
                is_port_connected = self._core.is_serial_port_connected
                self.connect_serial_btn.Label = 'Disconnect' if is_port_connected else 'Connect'

    def on_connect_serial(self, event: wx.CommandEvent) -> None:
        """On connect button pressed, updates serial connection and button text"""
        caption = 'Connect'
        connect_btn = self.FindControl(event.Id)
        if self.port_cb.Selection >= 0:
            selection = self.baud_cb.Selection
            baud = int(self.baud_cb.Items[selection]) \
                if selection >= 0 else self._core.serial_bauds[-1]

            if connect_btn.Label == caption:
                if self._core.connect_serial(baud):
                    connect_btn.Label = 'Disconnect'
                else:
                    connect_btn.Label = caption
                    show_msg_dialog('Unable to connect.', caption)
            else:
                self._core.disconnect_serial()
                connect_btn.Label = caption
        else:
            show_msg_dialog('Please select a port to connect to.', caption)

    def update_ports(self) -> None:
        """Set port combobox to serial ports list."""
        self.port_cb.Items = [p.name for p in self._core.serial_port_list]

    def on_tool_selected(self, event: wx.CommandEvent) -> None:
        """On toolbar tool selected, check which and process accordingly.

        TODO: Link with copiscore when implemented.
        """
        if event.Id == ToolIds.PLAY.value:
            if self.core.paused:
                self.core.resume_work()
            else:
                self.core.start_imaging()
        elif event.Id == ToolIds.PAUSE.value:
            self._core.pause_work()
        elif event.Id == ToolIds.STOP.value:
            self._core.stop_work()

        elif event.Id == ToolIds.SETTINGS.value:
            with MachineSettingsDialog(self) as dlg:
                print_debug_msg(self._core.console, 'Machine Settings opened.',
                    self._core.is_dev_env)

        elif event.Id == ToolIds.EXPORT.value:
            self._core.export_poses('actions.txt')

    def on_start_imaging(self, event: wx.CommandEvent) -> None:
        """On start imaging button pressed, initiate imaging workflow."""
        self._core.session_guid = str(uuid.uuid4())
        is_connected = self._core.is_serial_port_connected
        has_path = len(self._core.project.move_sets)
        is_homed = self._core.is_machine_homed
        can_image = is_connected and has_path and is_homed

        if not can_image:
            msg = 'The machine needs to be homed before imaging.'
            if not is_connected:
                msg = 'The machine needs to be connected for imaging.'
            elif not has_path:
                msg = 'The machine needs a path for imaging.'

            show_msg_dialog(msg, 'Imaging')
            return

        pos = event.GetEventObject().GetScreenPosition()
        pane: aui.AuiPaneInfo = self.GetAuiManager().GetPane(self._parent.imaging_toolbar)

        def play_all_handler():
            self._core.start_imaging()
            pane.window.enable_tool(ToolIds.PAUSE)
            pane.window.enable_tool(ToolIds.STOP)

        def pause_handler():
            self._core.pause_work()

        def stop_handler():
            self._core.stop_work()

        actions = [(ToolIds.PLAY_ALL, True, play_all_handler),
            (ToolIds.PAUSE, False, pause_handler),
            (ToolIds.STOP, False, stop_handler)]
        self._parent.show_imaging_toolbar(pos, actions)
        dispatcher.connect(self._parent.hide_imaging_toolbar, signal='ntf_machine_idle')

    def on_home(self, event: wx.CommandEvent) -> None:
        """On home button pressed, issue homing commands to machine."""
        if not self._core.is_serial_port_connected:
            show_msg_dialog('Connect to the machine in order to home it.', 'Homing')
            return

        home_btn = self.FindControl(event.Id)
        self._core.start_homing()
        home_btn.Enable(self._can_home())

    def on_ready(self, _) -> None:
        """On ready button pressed, issue commands to initializes
        the gantries to their current positions."""

        if not self._core.is_serial_port_connected:
            show_msg_dialog('Connect to the machine in order to set or go to ready.', 'Readying')
            return

        self._core.set_ready()

    def _can_home(self):
        # TODO figure this out: disable homing button when homed
        # enable when not; dynamically.
        return True # self._core.is_machine_homed

    def __del__(self) -> None:
        pass
