#!/usr/bin/env python3
"""TODO: Fill in docstring"""

import wx
from enums import Tool_Ids
from frames.settingsFrame import SettingsFrame
from controller.serialController import SerialController
import util

class ToolBarPanel(wx.Panel):
    def __init__(self, parent):
        super(ToolBarPanel, self).__init__(parent, style=wx.BORDER_SUNKEN)
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
        portLabel = wx.StaticText(self.toolbar, id=wx.ID_ANY, label="Port: ", style=wx.ALIGN_LEFT)
        self.toolbar.AddControl(portLabel)
        self.toolbar.portCombo = wx.ComboBox(self.toolbar, wx.ID_ANY, value="", style=wx.CB_DROPDOWN)
        self.toolbar.portCombo.Bind(wx.EVT_COMBOBOX, self.onSelectPort)
        self.toolbar.AddControl(self.toolbar.portCombo)
        baudLabel = wx.StaticText(self.toolbar, id=wx.ID_ANY, label=" Baud: ", style=wx.ALIGN_RIGHT)
        self.toolbar.AddControl(baudLabel)
        self.toolbar.baudCombo = wx.ComboBox(self.toolbar, wx.ID_ANY, value="")
        self.toolbar.baudCombo.Bind(wx.EVT_COMBOBOX, self.onSelectBaud)
        self.toolbar.AddControl(self.toolbar.baudCombo)

        self.toolbar.connectBtn = wx.Button(self.toolbar, wx.ID_ANY, label="Connect")
        self.toolbar.connectBtn.Bind(wx.EVT_BUTTON, self.onConnect)
        self.toolbar.AddControl(self.toolbar.connectBtn)

    def initAnimationButtons(self):
        # TODO: 3D simulation functionalities -- play, pause and stop
        playImg = wx.Image('img/play.png')
        playImg = playImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.toolbar.AddTool(Tool_Ids.Play.value, 'Play', wx.Bitmap(playImg), shortHelp="Play the simulation of commands.")

        pauseImg = wx.Image('img/pause.png')
        pauseImg = pauseImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.toolbar.AddTool(Tool_Ids.Pause.value, 'Pause', wx.Bitmap(pauseImg), shortHelp="Pause the simulation.")

        stopImg = wx.Image('img/stop.png')
        stopImg = stopImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.toolbar.AddTool(Tool_Ids.Stop.value, 'Stop', wx.Bitmap(stopImg), shortHelp="Stop the simulation.")

    def initImport(self):
        # TODO: browsing the file system and importing file functionalities
        fileLabel = wx.StaticText(self.toolbar, id=wx.ID_ANY, label="File: ", style=wx.ALIGN_LEFT)
        self.toolbar.AddControl(fileLabel)
        fileBox = wx.TextCtrl(self.toolbar)
        self.toolbar.AddControl(fileBox)
        loadBtn = wx.Button(self.toolbar, wx.ID_ANY, label="Browse")
        self.toolbar.AddControl(loadBtn)

    def initSetting(self):
        settingImg = wx.Image('img/setting.png')
        settingImg = settingImg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        self.toolbar.AddTool(Tool_Ids.Settings.value, 'Setting', wx.Bitmap(settingImg), shortHelp="Set general settings of the application.")

    def handleTool(self, event):
        if event.GetId() == Tool_Ids.Settings.value:
            settingsFrame = SettingsFrame()
            settingsFrame.Show()
        elif event.GetId() == Tool_Ids.Play.value:
            camId = self.parent.controller_panel.masterCombo.GetSelection()
            if camId != -1:
                cam = self.parent.visualizer_panel.getCamById(camId)
                if cam:
                   cam.translate(0.62, 0.62, 0.62)
            else:
                util.set_dialog("Please select the camera to control.")

    def setPorts(self):
        self.toolbar.portCombo.Clear()
        for port in self.controller.ports:
            self.toolbar.portCombo.Append(port)

    def setBaudRates(self):
        if self.controller.bauds:
            self.baudCombo.Clear()
            for baud in self.controller.bauds:
                self.baudCombo.Append(str(baud))

    def onSelectPort(self, event):
        self.controller.setCurrentSerial(self.portCombo.GetStringSelection())
        self.setBaudRates()

    def onSelectBaud(self, event):
        self.controller.selected_serial.baudrate = int(self.baudCombo.GetStringSelection())

    def onConnect(self, event):
        if self.controller.selected_serial.is_open:
            self.controller.selected_serial.close()
            self.connectBtn.SetLabel('Connect')
        else:
            self.controller.selected_serial.open()
            self.connectBtn.SetLabel('Disconnect')
