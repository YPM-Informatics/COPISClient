#!/usr/bin/env python3

import wx
# from wx.lib.pubsub import Publisher


class PreferenceFrame(wx.Frame):
    def __init__(self, main_frame=None):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Preferences')
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
        build_settings_label = wx.StaticText(self.panel, wx.ID_ANY, label='Customize your build settings', style=wx.ALIGN_LEFT)
        build_settings_label.SetFont(self.font)
        build_settings_box.Add(build_settings_label, 1, flag=wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

        bs_sub_box = wx.BoxSizer()

        # Dimensions Box
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

        # Origin Box
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
        bs_sub_box.Add(origin_box, 1, flag = wx.LEFT, border=50)

        build_settings_box.Add(bs_sub_box)
        self.vbox1.Add(build_settings_box, 1)

        # Build Prim Box
        proxy_obj_box = wx.BoxSizer(wx.VERTICAL)
        proxy_obj_label = wx.StaticText(self.panel, wx.ID_ANY, label='Customize your proxy object', style=wx.ALIGN_LEFT)
        proxy_obj_label.SetFont(self.font)
        proxy_obj_box.Add(proxy_obj_label, 1, flag=wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

        # Style
        self.proxy_style_box = wx.BoxSizer()
        proxy_style_label = wx.StaticText(self.panel, wx.ID_ANY, label='Style: ')
        self.proxy_style_box.Add(proxy_style_label)
        self.proxy_style_combo = wx.ComboBox(self.panel, wx.ID_ANY, choices=['Sphere','Cylinder', 'Cube'], style=wx.CB_READONLY)
        self.proxy_style_box.Add(self.proxy_style_combo)
        proxy_obj_box.Add(self.proxy_style_box, 1, flag=wx.LEFT, border=15)
        self.Bind(wx.EVT_COMBOBOX, self.onStyleCombo)

        # Sphere style options
        self.sphere_style_box = wx.BoxSizer()
        sphere_radius_label = wx.StaticText(self.panel, wx.ID_ANY, label='Radius: ')
        self.sphere_style_box.Add(sphere_radius_label)
        self.sphere_radius_sc = wx.SpinCtrl(self.panel, value='0', size=wx.Size(60, 22), min=0, max=1000)
        self.sphere_style_box.Add(self.sphere_radius_sc)
        # TO DO: Bind Update Event
        self.proxy_style_box.Add(self.sphere_style_box)

        # Cylinder style options
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

        # Cube style options
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

        self.vbox1.Add(proxy_obj_box, 1)

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
