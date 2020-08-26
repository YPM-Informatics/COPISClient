"""TODO"""

import wx
import wx.lib.scrolledpanel as scrolled


class PropertiesPanel(scrolled.ScrolledPanel):
    """TODO

    """

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits PropertiesPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        # self.BackgroundColour = wx.SystemSettings().GetColour(wx.SYS_COLOUR_WINDOW)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self._current = 'No Selection'
        self.current_text = wx.StaticText(self, label=self._current)
        self.Sizer.AddSpacer(15)
        self.Sizer.Add(self.current_text, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.AddSpacer(5)

        self._properties = {}

        self.init_all_property_panels()

        for _, p in self._properties.items():
            # p.BackgroundColour = wx.SystemSettings().GetColour(wx.SYS_COLOUR_WINDOW)
            self.Sizer.Add(p, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 0)

        self.SetupScrolling(scroll_x=False)
        self.Layout()

    def init_all_property_panels(self) -> None:
        """"""
        self._properties['transform'] = _PropTransform(self)
        self._properties['cameracontrols'] = _PropCamera(self)

    @property
    def current(self) -> str:
        return self._current

    @current.setter
    def current(self, value: str) -> None:
        if value == '':
            value = 'No Selection'
        self._current = value
        self.current_text.Label = value


class _PropTransform(wx.Panel):
    """TODO

    """

    def __init__(self, parent) -> None:
        """Inits _PropTransform with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Transform'), wx.VERTICAL)

        self.Sizer.Add(self.box_sizer, 0, wx.ALL|wx.EXPAND, 5)

        self.Layout()


class _PropCamera(wx.Panel):
    """TODO

    """

    def __init__(self, parent) -> None:
        """Inits _PropCamera with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Camera Control'), wx.VERTICAL)

        vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.remoteRb = wx.RadioButton(self.box_sizer.StaticBox, label='Remote Shutter', style=wx.RB_GROUP)
        vbox1.Add(self.remoteRb)

        vboxAFShutter = wx.BoxSizer()
        self.af_btn = wx.Button(self.box_sizer.StaticBox, label='A/F', size=(-1, -1))
        vboxAFShutter.Add(self.af_btn)
        self.shutter_btn = wx.Button(self.box_sizer.StaticBox, label='Shutter', size=(-1, -1))
        vboxAFShutter.Add(self.shutter_btn)
        vbox1.Add(vboxAFShutter, 0, flag=wx.ALL, border=5)

        self.usb_rb = wx.RadioButton(self.box_sizer.StaticBox, label='USB')
        vbox1.Add(self.usb_rb)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_remote_usb_radio_group)

        self.edsdk_rb = wx.RadioButton(self.box_sizer.StaticBox, label='EDSDK', style=wx.RB_GROUP)
        vbox1.Add(self.edsdk_rb, flag=wx.ALL|wx.TOP, border=5)
        self.edsdk_rb.Value = False
        self.edsdk_rb.Disable()

        self.ptp_rbh = wx.RadioButton(self.box_sizer.StaticBox, label='PTP')
        vbox1.Add(self.ptp_rbh, flag=wx.ALL|wx.TOP, border=5)
        self.ptp_rbh.Disable()

        hboxF = wx.BoxSizer()
        self.frBtn = wx.Button(self.box_sizer.StaticBox, label='Focus-', size=(-1, -1))
        hboxF.Add(self.frBtn)
        self.fiBtn = wx.Button(self.box_sizer.StaticBox, label='Focus+', size=(-1, -1))
        hboxF.Add(self.fiBtn)
        vbox1.Add(hboxF, 1, flag=wx.TOP, border=15)
        self.box_sizer.Add(vbox1, 0, flag=wx.ALL, border=5)


        vbox2 = wx.BoxSizer(wx.VERTICAL)
        self.takePictureBtn = wx.Button(self.box_sizer.StaticBox, wx.ID_ANY, label='Take Picture')
        vbox2.Add(self.takePictureBtn)
        self.takePictureBtn.Bind(wx.EVT_BUTTON, self.on_take_picture)

        self.startEvfBtn = wx.Button(self.box_sizer.StaticBox, wx.ID_ANY, label='Start Liveview')
        vbox2.Add(self.startEvfBtn)
        self.startEvfBtn.Bind(wx.EVT_BUTTON, self.on_start_evf)
        self.box_sizer.Add(vbox2, 0, flag=wx.ALL, border=5)

        self.Sizer.Add(self.box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.Layout()

    def on_remote_usb_radio_group(self, event: wx.CommandEvent) -> None:
        rb = event.EventObject

        # self.visualizer_panel.on_clear_cameras()
        self.Sizer.Clear()

        if rb.Label == 'USB':
            self.edsdk_rb.Enable()
            self.ptp_rbh.Enable()
        elif rb.Label == 'Remote Shutter':
            self.edsdk_rb.Value = False
            self.edsdk_rb.Disable()

            self.ptp_rbh.Value = False
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
