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

from math import cos, sin

import wx

from glm import vec3

from copis.globals import Point5
from copis.gui.wxutils import (EVT_FANCY_TEXT_UPDATED_EVENT, FancyTextCtrl, create_scaled_bitmap,
    simple_statictext)
from copis.helpers import dd_to_rad, get_heading, rad_to_dd, sanitize_number, xyz_units, pt_units


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
        self._xyz_step: float = 50.0
        self._pt_step: float = 5.0

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self._box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Transform'), wx.VERTICAL)

        self.init_gui()

        # Bind events.
        for ctrl in (self._x_ctrl, self._y_ctrl, self._z_ctrl, self._p_ctrl, self._t_ctrl,
            self._xyz_step_ctrl, self._pt_step_ctrl):
            ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self.on_text_update)

    def _add_freestyle_transform_controls(self):
        grid = wx.FlexGridSizer(3, 5, 0, 0)
        grid.AddGrowableCol(2, 0)

        grid.AddMany([
            (simple_statictext(self, f'X ({self._XYZ_UNIT}):', 50), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self._x_ctrl, 0, wx.EXPAND, 0),
            (10, 0),
            (simple_statictext(self, f'P ({self._PT_UNIT}):', 50), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self._p_ctrl, 0, wx.EXPAND, 0),

            (simple_statictext(self, f'Y ({self._XYZ_UNIT}):', 50), 0,
                wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0),
            (self._y_ctrl, 0, wx.EXPAND, 0),
            (10, 0),
            (simple_statictext(self, f'T ({self._PT_UNIT}):', 50), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self._t_ctrl, 0, wx.EXPAND, 0),

            (simple_statictext(self, f'Z ({self._XYZ_UNIT}):', 50), 0,
                wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0),
            (self._z_ctrl, 0, wx.EXPAND, 0),
            (10, 0),
            (0, 0),
            (0, 0)
        ])

        self._box_sizer.Add(grid, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)

    def _add_step_transform_controls(self):
        step_sizer = wx.BoxSizer(wx.VERTICAL)
        step_size_grid = wx.FlexGridSizer(4, 2, 0, 0)
        step_size_grid.AddGrowableCol(0)

        feed_rate_ctrl = wx.TextCtrl(self, value="2500", size=(80, -1), name='feed_rate')

        step_size_grid.AddMany([
            (simple_statictext(self, 'Increments', 180), 0,
                wx.EXPAND, 0),
            (0, 0),
            (simple_statictext(self, f'XYZ ({self._XYZ_UNIT}):', 80), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 20),
            (self._xyz_step_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, f'PT ({self._PT_UNIT}):', 80), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 20),
            (self._pt_step_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Feed Rate (<unit>/s):', 80), 0,
                wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0),
            (feed_rate_ctrl, 0, wx.EXPAND, 0),
        ])

        step_sizer.Add(step_size_grid, 0, wx.EXPAND, 0)
        step_sizer.AddSpacer(5)
        btn_size = (30, 30)
        font = wx.Font(
            7, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_MAX, wx.FONTWEIGHT_SEMIBOLD)

        x_pos_btn = wx.Button(self, label='X', size=(20, -1), name='x+')
        x_pos_btn.SetBitmap(create_scaled_bitmap('arrow_e', 12), wx.RIGHT)
        x_pos_btn.Font = font
        x_neg_btn = wx.Button(self, label='X', size=(20, -1), name='x-')
        x_neg_btn.SetBitmap(create_scaled_bitmap('arrow_w', 12))
        x_neg_btn.Font = font
        y_pos_btn = wx.Button(self, label='Y', size=(20, -1), name='y+')
        y_pos_btn.SetBitmap(create_scaled_bitmap('arrow_n', 12), wx.TOP)
        y_pos_btn.Font = font
        y_neg_btn = wx.Button(self, label='Y', size=(20, -1), name='y-')
        y_neg_btn.SetBitmap(create_scaled_bitmap('arrow_s', 12), wx.BOTTOM)
        y_neg_btn.Font = font
        z_pos_btn = wx.Button(self, label='Z', size=(20, -1), name='z+')
        z_pos_btn.SetBitmap(create_scaled_bitmap('arrow_n', 12), wx.TOP)
        z_pos_btn.Font = font
        z_neg_btn = wx.Button(self, label='Z', size=(20, -1), name='z-')
        z_neg_btn.SetBitmap(create_scaled_bitmap('arrow_s', 12), wx.BOTTOM)
        z_neg_btn.Font = font
        p_pos_btn = wx.Button(self, label='P', size=(20, -1), name='p+')
        p_pos_btn.SetBitmap(create_scaled_bitmap('arrow_w', 12), wx.LEFT)
        p_pos_btn.Font = font
        p_neg_btn = wx.Button(self, label='P', size=(20, -1), name='p-')
        p_neg_btn.SetBitmap(create_scaled_bitmap('arrow_e', 12), wx.RIGHT)
        p_neg_btn.Font = font
        t_pos_btn = wx.Button(self, label='T', size=(20, -1), name='t+')
        t_pos_btn.SetBitmap(create_scaled_bitmap('arrow_n', 12), wx.TOP)
        t_pos_btn.Font = font
        t_neg_btn = wx.Button(self, label='T', size=(20, -1), name='t-')
        t_neg_btn.SetBitmap(create_scaled_bitmap('arrow_s', 12), wx.BOTTOM)
        t_neg_btn.Font = font
        arrow_nw_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('arrow_nw', 15),
            size=(24, 24), name='nw')
        arrow_ne_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('arrow_ne', 15),
            size=(24, 24), name='ne')
        arrow_sw_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('arrow_sw', 15),
            size=(24, 24), name='sw')
        arrow_se_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('arrow_se', 15),
            size=(24, 24), name='se')
        target_closer_btn = wx.BitmapButton(self,
            bitmap=create_scaled_bitmap('target_closer', 24),
            size=btn_size, name='closer')
        re_target_btn = wx.BitmapButton(self,
            bitmap=create_scaled_bitmap('center_focus_strong', 24),
            size=btn_size, name='target')
        target_farther_btn = wx.BitmapButton(self,
            bitmap=create_scaled_bitmap('target_farther', 24),
            size=btn_size, name='farther')

        for btn in (x_pos_btn, x_neg_btn, y_pos_btn, y_neg_btn, z_pos_btn, z_neg_btn,
                    t_pos_btn, t_neg_btn, p_pos_btn, p_neg_btn,
                    arrow_ne_btn, arrow_nw_btn, arrow_se_btn, arrow_sw_btn):
            btn.Bind(wx.EVT_BUTTON, self.on_step_button)

        for btn in (target_closer_btn, target_farther_btn, re_target_btn):
            btn.Bind(wx.EVT_BUTTON, self.on_target_button)

        xyzpt_grid = wx.FlexGridSizer(8, 4, 0, 0)
        for col in (0, 1, 2, 3):
            xyzpt_grid.AddGrowableCol(col)

        xyzpt_grid.AddMany([
            (arrow_nw_btn, 0, wx.EXPAND, 0),
            (y_pos_btn, 0, wx.EXPAND, 0),
            (arrow_ne_btn, 0, wx.EXPAND, 0),
            (z_pos_btn, 0, wx.EXPAND, 0),

            (x_neg_btn, 0, wx.EXPAND, 0),
            btn_size,
            (x_pos_btn, 0, wx.EXPAND, 0),
            (0, 0),

            (arrow_sw_btn, 0, wx.EXPAND, 0),
            (y_neg_btn, 0, wx.EXPAND, 0),
            (arrow_se_btn, 0, wx.EXPAND, 0),
            (z_neg_btn, 0, wx.EXPAND, 0),

            (0, 5), (0, 0), (0, 0), (0, 0),

            (0, 0),
            (t_pos_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (0, 0),

            (p_pos_btn, 0, wx.EXPAND, 0),
            (t_neg_btn, 0, wx.EXPAND, 0),
            (p_neg_btn, 0, wx.EXPAND, 0),
            (0, 0),

            (0, 5), (0, 0), (0, 0), (0, 0),

            (target_closer_btn, 0, wx.EXPAND, 0),
            (re_target_btn, 0, wx.EXPAND, 0),
            (target_farther_btn, 0, wx.EXPAND, 0),
            (0, 0),
        ])

        step_sizer.Add(xyzpt_grid, 0, wx.EXPAND, 0)

        self._box_sizer.Add(step_sizer, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 5)


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

        self._xyz_step_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=self.xyz_step,
            name='xyz_step', default_unit=self._XYZ_UNIT, unit_conversions=xyz_units)
        self._pt_step_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=self.pt_step,
            name='pt_step', default_unit=self._PT_UNIT, unit_conversions=pt_units)

        self._add_freestyle_transform_controls()

        self._box_sizer.AddSpacer(5)
        self._box_sizer.Add(wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 0)

        self._add_step_transform_controls()

        self.Sizer.Add(self._box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.Layout()

    def on_target_button(self, event: wx.CommandEvent) -> None:
        """On EVT_BUTTONs, target accordingly."""
        button = event.EventObject
        task = button.Name

        if task == 'target':
            end_pan, end_tilt = get_heading(vec3(self.x, self.y, self.z),
                self.parent.core.imaging_target)

            self.p = rad_to_dd(end_pan)
            self.t = rad_to_dd(end_tilt)

            self.parent.core.update_selected_pose_position([self.x, self.y, self.z,
                sanitize_number(end_pan), sanitize_number(end_tilt)])
        else:
            dist = self.xyz_step
            if task == 'closer':
                dist = -1 * dist

            pan = dd_to_rad(self.p)
            tilt = dd_to_rad(self.t)

            d_places = 3
            sin_p = round(sin(pan), d_places)
            cos_p = round(cos(pan), d_places)
            sin_t = round(sin(tilt), d_places)
            cos_t = round(cos(tilt), d_places)

            # The right formula for this is:
            #   new_x = x + (dist * sin(pan) * cos(tilt))
            #   new_y = y + (dist * sin(tilt))
            #   new_z = z + (dist * cos(pan) * cos(tilt))
            # But since our axis is rotated 90dd clockwise around the x axis so
            # that z points up we have to adjust the formula accordingly.
            end_x = sanitize_number(self.x + (dist * sin_p * cos_t))
            end_y = sanitize_number(self.y + (dist * cos_p * cos_t))
            end_z = sanitize_number(self.z - (dist * sin_t))

            end_pan, end_tilt = get_heading(vec3(end_x, end_y, end_z),
                self.parent.core.imaging_target)

            self.x = end_x
            self.y = end_y
            self.z = end_z
            self.p = rad_to_dd(end_pan)
            self.t = rad_to_dd(end_tilt)

            self.parent.core.update_selected_pose_position([end_x, end_y, end_z,
                sanitize_number(end_pan), sanitize_number(end_tilt)])


    def on_step_button(self, event: wx.CommandEvent) -> None:
        """On EVT_BUTTONs, step value accordingly."""
        button = event.EventObject
        if button.Name[0] in 'xyzns':
            step = self.xyz_step
        else:  # button.Name in 'pt':
            step = self.pt_step
        if button.Name[1] == '-':
            step *= -1

        btn_name = button.Name[0] if button.Name[1] in '+-' else button.Name

        self.step_value(btn_name, step)
        self.parent.core.update_selected_pose_position([
            self.x, self.y, self.z, dd_to_rad(self.p), dd_to_rad(self.t)])

    def on_text_update(self, event: wx.Event) -> None:
        """On EVT_FANCY_TEXT_UPDATED_EVENT, set dirty flag true."""
        ctrl = event.GetEventObject()
        self.set_value(ctrl.Name, ctrl.num_value)

        # Update pose.
        if ctrl.Name in 'xyzpt':
            self.parent.core.update_selected_pose_position([
                self.x, self.y, self.z, dd_to_rad(self.p), dd_to_rad(self.t)])

    def set_pose_position(self, position: Point5) -> None:
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
        elif name == 'nw':
            self.y += value
            self.x -= value
        elif name == 'ne':
            self.y += value
            self.x += value
        elif name == 'sw':
            self.y -= value
            self.x -= value
        elif name == 'se':
            self.y -= value
            self.x += value
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
        self._xyz_step_ctrl.num_value = value

    @property
    def pt_step(self) -> float:
        return self._pt_step

    @pt_step.setter
    def pt_step(self, value: float) -> None:
        self._pt_step = value
        self._pt_step_ctrl.num_value = value
