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
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""COPIS transform properties panel."""

import wx
from copis.globals import Point5

from copis.gui.wxutils import EVT_FANCY_TEXT_UPDATED_EVENT, FancyTextCtrl, simple_statictext
from copis.helpers import dd_to_rad, rad_to_dd, xyz_units, pt_units


class TransformPanel(wx.Panel):
    """Show transform properties panel"""
    _XYZ_UNIT = 'mm'
    _PT_UNIT = 'dd'

    def __init__(self, parent) -> None:
        """Initialize _PropTransform with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent

        self._x: float = 0.0
        self._y: float = 0.0
        self._z: float = 0.0
        self._p: float = 0.0
        self._t: float = 0.0
        self._xyz_step: float = 1.0
        self._pt_step: float = 1.0

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self._box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Transform'), wx.VERTICAL)

        self.init_gui()

        # Bind events.
        for ctrl in (self._x_ctrl, self._y_ctrl, self._z_ctrl, self._p_ctrl, self._t_ctrl):#,
            # self.xyz_step_ctrl, self.pt_step_ctrl):
            ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self.on_text_update)

    def _add_freestyle_transform_controls(self):
        grid = wx.FlexGridSizer(3, 4, 0, 0)
        grid.AddGrowableCol(1, 0)
        grid.AddGrowableCol(3, 0)

        grid.AddMany([
            (simple_statictext(self, f'X ({self._XYZ_UNIT}):', 45), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 0),
            (self._x_ctrl, 0, wx.EXPAND|wx.RIGHT, 60),
            (simple_statictext(self, f'Pan ({self._PT_UNIT}):', 50), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 30),
            (self._p_ctrl, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0),

            (simple_statictext(self, f'Y ({self._XYZ_UNIT}):', 45), 0,
                wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 0),
            (self._y_ctrl, 0, wx.EXPAND|wx.RIGHT, 60),
            (simple_statictext(self, f'Tilt ({self._PT_UNIT}):', 50), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 30),
            (self._t_ctrl, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0),

            (simple_statictext(self, f'Z ({self._XYZ_UNIT}):', 45), 0,
                wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 0),
            (self._z_ctrl, 0, wx.EXPAND|wx.RIGHT, 60),
            (0, 0),
            (0, 0)
        ])

        self._box_sizer.Add(grid, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)

    def _add_step_transform_controls(self):
        pass

    def init_gui(self) -> None:
        """Initialize gui elements."""
        self._x_ctrl = FancyTextCtrl(
            self, size=(80, -1), name='x', default_unit=self._XYZ_UNIT, unit_conversions=xyz_units)
        self._y_ctrl = FancyTextCtrl(
            self, size=(80, -1), name='y', default_unit=self._XYZ_UNIT, unit_conversions=xyz_units)
        self._z_ctrl = FancyTextCtrl(
            self, size=(80, -1), name='z', default_unit=self._XYZ_UNIT, unit_conversions=xyz_units)
        self._p_ctrl = FancyTextCtrl(
            self, size=(80, -1), name='p', default_unit=self._PT_UNIT, unit_conversions=pt_units)
        self._t_ctrl = FancyTextCtrl(
            self, size=(80, -1), name='t', default_unit=self._PT_UNIT, unit_conversions=pt_units)

        self._add_freestyle_transform_controls()
        self._add_step_transform_controls()

        self._box_sizer.AddSpacer(5)
        self._box_sizer.Add(wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 0)
        self._box_sizer.AddSpacer(5)

        self._step_sizer = wx.BoxSizer(wx.VERTICAL)

        # self.xyz_step_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=self.xyz_step,
        #     name='xyz_step', default_unit=self._XYZ_UNIT, unit_conversions=xyz_units)
        # self.pt_step_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=self.pt_step,
        #     name='pt_step', default_unit=self._PT_UNIT, unit_conversions=pt_units)

        # step_size_grid = wx.FlexGridSizer(2, 2, 4, 8)
        # step_size_grid.AddGrowableCol(1, 0)

        # step_size_grid.AddMany([
        #     (simple_statictext(self, f'XYZ step ({self._XYZ_UNIT}):', 180), 0,
        #         wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
        #     (self.xyz_step_ctrl, 0, wx.EXPAND, 0),
        #     (simple_statictext(self, f'PT step ({self._PT_UNIT}):', 180), 0,
        #         wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
        #     (self.pt_step_ctrl, 0, wx.EXPAND, 0),
        # ])

        # self._step_sizer.Add(step_size_grid, 0, wx.EXPAND, 0)
        # self._step_sizer.AddSpacer(8)

        # x_pos_btn = wx.Button(self, label='X+', size=(20, -1), name='x+')
        # x_neg_btn = wx.Button(self, label='X-', size=(20, -1), name='x-')
        # y_pos_btn = wx.Button(self, label='Y+', size=(20, -1), name='y+')
        # y_neg_btn = wx.Button(self, label='Y-', size=(20, -1), name='y-')
        # z_pos_btn = wx.Button(self, label='Z+', size=(20, -1), name='z+')
        # z_neg_btn = wx.Button(self, label='Z-', size=(20, -1), name='z-')
        # p_pos_btn = wx.Button(self, label='P+', size=(20, -1), name='p+')
        # p_neg_btn = wx.Button(self, label='P-', size=(20, -1), name='p-')
        # t_pos_btn = wx.Button(self, label='T+', size=(20, -1), name='t+')
        # t_neg_btn = wx.Button(self, label='T-', size=(20, -1), name='t-')
        # for btn in (x_pos_btn, x_neg_btn, y_pos_btn, y_neg_btn, z_pos_btn, z_neg_btn,
        #             t_pos_btn, t_neg_btn, p_pos_btn, p_neg_btn):
        #     btn.Bind(wx.EVT_BUTTON, self.on_step_button)

        # step_xyzpt_grid = wx.GridBagSizer()
        # step_xyzpt_grid.AddMany([
        #     (0, 0, wx.GBPosition(0, 0)),    # vertical spacer

        #     (x_neg_btn, wx.GBPosition(0, 1), wx.GBSpan(2, 1), wx.EXPAND, 0),
        #     (y_pos_btn, wx.GBPosition(0, 2), wx.GBSpan(1, 1), wx.EXPAND, 0),
        #     (y_neg_btn, wx.GBPosition(1, 2), wx.GBSpan(1, 1), wx.EXPAND, 0),
        #     (x_pos_btn, wx.GBPosition(0, 3), wx.GBSpan(2, 1), wx.EXPAND, 0),

        #     (0, 0, wx.GBPosition(0, 4)),    # vertical spacer

        #     (z_pos_btn, wx.GBPosition(0, 5), wx.GBSpan(1, 1), wx.EXPAND, 0),
        #     (z_neg_btn, wx.GBPosition(1, 5), wx.GBSpan(1, 1), wx.EXPAND, 0),

        #     (4, 0, wx.GBPosition(0, 6)),    # vertical spacer

        #     (p_neg_btn, wx.GBPosition(0, 7), wx.GBSpan(2, 1), wx.EXPAND, 0),
        #     (t_pos_btn, wx.GBPosition(0, 8), wx.GBSpan(1, 1), wx.EXPAND, 0),
        #     (t_neg_btn, wx.GBPosition(1, 8), wx.GBSpan(1, 1), wx.EXPAND, 0),
        #     (p_pos_btn, wx.GBPosition(0, 9), wx.GBSpan(2, 1), wx.EXPAND, 0),
        # ])

        # for col in (1, 3, 7, 9):
        #     step_xyzpt_grid.AddGrowableCol(col, 1)
        # for col in (2, 5, 8):
        #     step_xyzpt_grid.AddGrowableCol(col, 3)

        # self._step_sizer.Add(step_xyzpt_grid, 0, wx.EXPAND, 0)

        # box_sizer.Add(self._step_sizer, 0, wx.ALL|wx.EXPAND, 4)

        self.Sizer.Add(self._box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.Layout()

    def on_step_button(self, event: wx.CommandEvent) -> None:
        """On EVT_BUTTONs, step value accordingly."""
        button = event.EventObject
        if button.Name[0] in 'xyz':
            step = self.xyz_step
        else:  # button.Name in 'pt':
            step = self.pt_step
        if button.Name[1] == '-':
            step *= -1

        self.step_value(button.Name[0], step)
        self.parent.core.update_selected_pose([
            self.x, self.y, self.z, dd_to_rad(self.p), dd_to_rad(self.t)])

    def on_text_update(self, event: wx.Event) -> None:
        """On EVT_FANCY_TEXT_UPDATED_EVENT, set dirty flag true."""
        ctrl = event.GetEventObject()
        self.set_value(ctrl.Name, ctrl.num_value)

        # Update pose.
        if ctrl.Name in 'xyzpt':
            self.parent.core.update_selected_pose([
                self.x, self.y, self.z, dd_to_rad(self.p), dd_to_rad(self.t)])

    def set_pose(self, position: Point5) -> None:
        """Set text controls given a position."""
        x, y, z, p, t = position

        self.x, self.y, self.z, self.p, self.t = x, y, z, rad_to_dd(
            p), rad_to_dd(t)

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
        self._x_ctrl.num_value = value

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        self._y = value
        self._y_ctrl.num_value = value

    @property
    def z(self) -> float:
        return self._z

    @z.setter
    def z(self, value: float) -> None:
        self._z = value
        self._z_ctrl.num_value = value

    @property
    def p(self) -> float:
        return self._p

    @p.setter
    def p(self, value: float) -> None:
        self._p = value
        self._p_ctrl.num_value = value

    @property
    def t(self) -> float:
        return self._t

    @t.setter
    def t(self, value: float) -> None:
        self._t = value
        self._t_ctrl.num_value = value

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
        self.pt_step_ctrl.num_value = value
