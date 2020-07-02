import wx


class PathGeneratorFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Path Generator", size=(300, 400))
        self.SetMinSize(wx.Size(300, 400))
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
        self.panel = wx.Panel(self, style=wx.BORDER_SUNKEN)

        vbox1 = wx.BoxSizer(wx.VERTICAL)
        vbox1.Add((0,0))

        ## Label
        cGeneratorLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Generate a new path', style=wx.ALIGN_LEFT)
        cGeneratorLabel.SetFont(self.font)
        vbox1.Add(cGeneratorLabel, 1, flag=wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

        hboxStyle = wx.BoxSizer()
        styleLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Style: ')
        hboxStyle.Add(styleLabel, 1, flag=wx.RIGHT, border = 5)
        self.lineRb = wx.RadioButton(self.panel, label='Line', style=wx.RB_GROUP)
        self.cylRb = wx.RadioButton(self.panel, label='Cylinder')
        self.helixRb = wx.RadioButton(self.panel, label='Helix')
        hboxStyle.Add(self.lineRb)
        hboxStyle.Add(self.cylRb)
        hboxStyle.Add(self.helixRb)
        vbox1.Add(hboxStyle, 1, flag=wx.LEFT, border=15)

        ## StartXYZ
        hboxStartXYZ = wx.BoxSizer()
        startXYZLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Start XYZ: ')
        hboxStartXYZ.Add(startXYZLabel, 1, flag=wx.RIGHT, border=5)
        self.startXSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        self.startYSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        self.startZSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        hboxStartXYZ.Add(self.startXSc)
        hboxStartXYZ.Add(self.startYSc)
        hboxStartXYZ.Add(self.startZSc)
        vbox1.Add(hboxStartXYZ, 1, flag=wx.LEFT, border=15)

        ## EndXYZ
        hboxEndXYZ = wx.BoxSizer()
        endXYZLabel = wx.StaticText(self.panel, wx.ID_ANY, label='End XYZ: ')
        hboxEndXYZ.Add(endXYZLabel, 1, flag=wx.RIGHT, border=5)
        self.endXSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        self.endYSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        self.endZSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        hboxEndXYZ.Add(self.endXSc)
        hboxEndXYZ.Add(self.endYSc)
        hboxEndXYZ.Add(self.endZSc)
        vbox1.Add(hboxEndXYZ, 1, flag=wx.LEFT, border=15)


        ## No. Points
        hboxPoints = wx.BoxSizer()
        noPointsLabel = wx.StaticText(self.panel, wx.ID_ANY, label='# of Points: ')
        hboxPoints.Add(noPointsLabel, 1, flag=wx.RIGHT, border=5)
        self.noPointsSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22))
        self.noPointsSc.SetRange(0, 100)
        hboxPoints.Add(self.noPointsSc)
        vbox1.Add(hboxPoints, 1, flag=wx.LEFT, border=15)

        ## Radius
        # hboxRadius = wx.BoxSizer()
        # radiusLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Radius (mm): ')
        # hboxRadius.Add(radiusLabel, 1, flag=wx.RIGHT, border=5)
        # self.radiusSc = wx.SpinCtrl(self.panel, value='0')
        # self.radiusSc.SetRange(0, 100)
        # hboxRadius.Add(self.radiusSc)
        # vbox1.Add(hboxRadius, 1, flag=wx.LEFT, border=15)

        ## No. Cams
        hboxCameras = wx.BoxSizer()
        noCamsLabel = wx.StaticText(self.panel, wx.ID_ANY, label='# of Cams: ')
        hboxCameras.Add(noCamsLabel, 1, flag=wx.RIGHT, border=5)
        self.noCamsSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22))
        self.noCamsSc.SetRange(0, 100)
        hboxCameras.Add(self.noCamsSc)
        vbox1.Add(hboxCameras, 1, flag=wx.LEFT, border=15)

        ## buttons
        self.vertextPhotoCb = wx.CheckBox(self.panel, label='Take Photo at Each Vertex')
        vbox1.Add(self.vertextPhotoCb, 1, flag=wx.LEFT, border=15)

        self.generatePathBtn = wx.Button(self.panel, wx.ID_ANY, label='Generate Path')
        vbox1.Add(self.generatePathBtn, 1, flag=wx.LEFT, border=15)

        self.panel.SetSizer(vbox1)
