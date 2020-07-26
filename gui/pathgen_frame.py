#!/usr/bin/env python3

import wx


class PathGeneratorFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Path Generator', size=(300, 400))
        self.SetMinSize(wx.Size(300, 400))
        self.font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(15)

        self.init_panel()
        self.Centre()

    def init_panel(self):
        self.panel = wx.Panel(self, style=wx.BORDER_SUNKEN)

        self.vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.vbox1.Add((0,0))

        # Label
        cGeneratorLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Generate a new path', style=wx.ALIGN_LEFT)
        cGeneratorLabel.SetFont(self.font)
        self.vbox1.Add(cGeneratorLabel, 1, flag=wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

        # Style
        hboxStyle = wx.BoxSizer()
        styleLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Style: ')
        hboxStyle.Add(styleLabel, 1, flag=wx.RIGHT | wx.TOP, border = 6)
        self.styleCombo = wx.ComboBox(self.panel, wx.ID_ANY, choices=['Line', 'Sphere','Cylinder', 'Helix', 'Cube', 'Grid'], style=wx.CB_READONLY)
        hboxStyle.Add(self.styleCombo)
        self.vbox1.Add(hboxStyle, 1, flag=wx.LEFT, border=15)
        self.Bind(wx.EVT_COMBOBOX, self.onStyleRadioGroup)

        # StartXYZ
        hboxStartXYZ = wx.BoxSizer()
        startXYZLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Start XYZ: ')
        hboxStartXYZ.Add(startXYZLabel, 1, flag=wx.RIGHT | wx.TOP, border=6)
        self.startXSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        self.startYSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        self.startZSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        hboxStartXYZ.Add(self.startXSc)
        hboxStartXYZ.Add(self.startYSc)
        hboxStartXYZ.Add(self.startZSc)
        self.vbox1.Add(hboxStartXYZ, 1, flag=wx.LEFT, border=15)

        # EndXYZ
        hboxEndXYZ = wx.BoxSizer()
        endXYZLabel = wx.StaticText(self.panel, wx.ID_ANY, label='End XYZ: ')
        hboxEndXYZ.Add(endXYZLabel, 1, flag=wx.RIGHT | wx.TOP, border=6)
        self.endXSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        self.endYSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        self.endZSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=-1, max=1)
        hboxEndXYZ.Add(self.endXSc)
        hboxEndXYZ.Add(self.endYSc)
        hboxEndXYZ.Add(self.endZSc)
        self.vbox1.Add(hboxEndXYZ, 1, flag=wx.LEFT, border=15)

        # Radius
        self.hboxRadius = wx.BoxSizer()
        radiusLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Radius (mm): ')
        self.hboxRadius.Add(radiusLabel, 1, flag=wx.RIGHT | wx.TOP, border=6)
        self.radiusSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=1, max=100)
        self.hboxRadius.Add(self.radiusSc)
        self.vbox1.Add(self.hboxRadius, 1, flag=wx.LEFT, border=15)
        self.vbox1.Hide(self.hboxRadius)

        # No. Circles
        self.hboxNCircle = wx.BoxSizer()
        nCircleLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Circles:  ')
        self.hboxNCircle.Add(nCircleLabel, 1, flag=wx.RIGHT | wx.TOP, border=6)
        self.nCircleSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60,22), min=1, max=1000)
        self.hboxNCircle.Add(self.nCircleSc)
        self.vbox1.Add(self.hboxNCircle, 1, flag=wx.LEFT, border=15)
        self.vbox1.Hide(self.hboxNCircle)

        # Points per circle
        self.hboxPointsCircle = wx.BoxSizer()
        pointsCircleLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Points per circle: ')
        self.hboxPointsCircle.Add(pointsCircleLabel, 1, flag=wx.RIGHT, border=5)
        self.pointsCircleSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60,22), min=1, max=1000)
        self.hboxPointsCircle.Add(self.pointsCircleSc)
        self.vbox1.Add(self.hboxPointsCircle, flag=wx.LEFT | wx.BOTTOM, border=25)
        self.vbox1.Hide(self.hboxPointsCircle)

        # No. Points
        hboxPoints = wx.BoxSizer()
        noPointsLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Points: ')
        hboxPoints.Add(noPointsLabel, 1, flag=wx.RIGHT | wx.TOP, border=6)
        self.noPointsSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22))
        self.noPointsSc.SetRange(0, 100)
        hboxPoints.Add(self.noPointsSc)
        self.vbox1.Add(hboxPoints, 1, flag=wx.LEFT, border=15)

        # No. Cams
        hboxCameras = wx.BoxSizer()
        noCamsLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Cams: ')
        hboxCameras.Add(noCamsLabel, 1, flag=wx.RIGHT | wx.TOP, border=6)
        self.noCamsSc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22))
        self.noCamsSc.SetRange(0, 100)
        hboxCameras.Add(self.noCamsSc)
        self.vbox1.Add(hboxCameras, 1, flag=wx.LEFT, border=15)

        # buttons
        self.vertextPhotoCb = wx.CheckBox(self.panel, label='Take Photo at Each Vertex')
        self.vbox1.Add(self.vertextPhotoCb, 1, flag=wx.LEFT, border=15)

        self.generatePathBtn = wx.Button(self.panel, wx.ID_ANY, label='Generate Path')
        self.vbox1.Add(self.generatePathBtn, 1, flag=wx.LEFT, border=15)

        self.panel.SetSizer(self.vbox1)

    def onStyleRadioGroup(self, event):
        choice = self.styleCombo.GetStringSelection()

        if choice == 'Cylinder' or choice == 'Sphere':
            self.vbox1.Show(self.hboxRadius)
            self.vbox1.Show(self.hboxNCircle)
            self.vbox1.Show(self.hboxPointsCircle)
            self.vbox1.Layout()
        elif choice == 'Helix':
            self.vbox1.Show(self.hboxRadius)
            self.vbox1.Hide(self.hboxNCircle)
            self.vbox1.Hide(self.hboxPointsCircle)
            self.vbox1.Layout()
        else:
            self.vbox1.Hide(self.hboxRadius)
            self.vbox1.Hide(self.hboxNCircle)
            self.vbox1.Hide(self.hboxPointsCircle)
            self.vbox1.Layout()
