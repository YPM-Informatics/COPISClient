"""TODO"""

import wx
import wx.lib.agw.aui as aui

from enums import ToolIds
from gui.settings_frame import SettingsFrame
from util.serial_controller import SerialController
from utils import create_scaled_bitmap, set_dialog


class ToolbarPanel(aui.AuiToolBar):
    """TODO"""

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits ToolbarPanel with constructors."""
        super().__init__(parent, agwStyle=
            aui.AUI_TB_PLAIN_BACKGROUND | aui.AUI_TB_OVERFLOW)
        self.parent = parent

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
        self.AddControl(wx.StaticText(self, wx.ID_ANY, 'Port', style=wx.ALIGN_LEFT))
        self.port_cb = wx.ComboBox(self, wx.ID_ANY, choices=[], style=wx.CB_READONLY, size=(75, -1))
        self.Bind(wx.EVT_COMBOBOX, self.on_select_port, self.AddControl(self.port_cb, label='Port combobox'))
        self.AddSpacer(10)
        self.AddControl(wx.StaticText(self, wx.ID_ANY, 'Baud', style=wx.ALIGN_LEFT))
        self.baud_cb = wx.ComboBox(self, wx.ID_ANY, choices=[], style=wx.CB_READONLY, size=(75, -1))
        self.Bind(wx.EVT_COMBOBOX, self.on_select_baud, self.AddControl(self.baud_cb, label='Baud combobox'))
        self.AddSpacer(10)
        self.Bind(wx.EVT_BUTTON, self.on_connect, self.AddControl(wx.Button(self, wx.ID_ANY, label='Connect', size=(75, -1))))

        self.AddSeparator()

        # add play, pause, stop tools
        _bmp = create_scaled_bitmap('play_arrow', 24)
        self.AddTool(ToolIds.PLAY.value, 'Play', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Play simulation')
        _bmp = create_scaled_bitmap('pause', 24)
        self.AddTool(ToolIds.PAUSE.value, 'Pause', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Pause simulation')
        _bmp = create_scaled_bitmap('stop', 24)
        self.AddTool(ToolIds.STOP.value, 'Stop', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Stop and reset simulation')

        self.AddSeparator()

        # add settings tool
        _bmp = create_scaled_bitmap('settings', 24)
        self.AddTool(ToolIds.SETTINGS.value, 'Settings', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Edit simulation settings')

    def on_select_port(self, event: wx.CommandEvent) -> None:
        port = event.GetString()
        if self.serial_controller.set_current_serial(port):
            self.update_bauds()
        else:
            set_dialog(f'Could not open port "{port}".')
            self.port_cb.SetSelection(-1)

    def on_select_baud(self, event: wx.CommandEvent) -> None:
        self.serial_controller.selected_serial.baudrate = int(event.GetString())

    def on_connect(self, event):
        connect_btn = self.FindControl(event.GetId())
        if self.serial_controller.selected_serial:
            if self.serial_controller.selected_serial.is_open:
                self.serial_controller.selected_serial.close()
                connect_btn.SetLabel('Connect')
            else:
                self.serial_controller.selected_serial.open()
                connect_btn.SetLabel('Disconnect')
        else:
            set_dialog('Please select a port to connect to.')

    def update_ports(self) -> None:
        self.port_cb.Set(self.serial_controller.ports)

    def update_bauds(self) -> None:
        if self.serial_controller.bauds is not None:
            self.baud_cb.Set([str(i) for i in self.serial_controller.bauds])

    def on_tool_selected(self, event: wx.CommandEvent) -> None:
        if event.GetId() == ToolIds.SETTINGS.value:
            settings_frame = SettingsFrame(self)
            settings_frame.Show()
        elif event.GetId() == ToolIds.PLAY.value:
            cam_id = self.parent.controller_panel.masterCombo.GetSelection()
            if cam_id != -1:
                cam = self.parent.visualizer_panel.get_camera_by_id(cam_id)
                if cam:
                    cam.translate(1, 1, 1)
            else:
                set_dialog('Please select the camera to control.')
        elif event.GetId() == ToolIds.PAUSE.value:
            pass
        else:
            pass

    def __del__(self) -> None:
        pass
