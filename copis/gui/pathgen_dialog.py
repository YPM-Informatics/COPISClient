# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

import wx
from copis.gui.wxutils import simple_statictext


class PathgenDialog(wx.Dialog):

    path_types = [
        'Line',
        'Sphere',
        'Cylinder',
        'Helix',
        'Cube',
        'Grid',
    ]

    def __init__(self, parent, *args, **kwargs):
        """Inits PathgenDialog with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Path', size=(400, 300))
        self.p = parent
        self.c = self.p.c

        self.setting_sizers = {}

        # self.SetMinSize(wx.Size(300, 400))
        # self._camera_num_choices = list(map(lambda x: x.device_name, self.c.devices))
        self._camera_num_choices = list(range(len(self.c.devices)))
        print(self._camera_num_choices)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.init_gui()

        self.Layout()
        self.Centre(wx.BOTH)

    def init_gui(self):
        """Initialize dialog."""

        path_select_grid = wx.FlexGridSizer(2, 2, 4, 8)
        path_select_grid.AddGrowableCol(1, 0)

        self.path_type_choice = wx.Choice(self, choices=self.path_types)
        self.camera_num_choice = wx.Choice(self, choices=self._camera_num_choices)

        path_select_grid.AddMany([
            (simple_statictext(self, 'Path Shape:', 80), 0, wx.EXPAND, 0),
            (self.path_type_choice, 0, wx.EXPAND, 0),

            (simple_statictext(self, '# Cameras:', 80), 0, wx.EXPAND, 0),
            (self.camera_num_choice, 0, wx.EXPAND, 0),
        ])

        self.Sizer.Add(path_select_grid, 1, wx.ALL | wx.EXPAND, 4)

        self.Sizer.AddSpacer(20)
        button_sizer = self.CreateButtonSizer(wx.APPLY | wx.OK | wx.CANCEL)

        self.Sizer.Add(button_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 0)

        self.setting_sizers['Radius'] = wx.BoxSizer(wx.HORIZONTAL)
        self.setting_sizers['Radius'] = wx.BoxSizer(wx.HORIZONTAL)
        self.setting_sizers['Radius'] = wx.BoxSizer(wx.HORIZONTAL)

        # self.button_sizer.Realize()
        # self.panel.Sizer.Add(self.button_sizer)


    #     # add label
    #     cGeneratorLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Generate a new path', style=wx.ALIGN_LEFT)
    #     self.boxsizer.Add(cGeneratorLabel, 1, flag=wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

    #     # add style combobox
    #     hboxStyle = wx.BoxSizer()
    #     styleLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Style: ')
    #     hboxStyle.Add(styleLabel, 1, flag=wx.RIGHT|wx.TOP, border=6)
    #     self.styleCombo = wx.ComboBox(self.panel, wx.ID_ANY, choices=['Line', 'Sphere', 'Cylinder', 'Helix', 'Cube', 'Grid'], style=wx.CB_READONLY)
    #     hboxStyle.Add(self.styleCombo)
    #     self.boxsizer.Add(hboxStyle, 1, flag=wx.LEFT, border=15)
    #     self.Bind(wx.EVT_COMBOBOX, self.onStyleRadioGroup)

    #     # add start xyz spinctrls
    #     hboxStartXYZ = wx.BoxSizer()
    #     startXYZLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Start XYZ: ')
    #     hboxStartXYZ.Add(startXYZLabel, 1, flag=wx.RIGHT|wx.TOP, border=6)
    #     self.startXSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=-1, max=1)
    #     self.startYSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=-1, max=1)
    #     self.startZSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=-1, max=1)
    #     hboxStartXYZ.Add(self.startXSc)
    #     hboxStartXYZ.Add(self.startYSc)
    #     hboxStartXYZ.Add(self.startZSc)
    #     self.boxsizer.Add(hboxStartXYZ, 1, flag=wx.LEFT, border=15)

    #     # add end xyz spinctrls
    #     hboxEndXYZ = wx.BoxSizer()
    #     endXYZLabel = wx.StaticText(self.panel, wx.ID_ANY, label='End XYZ: ')
    #     hboxEndXYZ.Add(endXYZLabel, 1, flag=wx.RIGHT|wx.TOP, border=6)
    #     self.endXSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=-1, max=1)
    #     self.endYSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=-1, max=1)
    #     self.endZSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=-1, max=1)
    #     hboxEndXYZ.Add(self.endXSc)
    #     hboxEndXYZ.Add(self.endYSc)
    #     hboxEndXYZ.Add(self.endZSc)
    #     self.boxsizer.Add(hboxEndXYZ, 1, flag=wx.LEFT, border=15)

    #     # add radius spinctrl
    #     self.hboxRadius = wx.BoxSizer()
    #     radiusLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Radius (mm): ')
    #     self.hboxRadius.Add(radiusLabel, 1, flag=wx.RIGHT|wx.TOP, border=6)
    #     self.radiusSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=1, max=100)
    #     self.hboxRadius.Add(self.radiusSc)
    #     self.boxsizer.Add(self.hboxRadius, 1, flag=wx.LEFT, border=15)
    #     self.boxsizer.Hide(self.hboxRadius)

    #     # add no circles spinctrl
    #     self.hboxNCircle = wx.BoxSizer()
    #     nCircleLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Circles:  ')
    #     self.hboxNCircle.Add(nCircleLabel, 1, flag=wx.RIGHT|wx.TOP, border=6)
    #     self.nCircleSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=1, max=1000)
    #     self.hboxNCircle.Add(self.nCircleSc)
    #     self.boxsizer.Add(self.hboxNCircle, 1, flag=wx.LEFT, border=15)
    #     self.boxsizer.Hide(self.hboxNCircle)

    #     # add points per circle spinctrl
    #     self.hboxPointsCircle = wx.BoxSizer()
    #     pointsCircleLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Points per circle: ')
    #     self.hboxPointsCircle.Add(pointsCircleLabel, 1, flag=wx.RIGHT, border=5)
    #     self.pointsCircleSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=1, max=1000)
    #     self.hboxPointsCircle.Add(self.pointsCircleSc)
    #     self.boxsizer.Add(self.hboxPointsCircle, flag=wx.LEFT|wx.BOTTOM, border=25)
    #     self.boxsizer.Hide(self.hboxPointsCircle)

    #     # add no points spinctrl
    #     hboxPoints = wx.BoxSizer()
    #     noPointsLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Points: ')
    #     hboxPoints.Add(noPointsLabel, 1, flag=wx.RIGHT|wx.TOP, border=6)
    #     self.noPointsSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1))
    #     self.noPointsSc.SetRange(0, 100)
    #     hboxPoints.Add(self.noPointsSc)
    #     self.boxsizer.Add(hboxPoints, 1, flag=wx.LEFT, border=15)

    #     # add no cams spinctrl
    #     hboxCameras = wx.BoxSizer()
    #     noCamsLabel = wx.StaticText(self.panel, wx.ID_ANY, label='Cams: ')
    #     hboxCameras.Add(noCamsLabel, 1, flag=wx.RIGHT|wx.TOP, border=6)
    #     self.noCamsSc = wx.SpinCtrl(self.panel, value='0', size=(60, -1))
    #     self.noCamsSc.SetRange(0, 100)
    #     hboxCameras.Add(self.noCamsSc)
    #     self.boxsizer.Add(hboxCameras, 1, flag=wx.LEFT, border=15)

    #     # add buttons
    #     self.vertextPhotoCb = wx.CheckBox(self.panel, label='Take Photo at Each Vertex')
    #     self.boxsizer.Add(self.vertextPhotoCb, 1, flag=wx.LEFT, border=15)
    #     self.generatePathBtn = wx.Button(self.panel, wx.ID_ANY, label='Generate Path')
    #     self.boxsizer.Add(self.generatePathBtn, 1, flag=wx.LEFT, border=15)

    #     self.panel.Sizer = self.boxsizer

    # def onStyleRadioGroup(self, event):
    #     choice = self.styleCombo.StringSelection

    #     if choice == 'Cylinder' or choice == 'Sphere':
    #         self.boxsizer.Show(self.hboxRadius)
    #         self.boxsizer.Show(self.hboxNCircle)
    #         self.boxsizer.Show(self.hboxPointsCircle)
    #         self.boxsizer.Layout()
    #     elif choice == 'Helix':
    #         self.boxsizer.Show(self.hboxRadius)
    #         self.boxsizer.Hide(self.hboxNCircle)
    #         self.boxsizer.Hide(self.hboxPointsCircle)
    #         self.boxsizer.Layout()
    #     else:
    #         self.boxsizer.Hide(self.hboxRadius)
    #         self.boxsizer.Hide(self.hboxNCircle)
    #         self.boxsizer.Hide(self.hboxPointsCircle)
    #         self.boxsizer.Layout()
