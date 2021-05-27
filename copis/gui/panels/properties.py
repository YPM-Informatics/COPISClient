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

"""PropertiesPanel class."""

from typing import List, Union

import math
import wx
import wx.lib.scrolledpanel as scrolled

from pydispatch import dispatcher

from copis.helpers import xyz_units, pt_units
from copis.gui.wxutils import (FancyTextCtrl,
    EVT_FANCY_TEXT_UPDATED_EVENT,
    simple_statictext)


class PropertiesPanel(scrolled.ScrolledPanel):
    """Properties panel. Shows settings and controls in the context of the
    current selection.

    TODO: implement quick actions

    Args:
        parent: Pointer to a parent wx.Frame.

    Attributes:
        current: A string which sets the current selection text label.
    """

    config = {
        'Default': ('visualizer'),
        'Camera': ('camera_info', 'camera_config'),
        'Point': ('transform'),
        'Group': ('transform'),
    }

    def __init__(self, parent) -> None:
        """Inits PropertiesPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self.core = self.parent.core

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self._current = 'No Selection'
        self._current_text = wx.StaticText(self, label=self._current)
        self.Sizer.AddSpacer(16)
        self.Sizer.Add(self._current_text, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 16)
        self.Sizer.AddSpacer(4)

        self._property_panels = {}

        self.init_all_property_panels()
        self.update_to_selected('Default')

        self.SetupScrolling(scroll_x=False)
        self.Layout()

        # bind copiscore listeners
        dispatcher.connect(self.on_device_selected, signal='core_d_selected')
        dispatcher.connect(self.on_points_selected, signal='core_p_selected')
        dispatcher.connect(self.on_deselected, signal='core_d_deselected')
        dispatcher.connect(self.on_deselected, signal='core_p_deselected')

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
        """Update panels to reflect the given selection."""
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
    def current(self, value: str) -> None:
        if not value:
            value = 'No Selection'
        self._current = value
        self._current_text.Label = value

    def on_device_selected(self, device) -> None:
        """On core_d_selected, set to camera view."""
        self.current = 'Camera'
        self._property_panels['camera_info'].device_id = device.device_id
        self._property_panels['camera_info'].device_name = device.device_name
        self._property_panels['camera_info'].device_type = device.device_type
        self.update_to_selected('Camera')

    def on_deselected(self) -> None:
        """On core_*_deselected, reset to default view."""
        self.current = 'No Selection'
        self.update_to_selected('Default')

    def on_points_selected(self, points: List[int]) -> None:
        """On core_p_selected, set to point view."""

        if len(points) == 1:
            action = self.core.actions[points[0]]
            if action.argc == 5:
                self.current = 'Point'
                self._property_panels['transform'].set_point(*action.args)
                self.update_to_selected('Point')


class _PropVisualizer(wx.Panel):

    def __init__(self, parent) -> None:
        """Inits _PropVisualizer with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Visualizer'), wx.VERTICAL)

        grid_check = wx.CheckBox(self, label='Show chamber &grid', name='grid')
        grid_check.Value = True
        axes_check = wx.CheckBox(self, label='Show chamber &axes', name='axes')
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
    """Transform panel. Default display units are mm and dd.

    Attributes:
        x: A float representing x value in mm.
        y: A float representing y value in mm.
        z: A float representing z value in mm.
        p: A float representing p value in radians.
        t: A float representing t value in radians.
    """

    def __init__(self, parent) -> None:
        """Inits _PropTransform with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent

        self._x: float = 0.0
        self._y: float = 0.0
        self._z: float = 0.0
        self._p: float = 0.0
        self._t: float = 0.0
        self._xyz_step: float = 1.0
        self._pt_step: float = math.pi/180

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.init_gui()

        # bind events
        for ctrl in (self.x_ctrl, self.y_ctrl, self.z_ctrl, self.p_ctrl, self.t_ctrl,
                     self.xyz_step_ctrl, self.pt_step_ctrl):
            ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self.on_text_update)

    def init_gui(self) -> None:
        """Initialize gui elements."""
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Transform'), wx.VERTICAL)

        grid = wx.FlexGridSizer(3, 4, 4, 8)
        grid.AddGrowableCol(1, 0)
        grid.AddGrowableCol(3, 0)

        self.x_ctrl = FancyTextCtrl(
            self, size=(48, -1), name='x', default_unit='mm', unit_conversions=xyz_units)
        self.y_ctrl = FancyTextCtrl(
            self, size=(48, -1), name='y', default_unit='mm', unit_conversions=xyz_units)
        self.z_ctrl = FancyTextCtrl(
            self, size=(48, -1), name='z', default_unit='mm', unit_conversions=xyz_units)
        self.p_ctrl = FancyTextCtrl(
            self, size=(48, -1), name='p', default_unit='dd', unit_conversions=pt_units)
        self.t_ctrl = FancyTextCtrl(
            self, size=(48, -1), name='t', default_unit='dd', unit_conversions=pt_units)
        more_btn = wx.Button(self, label='More...', size=(55, -1))

        grid.AddMany([
            (simple_statictext(self, 'X:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Pan:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.p_ctrl, 0, wx.EXPAND, 0),

            (simple_statictext(self, 'Y:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.y_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Tilt:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.t_ctrl, 0, wx.EXPAND, 0),

            (simple_statictext(self, 'Z:', 32), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.z_ctrl, 0, wx.EXPAND, 0),
            (0, 0),
            (more_btn, 0, wx.ALIGN_RIGHT, 0)
        ])

        more_btn.Bind(wx.EVT_BUTTON, self.on_show_button)
        box_sizer.Add(grid, 0, wx.ALL|wx.EXPAND, 4)

        # ---

        self._step_sizer = wx.BoxSizer(wx.VERTICAL)
        self._step_sizer.AddSpacer(8)
        self._step_sizer.Add(wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 0)
        self._step_sizer.AddSpacer(8)

        self.xyz_step_ctrl = FancyTextCtrl(
            self, size=(48, -1), name='xyz_step', max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.pt_step_ctrl = FancyTextCtrl(
            self, size=(48, -1), name='pt_step', max_precision=0, default_unit='dd', unit_conversions=pt_units)

        step_size_grid = wx.FlexGridSizer(1, 4, 4, 8)
        step_size_grid.AddGrowableCol(1, 0)
        step_size_grid.AddGrowableCol(3, 0)

        step_size_grid.AddMany([
            (simple_statictext(self, 'XYZ step:', 56), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.xyz_step_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'PT step:', 56), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.pt_step_ctrl, 0, wx.EXPAND, 0),
        ])

        self._step_sizer.Add(step_size_grid, 0, wx.EXPAND, 0)
        self._step_sizer.AddSpacer(8)

        x_pos_btn = wx.Button(self, label='X+', size=(20, -1), name='x+')
        x_neg_btn = wx.Button(self, label='X-', size=(20, -1), name='x-')
        y_pos_btn = wx.Button(self, label='Y+', size=(20, -1), name='y+')
        y_neg_btn = wx.Button(self, label='Y-', size=(20, -1), name='y-')
        z_pos_btn = wx.Button(self, label='Z+', size=(20, -1), name='z+')
        z_neg_btn = wx.Button(self, label='Z-', size=(20, -1), name='z-')
        p_pos_btn = wx.Button(self, label='P+', size=(20, -1), name='p+')
        p_neg_btn = wx.Button(self, label='P-', size=(20, -1), name='p-')
        t_pos_btn = wx.Button(self, label='T+', size=(20, -1), name='t+')
        t_neg_btn = wx.Button(self, label='T-', size=(20, -1), name='t-')
        for btn in (x_pos_btn, x_neg_btn, y_pos_btn, y_neg_btn, z_pos_btn, z_neg_btn,
                    t_pos_btn, t_neg_btn, p_pos_btn, p_neg_btn):
            btn.Bind(wx.EVT_BUTTON, self.on_step_button)

        step_xyzpt_grid = wx.GridBagSizer()
        step_xyzpt_grid.AddMany([
            (0, 0, wx.GBPosition(0, 0)),    # vertical spacer

            (x_neg_btn, wx.GBPosition(0, 1), wx.GBSpan(2, 1), wx.EXPAND, 0),
            (y_pos_btn, wx.GBPosition(0, 2), wx.GBSpan(1, 1), wx.EXPAND, 0),
            (y_neg_btn, wx.GBPosition(1, 2), wx.GBSpan(1, 1), wx.EXPAND, 0),
            (x_pos_btn, wx.GBPosition(0, 3), wx.GBSpan(2, 1), wx.EXPAND, 0),

            (0, 0, wx.GBPosition(0, 4)),    # vertical spacer

            (z_pos_btn, wx.GBPosition(0, 5), wx.GBSpan(1, 1), wx.EXPAND, 0),
            (z_neg_btn, wx.GBPosition(1, 5), wx.GBSpan(1, 1), wx.EXPAND, 0),

            (4, 0, wx.GBPosition(0, 6)),    # vertical spacer

            (p_neg_btn, wx.GBPosition(0, 7), wx.GBSpan(2, 1), wx.EXPAND, 0),
            (t_pos_btn, wx.GBPosition(0, 8), wx.GBSpan(1, 1), wx.EXPAND, 0),
            (t_neg_btn, wx.GBPosition(1, 8), wx.GBSpan(1, 1), wx.EXPAND, 0),
            (p_pos_btn, wx.GBPosition(0, 9), wx.GBSpan(2, 1), wx.EXPAND, 0),
        ])

        for col in (1, 3, 7, 9):
            step_xyzpt_grid.AddGrowableCol(col, 1)
        for col in (2, 5, 8):
            step_xyzpt_grid.AddGrowableCol(col, 3)

        self._step_sizer.Add(step_xyzpt_grid, 0, wx.EXPAND, 0)

        # start hidden
        self._step_sizer.ShowItems(False)
        box_sizer.Add(self._step_sizer, 0, wx.ALL|wx.EXPAND, 4)

        self.Sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 7)
        self.Layout()

    def on_show_button(self, event: wx.CommandEvent) -> None:
        """Show or hide extra controls."""
        if event.EventObject.Label == 'More...':
            self._step_sizer.ShowItems(True)
            event.EventObject.Label = 'Less...'
        else: # event.EventObject.Label == 'Less...':
            self._step_sizer.ShowItems(False)
            event.EventObject.Label = 'More...'
        self.parent.Layout()
        w, h = self.parent.Sizer.GetMinSize()
        self.parent.SetVirtualSize((w, h))

    def on_step_button(self, event: wx.CommandEvent) -> None:
        """On EVT_BUTTONs, step value accordingly."""
        button = event.EventObject
        if button.Name[0] in 'xyz':
            step = self.xyz_step
        else: # button.Name in 'pt':
            step = self.pt_step
        if button.Name[1] == '-':
            step *= -1

        self.step_value(button.Name[0], step)
        self.parent.core.update_selected_points(5, [self.x, self.y, self.z, self.p, self.t])

    def on_text_update(self, event: wx.Event) -> None:
        """On EVT_FANCY_TEXT_UPDATED_EVENT, set dirty flag true."""
        ctrl = event.GetEventObject()
        self.set_value(ctrl.Name, ctrl.num_value)

        # update point
        if ctrl.Name in 'xyzpt':
            self.parent.core.update_selected_points(5, [self.x, self.y, self.z, self.p, self.t])

    def set_point(self, x: int, y: int, z: int, p: int, t: int) -> None:
        """Set text controls given a x, y, z, p, t."""
        self.x, self.y, self.z, self.p, self.t = x, y, z, p, t

    def set_value(self, name: str, value: float) -> None:
        """Set value indicated by name.

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
        elif name == 'xyz_step':
            self.xyz_step = value
        elif name == 'pt_step':
            self.pt_step = value
        else:
            return

    def step_value(self, name: str, value: float) -> None:
        """Step value indicated by name.

        Args:
            name: A string representing the name of the text control
                (x, y, z, p, t) to be updated.
            value: A float representing the new value to step by.
        """
        if name == 'x':
            self.x += value
        elif name == 'y':
            self.y += value
        elif name == 'z':
            self.z += value
        elif name == 'p':
            self.p += value
        elif name == 't':
            self.t += value
        else:
            return

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        self._x = value
        self.x_ctrl.num_value = value

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        self._y = value
        self.y_ctrl.num_value = value

    @property
    def z(self) -> float:
        return self._z

    @z.setter
    def z(self, value: float) -> None:
        self._z = value
        self.z_ctrl.num_value = value

    @property
    def p(self) -> float:
        return self._p

    @p.setter
    def p(self, value: float) -> None:
        self._p = value
        self.p_ctrl.num_value = value*180/math.pi

    @property
    def t(self) -> float:
        return self._t

    @t.setter
    def t(self, value: float) -> None:
        self._t = value
        self.t_ctrl.num_value = value*180/math.pi

    @property
    def xyz_step(self) -> float:
        return self._xyz_step

    @xyz_step.setter
    def xyz_step(self, value: float) -> None:
        self._xyz_step = value
        self.xyz_step_ctrl.num_value = value

    @property
    def pt_step(self) -> float:
        return self._pt_step

    @pt_step.setter
    def pt_step(self, value: float) -> None:
        self._pt_step = value
        self.pt_step_ctrl.num_value = value*180/math.pi


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
            (simple_statictext(self, 'Device ID:', 80), 0, wx.EXPAND, 0),
            (self.id_text, 0, wx.EXPAND, 0),

            (simple_statictext(self, 'Device Name:', 80), 0, wx.EXPAND, 0),
            (self.name_text, 0, wx.EXPAND, 0),

            (simple_statictext(self, 'Device Type:', 80), 0, wx.EXPAND, 0),
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

            self.parent.core.terminate_edsdk()
        elif rb.Label == 'EDSDK':
            self.parent.core.init_edsdk()
        else:
            self.parent.core.terminate_edsdk()

    def on_take_picture(self, event: wx.CommandEvent) -> None:
        """ Take picture.

        TODO: implement when edsdk is fully implemented in copiscore.
        """
        return
        # camera = self.main_combo.Selection
        # if self.parent.core.get_selected_camera() is not None:
        #     self.parent.core.get_selected_camera().shoot()
        # else:
        #     set_dialog('Please select the camera to take a picture.')

    def on_start_evf(self, event: wx.CommandEvent) -> None:
        """TODO: implement when edsdk is fully implemented in copiscore.
        """
        return
        # if self.parent.core.get_selected_camera() is not None:
        #     self.parent.core.get_selected_camera().startEvf()
        #     self.parent.add_evf_pane()
        # else:
        #     set_dialog('Please select the camera to start live view.')


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
