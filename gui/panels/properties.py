"""TODO"""

import wx


class PropertiesPanel(wx.Panel):
    """TODO

    """

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits PropertiesPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)

        self.parent = parent
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.init_gui()

        self.SetSizer(self.main_sizer)
        self.Layout()

    def init_gui(self) -> None:
        camera_control_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Camera Control'), wx.VERTICAL)

        hbox = wx.BoxSizer()
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.remoteRb = wx.RadioButton(self, label='Remote Shutter', style=wx.RB_GROUP)
        vbox1.Add(self.remoteRb)

        vboxAFShutter = wx.BoxSizer()
        self.af_btn = wx.Button(self, label='A/F', size=(-1, -1))
        vboxAFShutter.Add(self.af_btn)
        self.shutter_btn = wx.Button(self, label='Shutter', size=(-1, -1))
        vboxAFShutter.Add(self.shutter_btn)
        vbox1.Add(vboxAFShutter, 1, flag=wx.LEFT, border=5)

        self.usb_rb = wx.RadioButton(self, label='USB')
        vbox1.Add(self.usb_rb)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_remote_usb_radio_group)

        self.edsdk_rb = wx.RadioButton(self, label='EDSDK', style=wx.RB_GROUP)
        vbox1.Add(self.edsdk_rb, flag=wx.LEFT | wx.TOP, border=10)
        self.edsdk_rb.SetValue(False)
        self.edsdk_rb.Disable()

        self.ptp_rbh = wx.RadioButton(self, label='PTP')
        vbox1.Add(self.ptp_rbh, flag=wx.LEFT | wx.TOP, border=10)
        self.ptp_rbh.Disable()

        hboxF = wx.BoxSizer()
        self.frBtn = wx.Button(self, label='Focus-', size=(-1, -1))
        hboxF.Add(self.frBtn)
        self.fiBtn = wx.Button(self, label='Focus+', size=(-1, -1))
        hboxF.Add(self.fiBtn)
        vbox1.Add(hboxF, 1, flag=wx.TOP, border=15)
        hbox.Add(vbox1, 1, flag=wx.LEFT, border=30)

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        self.takePictureBtn = wx.Button(self, wx.ID_ANY, label='Take Picture')
        vbox2.Add(self.takePictureBtn)
        self.takePictureBtn.Bind(wx.EVT_BUTTON, self.on_take_picture)

        self.startEvfBtn = wx.Button(self, wx.ID_ANY, label='Start Liveview')
        vbox2.Add(self.startEvfBtn)
        self.startEvfBtn.Bind(wx.EVT_BUTTON, self.on_start_evf)
        hbox.Add(vbox2, 1, flag=wx.LEFT, border=10)

        camera_control_sizer.Add(hbox, 0, wx.ALL | wx.EXPAND, 5)
        self.main_sizer.Add(camera_control_sizer, 0, wx.ALL | wx.EXPAND, 5)

    def on_remote_usb_radio_group(self, event: wx.CommandEvent) -> None:
        rb = event.EventObject

        # self.visualizer_panel.on_clear_cameras()
        self.main_combo.Clear()

        if rb.Label == 'USB':
            self.edsdk_rb.Enable()
            self.ptp_rbh.Enable()
        elif rb.Label == 'Remote Shutter':
            self.edsdk_rb.SetValue(False)
            self.ptp_rbh.SetValue(False)
            self.edsdk_rb.Disable()
            self.ptp_rbh.Disable()

            if self.parent.is_edsdk_on:
                self.parent.terminate_edsdk()
        elif rb.Label == 'EDSDK':
            self.parent.initEDSDK()
        else:
            if self.parent.is_edsdk_on:
                self.parent.terminate_edsdk()

    def on_take_picture(self, event: wx.CommandEvent) -> None:
        camera = self.main_combo.Selection
        if self.parent.get_selected_camera() is not None:
            self.parent.get_selected_camera().shoot()
        else:
            set_dialog('Please select the camera to take a picture.')

    def on_start_evf(self, event: wx.CommandEvent) -> None:
        if self.parent.get_selected_camera() is not None:
            self.parent.get_selected_camera().startEvf()
            self.parent.add_evf_pane()
        else:
            set_dialog('Please select the camera to start live view.')