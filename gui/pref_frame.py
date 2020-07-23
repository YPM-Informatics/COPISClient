#!/usr/bin/env python3

import wx
# from wx.lib.pubsub import Publisher

class PreferenceFrame(wx.Frame):
    def __init__(self, main_frame=None):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Preferences', size=(300, 360))
        self.main_frame = main_frame
        self.font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(15)

        self.init_panel()
        self.Centre()

    def init_panel(self):
        self.panel = wx.Panel(self, style=wx.BORDER_SUNKEN)

        self.vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.vbox1.Add((0,0))

        # Build settings box
        build_settings_box = wx.BoxSizer(wx.VERTICAL)
        bs_sub_box = wx.BoxSizer()

        # Build Settings/Dimensions Box
        dims_box = wx.BoxSizer(wx.VERTICAL)
        dims_label = wx.StaticText(self.panel, wx.ID_ANY, label='Dimensions', style=wx.ALIGN_LEFT)
        dims_box.Add(dims_label, 1, flag = wx.BOTTOM, border=5)

        width_box = wx.BoxSizer()
        width_label = wx.StaticText(self.panel, wx.ID_ANY, label='Width: ')
        width_box.Add(width_label)
        self.width_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        width_box.Add(self.width_sc, 1, flag = wx.LEFT, border=6)

        length_box = wx.BoxSizer()
        length_label = wx.StaticText(self.panel, wx.ID_ANY, label='Length: ')
        length_box.Add(length_label)
        self.length_sc= wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        length_box.Add(self.length_sc)

        height_box = wx.BoxSizer()
        height_label =  wx.StaticText(self.panel, wx.ID_ANY, label='Height: ')
        height_box.Add(height_label)
        self.height_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        height_box.Add(self.height_sc, 1, flag = wx.LEFT, border=1)

        dims_box.Add(width_box)
        dims_box.Add(length_box)
        dims_box.Add(height_box)
        bs_sub_box.Add(dims_box, 1, flag = wx.LEFT, border=15)

        # Build Settings/Origin Box
        origin_box = wx.BoxSizer(wx.VERTICAL)
        origin_label = wx.StaticText(self.panel, wx.ID_ANY, label='Origin', style=wx.ALIGN_LEFT)
        origin_box.Add(origin_label, 1, flag = wx.BOTTOM, border=5)

        x_box = wx.BoxSizer()
        x_label = wx.StaticText(self.panel, wx.ID_ANY, label='X: ')
        x_box.Add(x_label)
        self.x_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        x_box.Add(self.x_sc)

        y_box = wx.BoxSizer()
        y_label = wx.StaticText(self.panel, wx.ID_ANY, label='Y: ')
        y_box.Add(y_label)
        self.y_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        y_box.Add(self.y_sc, 1, flag = wx.LEFT, border=1)

        z_box = wx.BoxSizer()
        z_label = wx.StaticText(self.panel, wx.ID_ANY, label='X: ')
        z_box.Add(z_label)
        self.z_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        z_box.Add(self.z_sc)

        origin_box.Add(x_box)
        origin_box.Add(y_box)
        origin_box.Add(z_box)
        bs_sub_box.Add(origin_box, 0, flag = wx.LEFT, border=50)

        build_settings_box.Add(bs_sub_box)

        build_static_box = wx.StaticBox(self.panel, -1, 'Build Settings')
        build_static_sizer = wx.StaticBoxSizer(build_static_box, wx.HORIZONTAL)
        build_static_sizer.Add(build_settings_box)

        self.vbox1.Add(build_static_sizer, 0, flag=wx.ALIGN_TOP | wx.TOP | wx.BOTTOM | wx.EXPAND, border=5)

        # Proxy Object Box
        proxy_obj_box = wx.BoxSizer(wx.VERTICAL)

        # Proxy Object/Style Box
        self.proxy_style_box = wx.BoxSizer()
        proxy_style_label = wx.StaticText(self.panel, wx.ID_ANY, label='Style: ')
        self.proxy_style_box.Add(proxy_style_label)
        self.proxy_style_combo = wx.ComboBox(self.panel, wx.ID_ANY, choices=['Sphere','Cylinder', 'Cube'], style=wx.CB_READONLY)
        self.proxy_style_box.Add(self.proxy_style_combo, 1, flag=wx.BOTTOM, border=50)
        self.Bind(wx.EVT_COMBOBOX, self.onStyleCombo)

        # Style/Sphere style options
        self.sphere_style_box = wx.BoxSizer()
        sphere_radius_label = wx.StaticText(self.panel, wx.ID_ANY, label='Radius: ')
        self.sphere_style_box.Add(sphere_radius_label)
        self.sphere_radius_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        self.sphere_style_box.Add(self.sphere_radius_sc)
        # TO DO: Bind Update Event
        self.proxy_style_box.Add(self.sphere_style_box)

        # Style/Cylinder style options
        self.cylinder_style_box = wx.BoxSizer(wx.VERTICAL)

        cylinder_radius_box = wx.BoxSizer()
        cylinder_radius_label = wx.StaticText(self.panel, wx.ID_ANY, label='Radius: ')
        cylinder_radius_box.Add(cylinder_radius_label)
        self.cylinder_radius_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        cylinder_radius_box.Add(self.cylinder_radius_sc)
        # TO DO: Bind Update Event

        cylinder_height_box = wx.BoxSizer()
        cylinder_height_label = wx.StaticText(self.panel, wx.ID_ANY, label='Height: ')
        cylinder_height_box.Add(cylinder_height_label)
        self.cylinder_height_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        cylinder_height_box.Add(self.cylinder_height_sc)
        # TO DO: Bind Update Event

        self.cylinder_style_box.Add(cylinder_radius_box)
        self.cylinder_style_box.Add(cylinder_height_box)

        self.proxy_style_box.Add(self.cylinder_style_box)
        self.proxy_style_box.Hide(self.cylinder_style_box)

        # Style/Cube style options
        self.cube_style_box = wx.BoxSizer(wx.VERTICAL)

        cube_width_box = wx.BoxSizer()
        cube_width_label = wx.StaticText(self.panel, wx.ID_ANY, label='Width: ')
        cube_width_box.Add(cube_width_label)
        self.cube_width_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        cube_width_box.Add(self.cube_width_sc, 1, flag = wx.LEFT, border=6)

        cube_length_box = wx.BoxSizer()
        cube_length_label = wx.StaticText(self.panel, wx.ID_ANY, label='Length: ')
        cube_length_box.Add(cube_length_label)
        self.cube_length_sc= wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        cube_length_box.Add(self.cube_length_sc)

        cube_height_box = wx.BoxSizer()
        cube_height_label =  wx.StaticText(self.panel, wx.ID_ANY, label='Height: ')
        cube_height_box.Add(cube_height_label)
        self.cube_height_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        cube_height_box.Add(self.cube_height_sc, 1, flag = wx.LEFT, border=1)

        self.cube_style_box.Add(cube_width_box)
        self.cube_style_box.Add(cube_length_box)
        self.cube_style_box.Add(cube_height_box)

        self.proxy_style_box.Add(self.cube_style_box)
        self.proxy_style_box.Hide(self.cube_style_box)

        # Proxy Object/Color box
        color_box = wx.BoxSizer()
        color_label = wx.StaticText(self.panel, wx.ID_ANY, label='RGB Color: ')
        color_box.Add(color_label)
        self.color_r_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=255)
        self.color_g_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=255)
        self.color_b_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=255)
        color_box.Add(self.color_r_sc)
        color_box.Add(self.color_g_sc)
        color_box.Add(self.color_b_sc)

        proxy_obj_box.Add(self.proxy_style_box, 0, flag=wx.LEFT, border=15)
        proxy_obj_box.Add(color_box, 0, flag=wx.LEFT, border=15)

        proxy_static_box = wx.StaticBox(self.panel, -1, 'Proxy Object')
        proxy_static_sizer = wx.StaticBoxSizer(proxy_static_box, wx.HORIZONTAL)
        proxy_static_sizer.Add(proxy_obj_box)

        self.vbox1.Add(proxy_static_sizer, 0, flag=wx.ALIGN_TOP | wx.TOP | wx.BOTTOM | wx.EXPAND, border=5)
        
        # Camera box
        camera_box = wx.BoxSizer(wx.VERTICAL)

        scale_box = wx.BoxSizer()
        scale_label = wx.StaticText(self.panel, wx.ID_ANY, label='Scale: ')
        scale_box.Add(scale_label)
        self.scale_slider = wx.Slider(self.panel, value=0, minValue=0, maxValue=100)
        scale_box.Add(self.scale_slider)

        camera_box.Add(scale_box, 1, flag=wx.LEFT, border=15)

        camera_static_box = wx.StaticBox(self.panel, 0, 'Virtual Cameras')
        camera_static_sizer = wx.StaticBoxSizer(camera_static_box, wx.HORIZONTAL)
        camera_static_sizer.Add(camera_box)

        self.vbox1.Add(camera_static_sizer, 0, flag=wx.ALIGN_TOP | wx.TOP | wx.BOTTOM | wx.EXPAND, border=5)

        self.panel.SetSizer(self.vbox1)

    def onStyleCombo(self, event):
        choice = self.proxy_style_combo.GetStringSelection()

        if choice == 'Sphere':
            self.proxy_style_box.Hide(self.cylinder_style_box)
            self.proxy_style_box.Hide(self.cube_style_box)
            self.proxy_style_box.Show(self.sphere_style_box)
            self.vbox1.Layout()
        elif choice == 'Cylinder':
            self.proxy_style_box.Hide(self.cube_style_box)
            self.proxy_style_box.Hide(self.sphere_style_box)
            self.proxy_style_box.Show(self.cylinder_style_box)
            self.vbox1.Layout()
        elif choice == 'Cube':
            self.proxy_style_box.Hide(self.sphere_style_box)
            self.proxy_style_box.Hide(self.cylinder_style_box)      
            self.proxy_style_box.Show(self.cube_style_box)  
            self.vbox1.Layout()  
