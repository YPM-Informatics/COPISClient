"""TODO"""

from typing import Any, List, Optional, Union

import wx
import wx.lib.scrolledpanel as scrolled
from pydispatch import dispatcher

from gui.wxutils import create_scaled_bitmap
from utils import Point3, Point5


def _text(parent: Any, label: str = '', width: int = -1) -> wx.StaticText:
    return wx.StaticText(parent, label=label, size=(width, -1), style=wx.ALIGN_RIGHT)


class PropertiesPanel(scrolled.ScrolledPanel):
    """TODO

    """
    config = {
        'Default': ('visualizer', 'quick_actions'),
        'Camera': ('camera_info', 'camera_config', 'quick_actions'),
        'Point': ('transform', 'quick_actions'),
        'Group': ('transform', 'quick_actions'),
    }


    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits PropertiesPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        # self.BackgroundColour = wx.SystemSettings().GetColour(wx.SYS_COLOUR_WINDOW)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.text_style = wx.EXPAND | wx.ALIGN_CENTER_VERTICAL
        self.text_size = wx.Size(40, -1)

        self._current = 'No Selection'
        self.current_text = wx.StaticText(self, label=self._current)
        self.Sizer.AddSpacer(16)
        self.Sizer.Add(self.current_text, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 16)
        self.Sizer.AddSpacer(4)

        self._property_panels = {}

        self.init_all_property_panels()
        self.update_to_selected('Default')

        self.SetupScrolling(scroll_x=False)
        self.Layout()

        # bind copiscore listeners
        dispatcher.connect(self.on_device_selected, signal='core_device_selected')
        dispatcher.connect(self.on_deselected, signal='core_device_deselected')
        dispatcher.connect(self.on_points_selected, signal='core_point_selected')

    def init_all_property_panels(self) -> None:
        """Inits all property panels."""
        self._property_panels['visualizer'] = _PropVisualizer(self)
        self._property_panels['transform'] = _PropTransform(self)
        self._property_panels['camera_info'] = _PropCameraInfo(self)
        self._property_panels['camera_config'] = _PropCameraConfig(self)

        for _, panel in self._property_panels.items():
            self.Sizer.Add(panel, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 0)

    def update_to_selected(self, selected: str) -> None:
        """Update property panels to reflect current selection."""
        if selected not in self.config:
            return
        for _, panel in self._property_panels.items():
            panel.Hide()
        for name in self.config[selected]:
            panel = self._property_panels.get(name, None)
            if panel is not None:
                panel.Show()

        self.Layout()
        w, h = self.Sizer.GetMinSize()
        self.SetVirtualSize((w, h))

    @property
    def current(self) -> str:
        return self._current

    @current.setter
    def current(self, value: Optional[str]) -> None:
        if not value:
            value = 'No Selection'
        self._current = value
        self.current_text.Label = value

    def on_device_selected(self, device) -> None:
        """On on_device_selected, set to camera view."""
        self.current = 'Camera'
        self._property_panels['camera_info'].device_id = device.device_id
        self._property_panels['camera_info'].device_name = device.device_name
        self._property_panels['camera_info'].device_type = device.device_type
        self.update_to_selected('Camera')

    def on_deselected(self) -> None:
        """On core_device_deselected, reset to default view."""
        self.current = None
        self.update_to_selected('Default')

    def on_points_selected(self, points: List[int]) -> None:
        """On core_points_selected, set to point view."""
        if len(points) == 1:
            self.current = 'Point'
            point = wx.GetApp().core.points[points[0]]
            self._property_panels['transform'].set_point(point[1])
            self.update_to_selected('Point')


class _PropVisualizer(wx.Panel):

    def __init__(self, parent) -> None:
        """Inits _PropVisualizer with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self.text_style = parent.text_style
        self.text_size = parent.text_size

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Visualizer'), wx.VERTICAL)

        grid_check = wx.CheckBox(self, label='Show &grid', name='grid')
        grid_check.Value = True
        axes_check = wx.CheckBox(self, label='Show &axes', name='axes')
        axes_check.Value = True
        bbox_check = wx.CheckBox(self, label='Show chamber &boundaries', name='bbox')
        bbox_check.Value = True

        box_sizer.AddMany([
            (grid_check, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 4),
            (4, 4, 0),
            (axes_check, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 4),
            (4, 4, 0),
            (bbox_check, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 4),
        ])

        # ---

        self.Sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 7)
        self.Layout()

        self.Bind(wx.EVT_CHECKBOX, self.on_checkbox)

    def on_checkbox(self, event: wx.CommandEvent) -> None:
        name = event.EventObject.Name
        if name == 'grid':
            self.parent.parent.visualizer_panel.grid_shown = event.Int
        elif name == 'axes':
            self.parent.parent.visualizer_panel.axes_shown = event.Int
        else: # name == 'bbox'
            self.parent.parent.visualizer_panel.bbox_shown = event.Int


class _PropTransform(wx.Panel):

    def __init__(self, parent) -> None:
        """Inits _PropTransform with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self.text_style = parent.text_style
        self.text_size = parent.text_size

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Transform'), wx.VERTICAL)

        # ---

        grid = wx.FlexGridSizer(3, 4, 4, 8)
        grid.AddGrowableCol(1, 0)
        grid.AddGrowableCol(3, 0)

        self.x_val = wx.TextCtrl(self, size=(50, -1), value='0.000 mm')
        self.y_val = wx.TextCtrl(self, size=(50, -1), value='0.000 mm')
        self.z_val = wx.TextCtrl(self, size=(50, -1), value='0.000 mm')
        self.p_val = wx.TextCtrl(self, size=(50, -1), value='0.000 dd')
        self.t_val = wx.TextCtrl(self, size=(50, -1), value='0.000 dd')
        self.more_btn = wx.Button(self, label='More...', size=(50, -1))
        self.more_btn.Bind(wx.EVT_BUTTON, self.on_show_button)

        grid.AddMany([
            (_text(self, 'X:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.x_val, 0, wx.EXPAND, 0),
            (_text(self, 'Pan:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.p_val, 0, wx.EXPAND, 0),

            (_text(self, 'Y:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.y_val, 0, wx.EXPAND, 0),
            (_text(self, 'Tilt:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.t_val, 0, wx.EXPAND, 0),

            (_text(self, 'Z:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.z_val, 0, wx.EXPAND, 0),
            (0, 0),
            (self.more_btn, 0, wx.ALIGN_RIGHT, 0)
        ])

        box_sizer.Add(grid, 0, wx.ALL|wx.EXPAND, 4)

        # ---

        x_pos_btn = wx.Button(self, label='X+', size=(20, -1))
        x_neg_btn = wx.Button(self, label='X-', size=(20, -1))
        y_pos_btn = wx.Button(self, label='Y+', size=(20, -1))
        y_neg_btn = wx.Button(self, label='Y-', size=(20, -1))
        z_pos_btn = wx.Button(self, label='Z+', size=(20, -1))
        z_neg_btn = wx.Button(self, label='Z-', size=(20, -1))

        tilt_up_btn = wx.Button(self, label='T+', size=(20, -1))
        tilt_down_btn = wx.Button(self, label='T-', size=(20, -1))
        pan_right_btn = wx.Button(self, label='P+', size=(20, -1))
        pan_left_btn = wx.Button(self, label='P-', size=(20, -1))

        self.xyzpt_grid = wx.GridBagSizer()
        self.xyzpt_grid.AddMany([
            (0, 0, wx.GBPosition(0, 0)),    # vertical spacer

            (x_neg_btn, wx.GBPosition(0, 1), wx.GBSpan(2, 1), wx.EXPAND, 0),
            (y_pos_btn, wx.GBPosition(0, 2), wx.GBSpan(1, 1), wx.EXPAND, 0),
            (y_neg_btn, wx.GBPosition(1, 2), wx.GBSpan(1, 1), wx.EXPAND, 0),
            (x_pos_btn, wx.GBPosition(0, 3), wx.GBSpan(2, 1), wx.EXPAND, 0),

            (4, 0, wx.GBPosition(0, 4)),    # vertical spacer

            (z_pos_btn, wx.GBPosition(0, 5), wx.GBSpan(1, 1), wx.EXPAND, 0),
            (z_neg_btn, wx.GBPosition(1, 5), wx.GBSpan(1, 1), wx.EXPAND, 0),

            (4, 0, wx.GBPosition(0, 6)),    # vertical spacer

            (pan_left_btn, wx.GBPosition(0, 7), wx.GBSpan(2, 1), wx.EXPAND, 0),
            (tilt_up_btn, wx.GBPosition(0, 8), wx.GBSpan(1, 1), wx.EXPAND, 0),
            (tilt_down_btn, wx.GBPosition(1, 8), wx.GBSpan(1, 1), wx.EXPAND, 0),
            (pan_right_btn, wx.GBPosition(0, 9), wx.GBSpan(2, 1), wx.EXPAND, 0),
        ])

        for col in (1, 3, 7, 9):
            self.xyzpt_grid.AddGrowableCol(col, 1)
        for col in (2, 5, 8):
            self.xyzpt_grid.AddGrowableCol(col, 3)

        # start hidden
        self.xyzpt_grid.ShowItems(False)
        box_sizer.Add(self.xyzpt_grid, 0, wx.ALL|wx.EXPAND, 4)

        self.Sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 7)
        self.Layout()

    def on_show_button(self, event: wx.CommandEvent) -> None:
        """Show or hide extra controls."""
        if event.EventObject.Label == 'More...':
            self.xyzpt_grid.ShowItems(True)
            event.EventObject.Label = 'Less...'
        else: # event.EventObject.Label == 'Less...':
            self.xyzpt_grid.ShowItems(False)
            event.EventObject.Label = 'More...'
        self.parent.Layout()
        w, h = self.parent.Sizer.GetMinSize()
        self.parent.SetVirtualSize((w, h))

    def set_point(self, point: Point5) -> None:
        self.x_val.Label = f'{point.x:.3f} mm'
        self.y_val.Label = f'{point.y:.3f} mm'
        self.z_val.Label = f'{point.z:.3f} mm'
        self.p_val.Label = f'{point.p*57.295779513:.3f} dd'
        self.t_val.Label = f'{point.t*57.295779513:.3f} dd'


class _PropCameraInfo(wx.Panel):
    """[summary]

    Args:
        device_id:
        device_name:
        device_type:
    """

    def __init__(self, parent) -> None:
        """Inits _PropCameraInfo with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self.text_style = parent.text_style
        self.text_size = parent.text_size

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Camera Info'), wx.VERTICAL)

        # ---

        grid = wx.FlexGridSizer(3, 2, 4, 8)
        grid.AddGrowableCol(1, 0)

        self.id_text = wx.StaticText(self, label='')
        self.name_text = wx.StaticText(self, label='')
        self.type_text = wx.StaticText(self, label='')

        grid.AddMany([
            (_text(self, 'Device ID:', 80), 0, wx.EXPAND, 0),
            (self.id_text, 0, wx.EXPAND, 0),

            (_text(self, 'Device Name:', 80), 0, wx.EXPAND, 0),
            (self.name_text, 0, wx.EXPAND, 0),

            (_text(self, 'Device Type:', 80), 0, wx.EXPAND, 0),
            (self.type_text, 0, wx.EXPAND, 0),
        ])

        box_sizer.Add(grid, 0, wx.ALL|wx.EXPAND, 4)
        self.Sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 7)
        self.Layout()

    @property
    def device_id(self) -> str:
        return self.id_text.Label

    @device_id.setter
    def device_id(self, value: Union[str, int]) -> None:
        self.id_text.Label = str(value)

    @property
    def device_name(self) -> str:
        return self.name_text.Label

    @device_name.setter
    def device_name(self, value: str) -> None:
        self.name_text.Label = value

    @property
    def device_type(self) -> str:
        return self.type_text.Label

    @device_type.setter
    def device_type(self, value: str) -> None:
        self.type_text.Label = value


class _PropCameraConfig(wx.Panel):

    def __init__(self, parent) -> None:
        """Inits _PropCamera with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Camera Config'), wx.VERTICAL)

        # ---

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
        self.Sizer.Add(self.box_sizer, 0, wx.ALL|wx.EXPAND, 7)
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
            self.parent.init_edsdk()
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
