"""ToolbarPanel class."""

import wx
import wx.lib.agw.aui as aui

from enums import ToolIds
from gui.settings_frame import SettingsFrame
from util.serial_controller import SerialController
from gui.wxutils import create_scaled_bitmap, set_dialog


class ToolbarPanel(aui.AuiToolBar):
    """Manage AUI toolbar panel."""

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits ToolbarPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT, agwStyle=
            aui.AUI_TB_PLAIN_BACKGROUND|aui.AUI_TB_OVERFLOW)
        self.parent = parent
        self.c = self.parent.c

        self.serial_controller = None

        self.port_cb = None
        self.baud_cb = None

        self.init_controller()
        self.init_toolbar()
        self.update_ports()

        self.Bind(wx.EVT_TOOL, self.on_tool_selected)

    def init_controller(self) -> None:
        """Initialize serial controller object."""
        if self.serial_controller is not None:
            return

        self.serial_controller = SerialController()

    def init_toolbar(self) -> None:
        """Initialize and populate toolbar.

        Icons taken from https://material.io/resources/icons/?style=baseline.
        """
        # add port, baud comboboxes
        self.AddControl(wx.StaticText(self, label='Port', style=wx.ALIGN_LEFT))
        self.port_cb = wx.ComboBox(self, choices=[], style=wx.CB_READONLY, size=(75, -1))
        self.AddControl(self.port_cb, label='Port combobox')
        self.refresh_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('refresh', 20), size=(-1, -1))
        self.Bind(wx.EVT_BUTTON, self.on_refresh_port, self.AddControl(self.refresh_btn, label='Refresh port'))
        self.AddSpacer(8)
        self.AddControl(wx.StaticText(self, label='Baud', style=wx.ALIGN_LEFT))
        self.baud_cb = wx.ComboBox(self, choices=[], style=wx.CB_READONLY, size=(75, -1))
        self.Bind(wx.EVT_COMBOBOX, self.on_select_baud, self.AddControl(self.baud_cb, label='Baud combobox'))
        self.AddSpacer(8)
        self.Bind(wx.EVT_BUTTON, self.on_connect, self.AddControl(wx.Button(self, wx.ID_ANY, label='Connect', size=(75, -1))))

        self.AddSeparator()

        # add play, pause, stop tools
        _bmp = create_scaled_bitmap('play_arrow', 24)
        self.AddTool(ToolIds.PLAY.value, 'Play', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Play simulation')
        _bmp = create_scaled_bitmap('pause', 24)
        self.AddTool(ToolIds.PAUSE.value, 'Pause', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Pause simulation')
        _bmp = create_scaled_bitmap('stop', 24)
        self.AddTool(ToolIds.STOP.value, 'Stop', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Stop and reset simulation')
        _bmp = create_scaled_bitmap('get_app', 24)
        self.AddTool(ToolIds.EXPORT.value, 'Export', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Export actions as text')

        self.AddSeparator()

        # add settings tool
        _bmp = create_scaled_bitmap('settings', 24)
        self.AddTool(ToolIds.SETTINGS.value, 'Settings', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Edit simulation settings')

    def on_refresh_port(self, event: wx.CommandEvent) -> None:
        """On refresh button pressed, update baud combobox."""
        port = self.port_cb.StringSelection
        if not port:
            return
        if self.serial_controller.set_current_serial(port):
            self.update_bauds()
        else:
            set_dialog(f'Could not open port "{port}".')
            self.port_cb.Selection = -1

    def on_select_baud(self, event: wx.CommandEvent) -> None:
        self.serial_controller.selected_serial.baudrate = int(event.String)

    def on_connect(self, event: wx.CommandEvent) -> None:
        """On connect button pressed, update serial connection and button text.
        """
        connect_btn = self.FindControl(event.Id)
        if self.serial_controller.selected_serial:
            if self.serial_controller.selected_serial.is_open:
                self.serial_controller.selected_serial.close()
                connect_btn.Label = 'Connect'
            else:
                self.serial_controller.selected_serial.open()
                connect_btn.Label = 'Disconnect'
        else:
            set_dialog('Please select a port to connect to.')

    def update_ports(self) -> None:
        """Set port combobox to serial ports list."""
        self.port_cb.Items = self.serial_controller.ports

    def update_bauds(self) -> None:
        """If possible, set baud combobox to serial bauds list."""
        if self.serial_controller.bauds is not None:
            self.baud_cb.Items = [str(i) for i in self.serial_controller.bauds]

    def on_tool_selected(self, event: wx.CommandEvent) -> None:
        """On toolbar tool selected, check which and process accordingly.

        TODO: Link with copiscore when implemented.
        """
        if event.Id == ToolIds.PLAY.value:
            camera = self.parent.controller_panel.main_combo.Selection
            set_dialog(f'DEBUG: selected camera "{camera}".')
        elif event.Id == ToolIds.PAUSE.value:
            pass
        elif event.Id == ToolIds.SETTINGS.value:
            settings_frame = SettingsFrame(self)
            settings_frame.Show()
        elif event.Id == ToolIds.EXPORT.value:
            self.c.export_actions('actions.txt')
        else:
            pass

    def __del__(self) -> None:
        pass
