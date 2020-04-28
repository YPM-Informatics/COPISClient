import wx
from enums import Tool_Ids
from frames.settingsFrame import SettingsFrame

class ToolBar(wx.ToolBar):
    def __init__(self, parent):
        super(ToolBar, self).__init__(parent)

        # port and baud
        self.initPortBaudOptions()
        self.AddStretchableSpace()

        ## play, pause and stop buttons to animate the commands
        self.initAnimationButtons()
        self.AddStretchableSpace()

        ## import file
        self.initImport()
        self.AddStretchableSpace()

        ## general settings
        self.initSetting()

        self.Bind(wx.EVT_TOOL, self.handleTool)

        self.Realize()
        

    def initPortBaudOptions(self):
        ## TO DO: replace port and baud choices with dynamically detected ones
        self.AddStretchableSpace()
        portLabel = wx.StaticText(self, id = wx.ID_ANY, label = "Port: ", style = wx.ALIGN_LEFT)
        self.AddControl(portLabel)
        portCombo = wx.ComboBox(self, wx.ID_ANY, value = "", choices = ["Port 1", "Port 2", "Port 3"])
        self.AddControl(portCombo)
        baudLabel = wx.StaticText(self, id = wx.ID_ANY, label = " Baud: ", style = wx.ALIGN_RIGHT)
        self.AddControl(baudLabel)
        baudCombo = wx.ComboBox(self, wx.ID_ANY, value = "", choices = ["Baud 1", "Baud 2", "Baud 3"])
        self.AddControl(baudCombo)

        ## TO DO: connect and disconnect functionalities
        connectBtn = wx.Button(self, wx.ID_ANY, label = "Connect")
        self.AddControl(connectBtn)
        disconnectBtn = wx.Button(self, wx.ID_ANY, label = "Disconnect")
        self.AddControl(disconnectBtn)

    def initAnimationButtons(self):
        ## TO DO: 3D simulation functionalities -- play, pause and stop
        playImg = wx.Image('img/play.png')
        playImg = playImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(Tool_Ids.Play.value, 'Play', wx.Bitmap(playImg), shortHelp = "Play the simulation of commands.")

        pauseImg = wx.Image('img/pause.png')
        pauseImg = pauseImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(Tool_Ids.Pause.value, 'Pause', wx.Bitmap(pauseImg), shortHelp = "Pause the simulation.")
        
        stopImg = wx.Image('img/stop.png')
        stopImg = stopImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(Tool_Ids.Stop.value, 'Stop', wx.Bitmap(stopImg), shortHelp = "Stop the simulation.")

    def initImport(self):
        ## TO DO: browsing the file system and importing file functionalities
        fileLabel = wx.StaticText(self, id = wx.ID_ANY, label = "File: ", style = wx.ALIGN_LEFT)
        self.AddControl(fileLabel)
        fileBox = wx.TextCtrl(self)
        self.AddControl(fileBox)
        loadBtn = wx.Button(self, wx.ID_ANY, label = "Browse")
        self.AddControl(loadBtn)

    def initSetting(self):
        settingImg = wx.Image('img/setting.png')
        settingImg = settingImg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(Tool_Ids.Settings.value, 'Setting', wx.Bitmap(settingImg), shortHelp = "Set general settings of the application.")

    def handleTool(self, event):
        if event.GetId() == Tool_Ids.Settings.value:
            settingsFrame = SettingsFrame()
            settingsFrame.Show()