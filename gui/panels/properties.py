"""TODO"""

import re
from typing import Any, List, Optional, Union

import wx
import wx.lib.scrolledpanel as scrolled
from pydispatch import dispatcher

import utils
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
        dispatcher.connect(self.on_device_selected, signal='core_d_selected')
        dispatcher.connect(self.on_deselected, signal='core_d_deselected')
        dispatcher.connect(self.on_points_selected, signal='core_p_selected')

    def init_all_property_panels(self) -> None:
        """Inits all property panels."""
        self._property_panels['visualizer'] = _PropVisualizer(self)
        self._property_panels['transform'] = _PropTransform(self)
        self._property_panels['camera_info'] = _PropCameraInfo(self)
        self._property_panels['camera_config'] = _PropCameraConfig(self)
        self._property_panels['quick_actions'] = _PropQuickActions(self)

        for _, panel in self._property_panels.items():
            self.Sizer.Add(panel, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 0)

    def update_to_selected(self, selected: str) -> None:
        """Update property panels to reflect current selection."""
        if selected not in self.config:
            return

        # show/hide appropriate panels
        for name, panel in self._property_panels.items():
            panel.Show(name in self.config[selected])

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
        """On core_d_selected, set to camera view."""
        self.current = 'Camera'
        self._property_panels['camera_info'].device_id = device.device_id
        self._property_panels['camera_info'].device_name = device.device_name
        self._property_panels['camera_info'].device_type = device.device_type
        self.update_to_selected('Camera')

    def on_deselected(self) -> None:
        """On core_d_deselected, reset to default view."""
        self.current = None
        self.update_to_selected('Default')

    def on_points_selected(self, points: List[int]) -> None:
        """On core_p_selected, set to point view."""
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

        self._x: float = 0.0
        self._y: float = 0.0
        self._z: float = 0.0
        self._p: float = 0.0
        self._t: float = 0.0

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
    """[summary]

    Attributes:
        x: A float representing x value.
        y: A float representing y value.
        z: A float representing z value.
        p: A float representing p value.
        t: A float representing t value.
    """

    def __init__(self, parent) -> None:
        """Inits _PropTransform with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self._text_dirty = False
        self._selected_dirty = False

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Transform'), wx.VERTICAL)

        # ---

        grid = wx.FlexGridSizer(3, 4, 4, 8)
        grid.AddGrowableCol(1, 0)
        grid.AddGrowableCol(3, 0)

        self.x_ctrl = wx.TextCtrl(self, size=(50, -1), style=wx.TE_PROCESS_ENTER, name='x')
        self.y_ctrl = wx.TextCtrl(self, size=(50, -1), style=wx.TE_PROCESS_ENTER, name='y')
        self.z_ctrl = wx.TextCtrl(self, size=(50, -1), style=wx.TE_PROCESS_ENTER, name='z')
        self.p_ctrl = wx.TextCtrl(self, size=(50, -1), style=wx.TE_PROCESS_ENTER, name='p')
        self.t_ctrl = wx.TextCtrl(self, size=(50, -1), style=wx.TE_PROCESS_ENTER, name='t')
        more_btn = wx.Button(self, label='More...', size=(50, -1))

        grid.AddMany([
            (_text(self, 'X:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.x_ctrl, 0, wx.EXPAND, 0),
            (_text(self, 'Pan:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.p_ctrl, 0, wx.EXPAND, 0),

            (_text(self, 'Y:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.y_ctrl, 0, wx.EXPAND, 0),
            (_text(self, 'Tilt:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.t_ctrl, 0, wx.EXPAND, 0),

            (_text(self, 'Z:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.z_ctrl, 0, wx.EXPAND, 0),
            (0, 0),
            (more_btn, 0, wx.ALIGN_RIGHT, 0)
        ])

        for ctrl in (self.x_ctrl, self.y_ctrl, self.z_ctrl, self.p_ctrl, self.t_ctrl):
            ctrl.Bind(wx.EVT_LEFT_UP, self.on_left_up)
            ctrl.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
            ctrl.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)
            ctrl.Bind(wx.EVT_TEXT, self.on_text_change)
            ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter)

        more_btn.Bind(wx.EVT_BUTTON, self.on_show_button)

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

        self._xyzpt_grid = wx.GridBagSizer()
        self._xyzpt_grid.AddMany([
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
            self._xyzpt_grid.AddGrowableCol(col, 1)
        for col in (2, 5, 8):
            self._xyzpt_grid.AddGrowableCol(col, 3)

        # start hidden
        self._xyzpt_grid.ShowItems(False)
        box_sizer.Add(self._xyzpt_grid, 0, wx.ALL|wx.EXPAND, 4)

        self.Sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 7)
        self.Layout()

    def on_show_button(self, event: wx.CommandEvent) -> None:
        """Show or hide extra controls."""
        if event.EventObject.Label == 'More...':
            self._xyzpt_grid.ShowItems(True)
            event.EventObject.Label = 'Less...'
        else: # event.EventObject.Label == 'Less...':
            self._xyzpt_grid.ShowItems(False)
            event.EventObject.Label = 'More...'
        self.parent.Layout()
        w, h = self.parent.Sizer.GetMinSize()
        self.parent.SetVirtualSize((w, h))

    def on_left_up(self, event: wx.MouseEvent) -> None:
        """On EVT_LEFT_UP, if not already focused, select digits."""
        ctrl = event.EventObject
        if not self._selected_dirty:
            self._selected_dirty = True
            ctrl.SetSelection(0, ctrl.Value.find(' '))
        event.Skip()

    def on_set_focus(self, event: wx.FocusEvent) -> None:
        """On EVT_SET_FOCUS, select digits."""
        ctrl = event.EventObject
        ctrl.SetSelection(0, ctrl.Value.find(' '))
        event.Skip()

    def on_kill_focus(self, event: wx.FocusEvent) -> None:
        """On EVT_KILL_FOCUS, process the updated value."""
        if self._text_dirty:
            event.EventObject.Undo()
            self._text_dirty = False
        self._selected_dirty = False
        event.Skip()

    def on_text_change(self, event: wx.CommandEvent) -> None:
        """On EVT_TEXT, set dirty flag true."""
        self._text_dirty = True

    def on_text_enter(self, event: wx.CommandEvent) -> None:
        """On EVT_TEXT_ENTER, process the updated value."""
        self._process_value(event.EventObject)

    def _process_value(self, ctrl: wx.TextCtrl) -> None:
        """Process updated text control and convert units accordingly."""
        if not self._text_dirty:
            return

        value = 0
        if ctrl.Name in ('x', 'y', 'z'):
            regex = re.findall(r'(-?\d*\.?\d+)\s*(mm|cm|inch|in)?', ctrl.Value)
            if len(regex) == 0:
                ctrl.Undo()
                return
            else:
                value, unit = regex[0]
                value = float(value) * utils.xyz_units.get(unit, 1)

        else: # ctrl.Name in ('p', 't')
            regex = re.findall(r'(-?\d*\.?\d+)\s*(dd|rad)?', ctrl.Value)
            if len(regex) == 0:
                ctrl.Undo()
                return
            else:
                value, unit = regex[0]
                value = float(value) * utils.pt_units.get(unit, 1)

        self._text_dirty = False
        self.set_value(ctrl.Name, value)

        # update actual point
        wx.GetApp().core.update_selected_points_by_pos(Point5(self.x, self.y, self.z, self.p, self.t))

    def set_point(self, point: Point5) -> None:
        """Set text controls given a Point5.

        Args:
            point: A Point5 representing the new point to set.
        """
        self.x, self.y, self.z, self.p, self.t = point

    def set_value(self, name: str, value: float) -> None:
        """Set value in text control and append units accordingly.

        Args:
            name: A string representing the name of the text control
                (x, y, z, p, t) to be updated.
            value: A float representing the new value to set.
        """
        if name == 'x':
            self.x = value
        elif name == 'y':
            self.y = value
        elif name == 'z':
            self.z = value
        elif name == 'p':
            self.p = value
        elif name == 't':
            self.t = value
        else:
            return

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        self._x = value
        self.x_ctrl.ChangeValue(f'{value:.3f} mm')

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        self._y = value
        self.y_ctrl.ChangeValue(f'{value:.3f} mm')

    @property
    def z(self) -> float:
        return self._z

    @z.setter
    def z(self, value: float) -> None:
        self._z = value
        self.z_ctrl.ChangeValue(f'{value:.3f} mm')

    @property
    def p(self) -> float:
        return self._p

    @p.setter
    def p(self, value: float) -> None:
        self._p = value
        self.p_ctrl.ChangeValue(f'{value:.3f} dd')

    @property
    def t(self) -> float:
        return self._t

    @t.setter
    def t(self, value: float) -> None:
        self._t = value
        self.t_ctrl.ChangeValue(f'{value:.3f} dd')


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


class _PropQuickActions(wx.Panel):
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

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Quick Actions'), wx.VERTICAL)

        # ---

        grid = wx.FlexGridSizer(1, 3, 4, 8)
        grid.AddGrowableCol(0, 0)
        grid.AddGrowableCol(1, 0)
        grid.AddGrowableCol(2, 0)

        self.button1 = wx.Button(self, label='Thing 1', size=(50, -1))
        self.button2 = wx.Button(self, label='Thing 2', size=(50, -1))
        self.button3 = wx.Button(self, label='Thing 3', size=(50, -1))

        grid.AddMany([
            (self.button1, 0, wx.EXPAND, 0),
            (self.button2, 0, wx.EXPAND, 0),
            (self.button3, 0, wx.EXPAND, 0),
        ])

        box_sizer.Add(grid, 0, wx.ALL|wx.EXPAND, 4)
        self.Sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 7)
        self.Layout()
