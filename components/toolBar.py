import wx

class ToolBar(wx.ToolBar):
    def __init__(self, parent):
        super(ToolBar, self).__init__(parent)

        ## port and baud options
        self.initPortBaudOptions()

        ## play, pause and stop buttons to animate the commands
        self.initAnimationButtons()

        ## import file
        self.initImport()

        ## setting options
        self.initSetting()
        

    def initPortBaudOptions(self):
        ## TO DO: it should detect ports and baud options when the machine is connected
        self.AddStretchableSpace()
        portLabel = wx.StaticText(self, id = wx.ID_ANY, label = "Port: ", style = wx.ALIGN_LEFT)
        self.AddControl(portLabel)
        portCombo = wx.ComboBox(self, wx.ID_ANY, value = "", choices = ["Port 1", "Port 2", "Port 3"])
        self.AddControl(portCombo)
        baudLabel = wx.StaticText(self, id = wx.ID_ANY, label = " Baud: ", style = wx.ALIGN_RIGHT)
        self.AddControl(baudLabel)
        baudCombo = wx.ComboBox(self, wx.ID_ANY, value = "", choices = ["Baud 1", "Baud 2", "Baud 3"])
        self.AddControl(baudCombo)

        ## TO DO: create and bind functions
        connectBtn = wx.Button(self, wx.ID_ANY, label = "Connect")
        self.AddControl(connectBtn)
        disconnectBtn = wx.Button(self, wx.ID_ANY, label = "Disconnect")
        self.AddControl(disconnectBtn)

    def initAnimationButtons(self):
        ## TO DO: create and bind functions
        self.AddStretchableSpace()
        playImg = wx.Image('img/play.png')
        playImg = playImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(1, 'Play', wx.Bitmap(playImg))

        pauseImg = wx.Image('img/pause.png')
        pauseImg = pauseImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(1, 'Pause', wx.Bitmap(pauseImg))
        
        stopImg = wx.Image('img/stop.png')
        stopImg = stopImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(1, 'Stop', wx.Bitmap(stopImg))

    def initImport(self):
        ## TO DO: create and bind function to "Browse" button
        self.AddStretchableSpace()
        fileLabel = wx.StaticText(self, id = wx.ID_ANY, label = "File: ", style = wx.ALIGN_LEFT)
        self.AddControl(fileLabel)
        fileBox = wx.TextCtrl(self)
        self.AddControl(fileBox)
        loadBtn = wx.Button(self, wx.ID_ANY, label = "Browse")
        self.AddControl(loadBtn)

    def initSetting(self):
        ## TO DO: figure out what settings are needed and create a popup box with setting options
        self.AddStretchableSpace()
        settingImg = wx.Image('img/setting.png')
        settingImg = settingImg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        self.AddTool(1, 'Setting', wx.Bitmap(settingImg))
