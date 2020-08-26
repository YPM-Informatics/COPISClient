"""TODO"""

import wx


class PreferenceFrame(wx.Frame):
    def __init__(self, parent, *args, **kwargs):
        wx.Frame.__init__(self, parent, wx.ID_ANY, 'Preferences', size=(300, 360))
        self._glcanvas = parent.visualizer_panel.glcanvas

        self.init_panel()
        self.Centre()

    def init_panel(self):
        curr_dims = self._glcanvas.build_dimensions
        curr_scale = self._glcanvas.object_scale
        curr_proxy_style = self._glcanvas.proxy3d.style
        curr_proxy_dims = self._glcanvas.proxy3d.dimensions
        curr_proxy_color = self._glcanvas.proxy3d.color

        self.panel = wx.Panel(self, style=wx.BORDER_DEFAULT)

        self.boxsizer = wx.BoxSizer(wx.VERTICAL)

        # Build settings box
        build_settings_box = wx.BoxSizer(wx.VERTICAL)
        bs_sub_box = wx.BoxSizer()

        # Build Settings/Dimensions Box
        dims_box = wx.BoxSizer(wx.VERTICAL)
        dims_label = wx.StaticText(self.panel, wx.ID_ANY, label='Dimensions', style=wx.ALIGN_LEFT)
        dims_box.Add(dims_label, 1, flag=wx.BOTTOM, border=5)

        width_box = wx.BoxSizer()
        width_label = wx.StaticText(self.panel, wx.ID_ANY, label='Width: ')
        width_box.Add(width_label)
        self.width_sc = wx.SpinCtrl(self.panel, value=str(curr_dims[0]), size=(60, -1), min=0, max=1000, name="dw")
        width_box.Add(self.width_sc, 1, flag=wx.LEFT, border=6)

        length_box = wx.BoxSizer()
        length_label = wx.StaticText(self.panel, wx.ID_ANY, label='Length: ')
        length_box.Add(length_label)
        self.length_sc = wx.SpinCtrl(self.panel, value=str(curr_dims[1]), size=(60, -1), min=0, max=1000, name="dl")
        length_box.Add(self.length_sc)

        height_box = wx.BoxSizer()
        height_label = wx.StaticText(self.panel, wx.ID_ANY, label='Height: ')
        height_box.Add(height_label)
        self.height_sc = wx.SpinCtrl(self.panel, value=str(curr_dims[2]), size=(60, -1), min=0, max=1000, name="dh")
        height_box.Add(self.height_sc, 1, flag=wx.LEFT, border=1)

        dims_box.Add(width_box)
        dims_box.Add(length_box)
        dims_box.Add(height_box)
        bs_sub_box.Add(dims_box, 1, flag=wx.LEFT, border=15)

        # Build Settings/Origin Box
        origin_box = wx.BoxSizer(wx.VERTICAL)
        origin_label = wx.StaticText(self.panel, wx.ID_ANY, label='Origin', style=wx.ALIGN_LEFT)
        origin_box.Add(origin_label, 1, flag=wx.BOTTOM, border=5)

        x_box = wx.BoxSizer()
        x_label = wx.StaticText(self.panel, wx.ID_ANY, label='X: ')
        x_box.Add(x_label)
        self.x_sc = wx.SpinCtrl(self.panel, value=str(curr_dims[3]), size=(60, -1), min=0, max=1000, name='ox')
        x_box.Add(self.x_sc)

        y_box = wx.BoxSizer()
        y_label = wx.StaticText(self.panel, wx.ID_ANY, label='Y: ')
        y_box.Add(y_label)
        self.y_sc = wx.SpinCtrl(self.panel, value=str(curr_dims[4]), size=(60, -1), min=0, max=1000, name='oy')
        y_box.Add(self.y_sc, 1, flag=wx.LEFT, border=1)

        z_box = wx.BoxSizer()
        z_label = wx.StaticText(self.panel, wx.ID_ANY, label='Z: ')
        z_box.Add(z_label)
        self.z_sc = wx.SpinCtrl(self.panel, value=str(curr_dims[5]), size=(60, -1), min=0, max=1000, name='oz')
        z_box.Add(self.z_sc)

        origin_box.Add(x_box)
        origin_box.Add(y_box)
        origin_box.Add(z_box)
        bs_sub_box.Add(origin_box, 0, flag=wx.LEFT, border=50)

        build_settings_box.Add(bs_sub_box)

        build_static_sizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, 'Build Settings'), wx.HORIZONTAL)
        build_static_sizer.Add(build_settings_box)

        self.boxsizer.Add(build_static_sizer, 0, flag=wx.ALIGN_TOP|wx.ALL|wx.EXPAND, border=5)

        # Proxy Object Box
        proxy_obj_box = wx.BoxSizer(wx.VERTICAL)

        # Proxy Object/Style Box
        self.proxy_style_box = wx.BoxSizer()
        proxy_style_label = wx.StaticText(self.panel, wx.ID_ANY, label='Style: ')
        self.proxy_style_box.Add(proxy_style_label)
        self.proxy_style_combo = wx.ComboBox(self.panel, wx.ID_ANY, choices=['Sphere','Cylinder', 'Cube'], style=wx.CB_READONLY, value=curr_proxy_style)
        self.proxy_style_box.Add(self.proxy_style_combo, 1, flag=wx.BOTTOM, border=50)

        # Style/Sphere style options
        self.sphere_style_box = wx.BoxSizer()
        sphere_radius_label = wx.StaticText(self.panel, wx.ID_ANY, label='Radius: ')
        self.sphere_style_box.Add(sphere_radius_label)
        self.sphere_radius_sc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=0, max=1000, name='ps')
        self.sphere_style_box.Add(self.sphere_radius_sc)
        self.proxy_style_box.Add(self.sphere_style_box)

        # Hide sphere box or populate values
        if curr_proxy_style != 'Sphere':
            self.proxy_style_box.Hide(self.sphere_style_box)
        else:
            self.sphere_radius_sc.Value = curr_proxy_dims[0]

        # Style/Cylinder style options
        self.cylinder_style_box = wx.BoxSizer(wx.VERTICAL)

        cylinder_radius_box = wx.BoxSizer()
        cylinder_radius_label = wx.StaticText(self.panel, wx.ID_ANY, label='Radius: ')
        cylinder_radius_box.Add(cylinder_radius_label)
        self.cylinder_radius_sc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=0, max=1000, name='pcylr')
        cylinder_radius_box.Add(self.cylinder_radius_sc)

        cylinder_height_box = wx.BoxSizer()
        cylinder_height_label = wx.StaticText(self.panel, wx.ID_ANY, label='Height: ')
        cylinder_height_box.Add(cylinder_height_label)
        self.cylinder_height_sc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=0, max=1000, name='pcylh')
        cylinder_height_box.Add(self.cylinder_height_sc)


        self.cylinder_style_box.Add(cylinder_radius_box)
        self.cylinder_style_box.Add(cylinder_height_box)

        self.proxy_style_box.Add(self.cylinder_style_box)

        # Hide cylinder box or populate values
        if curr_proxy_style != 'Cylinder':
            self.proxy_style_box.Hide(self.cylinder_style_box)
        else:
            self.cylinder_radius_sc.Value = curr_proxy_dims[0]
            self.cylinder_height_sc.Value = curr_proxy_dims[1]

        # Style/Cube style options
        self.cube_style_box = wx.BoxSizer(wx.VERTICAL)

        cube_width_box = wx.BoxSizer()
        cube_width_label = wx.StaticText(self.panel, wx.ID_ANY, label='Width: ')
        cube_width_box.Add(cube_width_label)
        self.cube_width_sc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=0, max=1000, name='pcubw')
        cube_width_box.Add(self.cube_width_sc, 1, flag=wx.LEFT, border=6)

        cube_length_box = wx.BoxSizer()
        cube_length_label = wx.StaticText(self.panel, wx.ID_ANY, label='Length: ')
        cube_length_box.Add(cube_length_label)
        self.cube_length_sc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=0, max=1000, name='pcubl')
        cube_length_box.Add(self.cube_length_sc)

        cube_height_box = wx.BoxSizer()
        cube_height_label = wx.StaticText(self.panel, wx.ID_ANY, label='Height: ')
        cube_height_box.Add(cube_height_label)
        self.cube_height_sc = wx.SpinCtrl(self.panel, value='0', size=(60, -1), min=0, max=1000, name='pcubh')
        cube_height_box.Add(self.cube_height_sc, 1, flag=wx.LEFT, border=1)

        self.cube_style_box.Add(cube_width_box)
        self.cube_style_box.Add(cube_length_box)
        self.cube_style_box.Add(cube_height_box)

        self.proxy_style_box.Add(self.cube_style_box)
        self.proxy_style_box.Hide(self.cube_style_box)

        # Hide cube box or populate values
        if curr_proxy_style != 'Cube':
            self.proxy_style_box.Hide(self.cube_style_box)
        else:
            self.cube_width_sc.Value = curr_proxy_dims[0]
            self.cube_length_sc.Value = curr_proxy_dims[1]
            self.cube_height_sc.Value = curr_proxy_dims[2]

        # Proxy Object/Color box
        color_box = wx.BoxSizer()
        color_label = wx.StaticText(self.panel, wx.ID_ANY, label='RGB Color: ')
        color_box.Add(color_label)
        self.color_r_sc = wx.SpinCtrl(self.panel, value=str(curr_proxy_color[0]), size=(60, -1), min=0, max=255, name='pcolr')
        self.color_g_sc = wx.SpinCtrl(self.panel, value=str(curr_proxy_color[1]), size=(60, -1), min=0, max=255, name='pcolg')
        self.color_b_sc = wx.SpinCtrl(self.panel, value=str(curr_proxy_color[2]), size=(60, -1), min=0, max=255, name='pcolb')
        color_box.Add(self.color_r_sc)
        color_box.Add(self.color_g_sc)
        color_box.Add(self.color_b_sc)

        proxy_obj_box.Add(self.proxy_style_box, 0, flag=wx.LEFT, border=15)
        proxy_obj_box.Add(color_box, 0, flag=wx.LEFT, border=15)

        proxy_static_sizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, -1, 'Proxy Object'), wx.HORIZONTAL)
        proxy_static_sizer.Add(proxy_obj_box)

        self.boxsizer.Add(proxy_static_sizer, 0, flag=wx.ALIGN_TOP|wx.ALL|wx.EXPAND, border=5)

        # Camera box
        camera_box = wx.BoxSizer(wx.VERTICAL)

        scale_box = wx.BoxSizer()
        scale_label = wx.StaticText(self.panel, wx.ID_ANY, label='Scale: ')
        scale_box.Add(scale_label)
        self.scale_slider = wx.Slider(self.panel, wx.ID_ANY, curr_scale, 5, 50, size=(225, -1))
        scale_box.Add(self.scale_slider)

        camera_box.Add(scale_box, 1, flag=wx.LEFT, border=15)

        camera_static_sizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, 0, 'Virtual Cameras'), wx.HORIZONTAL)
        camera_static_sizer.Add(camera_box)

        self.boxsizer.Add(camera_static_sizer, 0, flag=wx.ALIGN_TOP|wx.ALL|wx.EXPAND, border=5)

        self.panel.Sizer = self.boxsizer

        self.Bind(wx.EVT_SPINCTRL, self.on_spin_control)
        self.Bind(wx.EVT_COMBOBOX, self.on_combo)
        self.Bind(wx.EVT_SLIDER, self.on_slider)

    def on_combo(self, event: wx.CommandEvent) -> None:
        # Populate the proxy style options for the selected style
        choice = event.String

        if choice == 'Sphere':
            self.proxy_style_box.Hide(self.cylinder_style_box)
            self.proxy_style_box.Hide(self.cube_style_box)
            self.proxy_style_box.Show(self.sphere_style_box)
            self.boxsizer.Layout()
        elif choice == 'Cylinder':
            self.proxy_style_box.Hide(self.cube_style_box)
            self.proxy_style_box.Hide(self.sphere_style_box)
            self.proxy_style_box.Show(self.cylinder_style_box)
            self.boxsizer.Layout()
        elif choice == 'Cube':
            self.proxy_style_box.Hide(self.sphere_style_box)
            self.proxy_style_box.Hide(self.cylinder_style_box)
            self.proxy_style_box.Show(self.cube_style_box)
            self.boxsizer.Layout()

    def on_spin_control(self, event):
        sc = event.EventObject
        name = sc.Name

        # Handles dimension spin controls
        if name[0] == 'd' or name[0] == 'o':
            self._glcanvas.build_dimensions = [self.width_sc.Value, self.length_sc.Value, self.height_sc.Value, self.x_sc.Value, self.y_sc.Value, self.z_sc.Value]
        # Handles proxy spin controls
        elif name[0] == 'p':
            self._glcanvas.proxy3d.style = self.proxy_style_combo.Value
            self._glcanvas.proxy3d.color = self._glcanvas.proxy3d.color = [self.color_r_sc.Value, self.color_g_sc.Value, self.color_b_sc.Value]
            if self.proxy_style_combo.Value == 'Sphere':
                self._glcanvas.proxy3d.dimensions = [self.sphere_radius_sc.Value]
            elif self.proxy_style_combo.Value == 'Cylinder':
                self._glcanvas.proxy3d.dimensions = [self.cylinder_radius_sc.Value, self.cylinder_height_sc.Value]
            elif self.proxy_style_combo.Value == 'Cube':
                self._glcanvas.proxy3d.dimensions = [self.cube_width_sc.Value, self.cube_length_sc.Value, self.cube_height_sc.Value]

    def on_slider(self, event):
        slider = event.EventObject
        self._glcanvas.object_scale = slider.Value
