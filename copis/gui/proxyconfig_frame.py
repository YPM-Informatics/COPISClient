"""TODO"""

import wx
from pydispatch import dispatcher

class ProxyConfigFrame(wx.Frame):
    def __init__(self, parent, *args, **kwargs):
        wx.Frame.__init__(self, parent, wx.ID_ANY, 'Proxy Object Configuration', size=(300, 400))
        self.SetMinSize(wx.Size(300, 400))

        self.init_panel()
        self.Centre()

    def init_panel(self):
        self.panel = wx.Panel(self, style=wx.BORDER_DEFAULT)

        self.boxsizer = wx.BoxSizer(wx.VERTICAL)

        # add label
        proxyAdderLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Create a new proxy object')
        self.boxsizer.Add(proxyAdderLabel, 1, flag=wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

        # add style combobox
        hboxStyle = wx.BoxSizer()
        styleLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Style: ')
        hboxStyle.Add(styleLabel, 1, flag=wx.RIGHT|wx.TOP, border=6)
        self.styleCombo = wx.ComboBox(self.panel, wx.ID_ANY, choices=['Sphere', 'Cylinder', 'Cube', 'Bulldog'], style=wx.CB_READONLY)
        hboxStyle.Add(self.styleCombo)
        self.boxsizer.Add(hboxStyle, 1, flag=wx.LEFT, border=15)
        self.Bind(wx.EVT_COMBOBOX, self.onStyleRadioGroup)

        # add position xyz spinctrls
        self.hboxPosXYZ = wx.BoxSizer()
        posXYZLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Position XYZ: ')
        self.hboxPosXYZ.Add(posXYZLabel, 1, flag=wx.RIGHT|wx.TOP, border=6)
        self.posXSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=-200, max=200)
        self.posYSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=-200, max=200)
        self.posZSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=-200, max=200)
        self.hboxPosXYZ.Add(self.posXSc)
        self.hboxPosXYZ.Add(self.posYSc)
        self.hboxPosXYZ.Add(self.posZSc)
        self.boxsizer.Add(self.hboxPosXYZ, 1, flag=wx.LEFT, border=15)

        # add radius spinctrl
        self.hboxRadius = wx.BoxSizer()
        radiusLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Radius (mm): ')
        self.hboxRadius.Add(radiusLabel, 1, flag=wx.RIGHT|wx.TOP, border=6)
        self.radiusSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=1, max=200)
        self.hboxRadius.Add(self.radiusSc)
        self.boxsizer.Add(self.hboxRadius, 1, flag=wx.LEFT, border=15)
        self.boxsizer.Hide(self.hboxRadius)

        # add height spinctrl
        self.hboxHeight = wx.BoxSizer()
        heightLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Height (mm):  ')
        self.hboxHeight.Add(heightLabel, 1, flag=wx.RIGHT|wx.TOP, border=6)
        self.heightSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=1, max=50)
        self.hboxHeight.Add(self.heightSc)
        self.boxsizer.Add(self.hboxHeight, 1, flag=wx.LEFT, border=15)
        self.boxsizer.Hide(self.hboxHeight)

        # add side length spinctrl
        self.hboxSideLength = wx.BoxSizer()
        sideLengthLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Side Length (mm): ')
        self.hboxSideLength.Add(sideLengthLabel, 1, flag=wx.RIGHT, border=5)
        self.sideLengthSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=1, max=100)
        self.hboxSideLength.Add(self.sideLengthSc)
        self.boxsizer.Add(self.hboxSideLength, flag=wx.LEFT|wx.BOTTOM, border=15)
        self.boxsizer.Hide(self.hboxSideLength)

        # add create object button
        self.createObjectBtn = wx.Button(self.panel, wx.ID_ANY, label='Create Object')
        self.boxsizer.Add(self.createObjectBtn, 1, flag=wx.LEFT, border=15)
        self.createObjectBtn.Bind(wx.EVT_BUTTON, self.on_create_object)

        self.panel.Sizer = self.boxsizer

    def onStyleRadioGroup(self, event):
        choice = self.styleCombo.StringSelection

        if choice == 'Sphere':
            self.boxsizer.Show(self.hboxRadius)
            self.boxsizer.Hide(self.hboxHeight)
            self.boxsizer.Hide(self.hboxSideLength)
            self.boxsizer.Layout()
        elif choice == 'Cylinder':
            self.boxsizer.Show(self.hboxRadius)
            self.boxsizer.Show(self.hboxHeight)
            self.boxsizer.Hide(self.hboxSideLength)
            self.boxsizer.Layout()
        elif choice == 'Cube':
            self.boxsizer.Show(self.hboxSideLength)
            self.boxsizer.Hide(self.hboxRadius)
            self.boxsizer.Hide(self.hboxHeight)
            self.boxsizer.Layout()
        else:
            self.boxsizer.Hide(self.hboxSideLength)
            self.boxsizer.Hide(self.hboxRadius)
            self.boxsizer.Hide(self.hboxHeight)

    def on_create_object(self, even: wx.CommandEvent) -> None:
        choice = self.styleCombo.StringSelection
        if choice == 'Sphere':
            wx.GetApp().c.add_proxy(0, '', [self.posXSc.GetValue(), self.posXSc.GetValue(), self.posXSc.GetValue(), 0, 0], self.radiusSc.GetValue(),
                self.radiusSc.GetValue())
            self.Destroy()
        elif choice == 'Cylinder':
            wx.GetApp().c.add_proxy(1, '', [self.posXSc.GetValue(), self.posXSc.GetValue(), self.posXSc.GetValue(), 0, 0], self.radiusSc.GetValue(),
                self.heightSc.GetValue())
            self.Destroy()
        elif choice == 'Cube':
            wx.GetApp().c.add_proxy(2, '', [self.posXSc.GetValue(), self.posXSc.GetValue(), self.posXSc.GetValue(), 0, 0], self.sideLengthSc.GetValue(),
                self.sideLengthSc.GetValue())
            self.Destroy()
        elif choice == 'Bulldog':
            wx.GetApp().c.add_proxy(3, '', [self.posXSc.GetValue(), self.posXSc.GetValue(), self.posXSc.GetValue(), 0, 0], 1, 1)
