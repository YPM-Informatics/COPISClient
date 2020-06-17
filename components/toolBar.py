#!/usr/bin/env python3
"""TODO: Fill in docstring"""

import wx
from enums import Tool_Ids
from frames.settingsFrame import SettingsFrame
from controller.serialController import SerialController


class ToolBar(wx.ToolBar):
    def __init__(self, parent, *args, **kwargs):
        super(ToolBar, self).__init__(parent)

        # port and baud
        self.initPortBaudOptions()
        self.controller = SerialController()
        self.setPorts()
        self.setBaudRates()
        self.AddStretchableSpace()

        # play, pause and stop buttons to animate the commands
        self.initAnimationButtons()
        self.AddStretchableSpace()

        # import file
        self.initImport()
        self.AddStretchableSpace()

        # general settings
        self.initSetting()

        self.Bind(wx.EVT_TOOL, self.handleTool)

        self.Realize()

    def initPortBaudOptions(self):
        self.AddStretchableSpace()
        portLabel = wx.StaticText(self, id=wx.ID_ANY, label="Port: ", style=wx.ALIGN_LEFT)
        self.AddControl(portLabel)
        self.portCombo = wx.ComboBox(self, wx.ID_ANY, value="")
        self.portCombo.Bind(wx.EVT_COMBOBOX, self.onSelectPort)
        self.AddControl(self.portCombo)
        baudLabel = wx.StaticText(self, id=wx.ID_ANY, label=" Baud: ", style=wx.ALIGN_RIGHT)
        self.AddControl(baudLabel)
        self.baudCombo = wx.ComboBox(self, wx.ID_ANY, value="")
        self.baudCombo.Bind(wx.EVT_COMBOBOX, self.onSelectBaud)
        self.AddControl(self.baudCombo)

        self.connectBtn = wx.Button(self, wx.ID_ANY, label="Connect")
        self.connectBtn.Bind(wx.EVT_BUTTON, self.onConnect)
        self.AddControl(self.connectBtn)

    def initAnimationButtons(self):
        # TODO: 3D simulation functionalities -- play, pause and stop
        playImg = wx.Image('img/play.png')
        playImg = playImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(Tool_Ids.Play.value, 'Play', wx.Bitmap(playImg), shortHelp="Play the simulation of commands.")

        pauseImg = wx.Image('img/pause.png')
        pauseImg = pauseImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(Tool_Ids.Pause.value, 'Pause', wx.Bitmap(pauseImg), shortHelp="Pause the simulation.")

        stopImg = wx.Image('img/stop.png')
        stopImg = stopImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(Tool_Ids.Stop.value, 'Stop', wx.Bitmap(stopImg), shortHelp="Stop the simulation.")

    def initImport(self):
        # TODO: browsing the file system and importing file functionalities
        fileLabel = wx.StaticText(self, id=wx.ID_ANY, label="File: ", style=wx.ALIGN_LEFT)
        self.AddControl(fileLabel)
        fileBox = wx.TextCtrl(self)
        self.AddControl(fileBox)
        loadBtn = wx.Button(self, wx.ID_ANY, label="Browse")
        self.AddControl(loadBtn)

    def initSetting(self):
        settingImg = wx.Image('img/setting.png')
        settingImg = settingImg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(Tool_Ids.Settings.value, 'Setting', wx.Bitmap(settingImg), shortHelp="Set general settings of the application.")

    def handleTool(self, event):
        if event.GetId() == Tool_Ids.Settings.value:
            settingsFrame = SettingsFrame()
            settingsFrame.Show()

    def setPorts(self):
        self.portCombo.Clear()
        for port in self.controller.ports:
            self.portCombo.Append(port)

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
