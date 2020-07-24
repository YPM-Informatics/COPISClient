#!/usr/bin/env python3

import wx
from utils import set_dialog
from enums import ToolIds

from gui.settings_frame import SettingsFrame
from util.serial_controller import SerialController


class ToolbarPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        hbox = wx.BoxSizer()
        self.toolbar = wx.ToolBar(self, -1, style=wx.TB_HORIZONTAL | wx.NO_BORDER)
        hbox.Add(self.toolbar, 1, flag=wx.EXPAND)
        self.parent = parent

        # port and baud
        self.initPortBaudOptions()
        self.controller = SerialController()
        self.setPorts()
        self.setBaudRates()
        self.toolbar.AddStretchableSpace()

        # play, pause and stop buttons to animate the commands
        self.initAnimationButtons()
        self.toolbar.AddStretchableSpace()

        # import file
        self.initImport()
        self.toolbar.AddStretchableSpace()

        # general settings
        self.initSetting()
        self.toolbar.AddStretchableSpace()

        self.toolbar.Bind(wx.EVT_TOOL, self.handleTool)
        self.SetSizerAndFit(hbox)
        self.toolbar.Realize()

    def initPortBaudOptions(self):
        self.toolbar.AddStretchableSpace()
        portLabel = wx.StaticText(self.toolbar, id=wx.ID_ANY, label='Port: ', style=wx.ALIGN_LEFT)
        self.toolbar.AddControl(portLabel)
        self.toolbar.portCombo = wx.ComboBox(self.toolbar, wx.ID_ANY, value='', style=wx.CB_DROPDOWN)
        self.toolbar.portCombo.Bind(wx.EVT_COMBOBOX, self.onSelectPort)
        self.toolbar.AddControl(self.toolbar.portCombo)
        baudLabel = wx.StaticText(self.toolbar, id=wx.ID_ANY, label=' Baud: ', style=wx.ALIGN_RIGHT)
        self.toolbar.AddControl(baudLabel)
        self.toolbar.baudCombo = wx.ComboBox(self.toolbar, wx.ID_ANY, value='')
        self.toolbar.baudCombo.Bind(wx.EVT_COMBOBOX, self.onSelectBaud)
        self.toolbar.AddControl(self.toolbar.baudCombo)

        self.toolbar.connectBtn = wx.Button(self.toolbar, wx.ID_ANY, label='Connect')
        self.toolbar.connectBtn.Bind(wx.EVT_BUTTON, self.onConnect)
        self.toolbar.AddControl(self.toolbar.connectBtn)

    def initAnimationButtons(self):
        # TODO: 3D simulation functionalities -- play, pause and stop
        playImg = wx.Image('img/play.png')
        playImg = playImg.Scale(32, 32, wx.IMAGE_QUALITY_HIGH)
        self.toolbar.AddTool(ToolIds.PLAY.value, 'Play', wx.Bitmap(playImg), shortHelp='Play the simulation of commands.')

        pauseImg = wx.Image('img/pause.png')
        pauseImg = pauseImg.Scale(32, 32, wx.IMAGE_QUALITY_HIGH)
        self.toolbar.AddTool(ToolIds.PAUSE.value, 'Pause', wx.Bitmap(pauseImg), shortHelp='Pause the simulation.')

        stopImg = wx.Image('img/stop.png')
        stopImg = stopImg.Scale(32, 32, wx.IMAGE_QUALITY_HIGH)
        self.toolbar.AddTool(ToolIds.STOP.value, 'Stop', wx.Bitmap(stopImg), shortHelp='Stop the simulation.')

    def initImport(self):
        # TODO: browsing the file system and importing file functionalities
        fileLabel = wx.StaticText(self.toolbar, id=wx.ID_ANY, label='File: ', style=wx.ALIGN_LEFT)
        self.toolbar.AddControl(fileLabel)
        fileBox = wx.TextCtrl(self.toolbar)
        self.toolbar.AddControl(fileBox)
        loadBtn = wx.Button(self.toolbar, wx.ID_ANY, label='Browse')
        self.toolbar.AddControl(loadBtn)

    def initSetting(self):
        settingImg = wx.Image('img/setting.png')
        settingImg = settingImg.Scale(16, 16, wx.IMAGE_QUALITY_HIGH)
        self.toolbar.AddTool(ToolIds.SETTINGS.value, 'Setting', wx.Bitmap(settingImg), shortHelp='Set general settings of the application.')

    def handleTool(self, event):
        if event.GetId() == ToolIds.SETTINGS.value:
            settings_frame = SettingsFrame()
            settings_frame.Show()
        elif event.GetId() == ToolIds.PLAY.value:
            camid = self.parent.controller_panel.masterCombo.GetSelection()
            if camid != -1:
                cam = self.parent.visualizer_panel.get_camera_by_id(camid)
                if cam:
                   cam.translate(0.62, 0.62, 0.62)
            else:
                set_dialog('Please select the camera to control.')

    def setPorts(self):
        self.toolbar.portCombo.Clear()
        for port in self.controller.ports:
            self.toolbar.portCombo.Append(port)

    def setBaudRates(self):
        if self.controller.bauds:
            self.toolbar.baudCombo.Clear()
            for baud in self.controller.bauds:
                self.toolbar.baudCombo.Append(str(baud))

    def onSelectPort(self, event):
        self.controller.set_current_serial(self.toolbar.portCombo.GetStringSelection())
        self.setBaudRates()

    def onSelectBaud(self, event):
        self.controller.selected_serial.baudrate = int(self.toolbar.baudCombo.GetStringSelection())

    def onConnect(self, event):
        if self.controller.selected_serial:
            if self.controller.selected_serial.is_open:
                self.controller.selected_serial.close()
                self.toolbar.connectBtn.SetLabel('Connect')
            else:
                self.controller.selected_serial.open()
                self.toolbar.connectBtn.SetLabel('Disconnect')
        else:
            set_dialog('Please select a port to connect to.')
