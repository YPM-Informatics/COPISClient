import wx

class PathGeneratorFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Path Generator", size = (250, 400))
        self.SetMinSize(wx.Size(250, 400))
        self.font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(15)

        self.initPanel()
        self.Centre()

    def initPanel(self):
        ## LAYOUT

     	############################################
        ## vbox1  ------------------------------  ##
	    ##        | Circular Path Generator    |  ##
	    ##        | hbox   ------------------- |  ##
	    ##        | Points | No.Points: ____ | |  ##
	    ##        |        ------------------- |  ##
	    ##        | hbox   ------------------- |  ##
	    ##        | Radius | Radius (mm): ___| |  ##
	    ##        |        ------------------- |  ##
	    ##        | hbox   ------------------- |  ##
	    ##        | StartX | Start X: ____   | |  ##
	    ##        |        ------------------- |  ##
	    ##        | hbox   ------------------- |  ##
	    ##        | StartY | Start Y: ____   | |  ##
	    ##        |        ------------------- |  ##
	    ##        | hbox   ------------------- |  ##
	    ##        | StartZ | Start Z: ____   | |  ##
	    ##        |        ------------------- |  ##
        ##        | hbox   ------------------- |  ##
        ##        | Cameras| No. Cams: ____  | |  ##
        ##        |        ------------------- |  ##
        ##        |                            |  ##
        ##        | Take photo at each vertex  |  ##
        ##        |                            |  ##
        ##        | Generate Circle            |  ##
        ##        | Generate Sphere            |  ##
        ##        ------------------------------  ##
        ############################################
        self.panel = wx.Panel(self, style = wx.BORDER_SUNKEN)

        vbox1 = wx.BoxSizer(wx.VERTICAL)

        ## Label
        cGeneratorLabel = wx.StaticText(self.panel, wx.ID_ANY, label = 'Circular Path Generator', style = wx.ALIGN_LEFT)
        cGeneratorLabel.SetFont(self.font)
        vbox1.Add(cGeneratorLabel, 1, flag = wx.TOP|wx.BOTTOM|wx.LEFT, border = 10)

        ## No. Points
        hboxPoints = wx.BoxSizer()
        noPointsLabel = wx.StaticText(self.panel, wx.ID_ANY, label = 'No. Points: ')
        hboxPoints.Add(noPointsLabel, 1, flag = wx.RIGHT, border = 5)
        self.noPointsSc = wx.SpinCtrl(self.panel, value = '0')
        self.noPointsSc.SetRange(0, 100)
        hboxPoints.Add(self.noPointsSc)
        vbox1.Add(hboxPoints, 1, flag = wx.LEFT, border = 15)

        ## Radius
        hboxRadius = wx.BoxSizer()
        radiusLabel = wx.StaticText(self.panel, wx.ID_ANY, label = 'Radius (mm): ')
        hboxRadius.Add(radiusLabel, 1, flag = wx.RIGHT, border = 5)
        self.radiusSc = wx.SpinCtrl(self.panel, value = '0')
        self.radiusSc.SetRange(0, 100)
        hboxRadius.Add(self.radiusSc)
        vbox1.Add(hboxRadius, 1, flag = wx.LEFT, border = 15)

        ## X
        hboxStartX = wx.BoxSizer()
        startXLabel = wx.StaticText(self.panel, wx.ID_ANY, label = 'Start X: ')
        hboxStartX.Add(startXLabel, 1, flag = wx.RIGHT, border = 5)
        self.startXSc = wx.SpinCtrl(self.panel, value = '0')
        self.startXSc.SetRange(0, 100)
        hboxStartX.Add(self.startXSc)
        vbox1.Add(hboxStartX, 1, flag = wx.LEFT, border = 15)

        ## Y
        hboxStartY = wx.BoxSizer()
        startYLabel = wx.StaticText(self.panel, wx.ID_ANY, label = 'Start Y: ')
        hboxStartY.Add(startYLabel, 1, flag = wx.RIGHT, border = 15)
        self.startYSc = wx.SpinCtrl(self.panel, value = '0')
        self.startYSc.SetRange(0, 100)
        hboxStartY.Add(self.startYSc)
        vbox1.Add(hboxStartY, 1, flag = wx.LEFT, border = 15)

        ## Z
        hboxStartZ = wx.BoxSizer()
        startZLabel = wx.StaticText(self.panel, wx.ID_ANY, label = 'Start Z: ')
        hboxStartZ.Add(startZLabel, 1, flag = wx.RIGHT, border = 15)
        self.startZSc = wx.SpinCtrl(self.panel, value = '0')
        self.startZSc.SetRange(0, 100)
        hboxStartZ.Add(self.startZSc)
        vbox1.Add(hboxStartZ, 1, flag = wx.LEFT, border = 15)

        ## No. Cams
        hboxCameras = wx.BoxSizer()
        noCamsLabel = wx.StaticText(self.panel, wx.ID_ANY, label = 'No. Cams: ')
        hboxCameras.Add(noCamsLabel, 1, flag = wx.RIGHT, border = 5)
        self.noCamsSc = wx.SpinCtrl(self.panel, value = '0')
        self.noCamsSc.SetRange(0, 100)
        hboxCameras.Add(self.noCamsSc)
        vbox1.Add(hboxCameras, 1, flag = wx.LEFT, border = 15)

        ## buttons
        self.vertextPhotoCb = wx.CheckBox(self.panel, label = 'Take Photo at Each Vertex')
        vbox1.Add(self.vertextPhotoCb, 1, flag = wx.LEFT, border = 15)
        self.generateCBtn = wx.Button(self.panel, wx.ID_ANY, label = 'Generate Circle')
        vbox1.Add(self.generateCBtn, 1, flag = wx.LEFT, border = 15)
        self.generateSBtn = wx.Button(self.panel, wx.ID_ANY, label = 'Generate Sphere')
        vbox1.Add(self.generateSBtn, 1, flag = wx.LEFT, border = 15)

        self.panel.SetSizer(vbox1)
