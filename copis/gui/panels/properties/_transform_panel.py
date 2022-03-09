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
from functools import partial
from collections import namedtuple

import wx

from glm import vec3

from copis.globals import ActionType, Point5
from copis.gui.wxutils import (EVT_FANCY_TEXT_UPDATED_EVENT, FancyTextCtrl, create_scaled_bitmap,
    simple_statictext)
from copis.helpers import (create_action_args, dd_to_rad, get_action_args_values, get_heading,
    rad_to_dd, sanitize_number,
    xyz_units, pt_units)
from copis.store import get_file_base_name_no_ext
from copis.classes import Action, Device, Pose


class TransformPanel(wx.Panel):
    """Show transform properties panel"""
    target_ctx_choices = namedtuple('TargetContextChoices',
        'center, floor_center, ceiling_center')

    _XYZ_UNIT = 'mm'
    _PT_UNIT = 'dd'

    _TARGET_CTX_CHOICES = target_ctx_choices(
        'Bounding Box Center',
        'Bounding Box Floor Center',
        'Bounding Box Ceiling center'
    )

    def __init__(self, parent, is_live: bool=False) -> None:
        """Initialize _PropTransform with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self._is_live = is_live

        self._pose = None
        self._device = None

        self._x: float = 0.0
        self._y: float = 0.0
        self._z: float = 0.0
        self._p: float = 0.0
        self._t: float = 0.0
        self._xyz_step: float = 50.0
        self._pt_step: float = 5.0

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self._box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Transform'), wx.VERTICAL)

        self._init_gui()

        # Bind events.
        for ctrl in (self._x_ctrl, self._y_ctrl, self._z_ctrl, self._p_ctrl, self._t_ctrl,
            self._xyz_step_ctrl, self._pt_step_ctrl):
            ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_text_updated)

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
        grid_rows = 4 if self._is_live else 3
        step_size_grid = wx.FlexGridSizer(grid_rows, 2, 0, 0)
        step_size_grid.AddGrowableCol(0)

        step_size_grid.AddMany([
            (simple_statictext(self, 'Increments', 180), 0,
                wx.EXPAND, 0),
            (0, 0),
            (simple_statictext(self, f'XYZ ({self._XYZ_UNIT}):', 80), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 20),
            (self._xyz_step_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, f'PT ({self._PT_UNIT}):', 80), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 20),
            (self._pt_step_ctrl, 0, wx.EXPAND, 0)
        ])

        if self._is_live:
            self._feed_rate_ctrl.Show()
            step_size_grid.AddMany([
                (simple_statictext(self, 'Feed Rate (<unit>/m):', 80), 0,
                    wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0),
                (self._feed_rate_ctrl, 0, wx.EXPAND, 0)
            ])
        else:
            self._feed_rate_ctrl.Hide()

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
            btn.Bind(wx.EVT_BUTTON, self._on_step_button)

        for btn in (target_closer_btn, target_farther_btn, re_target_btn):
            btn.Bind(wx.EVT_BUTTON, self._on_target_button)

        re_target_btn.Bind(wx.EVT_CONTEXT_MENU, self._on_target_ctx_menu)

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

    def _init_gui(self) -> None:
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
        self._feed_rate_ctrl = wx.TextCtrl(self, value="2500", size=(80, -1),
            name='feed_rate')
        self._feed_rate_ctrl.Hide()

        self._add_freestyle_transform_controls()

        self._box_sizer.AddSpacer(5)
        self._box_sizer.Add(wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 0)

        self._add_step_transform_controls()

        self.Sizer.Add(self._box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.Layout()

    def _get_proxy_name(self, idx: int):
        proxies = self.parent.core.project.proxies
        proxy = proxies[idx]

        if hasattr(proxy, 'obj'):
            name = get_file_base_name_no_ext(proxy.obj.file_name)
            name = f'{name[0].upper()}{name[1:]}'
        else:
            names = [(i, type(p).__qualname__) for i, p in enumerate(proxies)
                        if isinstance(p, type(proxy))]
            names = [(t[0], f'{t[1]}_{i}') if i >
                        0 else t for i, t in enumerate(names)]

            name = next(filter(lambda t: t[0] == idx, names))[1]

        return name

    def _build_target_ctx_menu(self):
        target_menu = wx.Menu()

        item: wx.MenuItem = target_menu.Append(
            wx.ID_ANY, 'Target Custom Position')
        self.Bind(wx.EVT_MENU, partial(
            self._on_target_type_selected, None), item)

        for i in range(0, len(self.parent.core.project.proxies)):
            submenu = wx.Menu()
            for _, caption in self._TARGET_CTX_CHOICES._asdict().items():
                item = submenu.Append(-1, caption)
                handler = partial(self._on_target_type_selected, i)
                self.Bind(wx.EVT_MENU, handler, item)

            target_menu.Append(
                wx.ID_ANY, f'Target {self._get_proxy_name(i)}', submenu)

        return target_menu

    def _on_target_ctx_menu(self, event: wx.ContextMenuEvent):
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)

        target_menu = self._build_target_ctx_menu()
        self.PopupMenu(target_menu, pos)

    def _on_target_type_selected(self, proxy_index, event: wx.CommandEvent):
        item: wx.MenuItem = event.EventObject.FindItemById(event.Id)
        menu: wx.Menu = item.Menu
        pos = menu.GetWindow().GetScreenPosition()

        if proxy_index is None:
            dialog_size = (100, -1)
            target_dialog = wx.Dialog(self, wx.ID_ANY, 'Target Position', size=dialog_size, pos=pos)
            target_dialog.Sizer = wx.BoxSizer(wx.VERTICAL)
            grid = wx.FlexGridSizer(3, 2, 10, 0)
            img_target = self.parent.core.imaging_target

            target_dialog.target_x_ctrl = FancyTextCtrl(target_dialog, size=(70, -1),
                num_value=img_target.x, default_unit=self._XYZ_UNIT, unit_conversions=xyz_units)
            target_dialog.target_y_ctrl = FancyTextCtrl(target_dialog, size=(70, -1),
                num_value=img_target.y, default_unit=self._XYZ_UNIT, unit_conversions=xyz_units)
            target_dialog.target_z_ctrl = FancyTextCtrl(target_dialog, size=(70, -1),
                num_value=img_target.z, default_unit=self._XYZ_UNIT, unit_conversions=xyz_units)

            grid.AddMany([
                (simple_statictext(target_dialog, f'X ({self._XYZ_UNIT}):', 60), 0,
                    wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 20),
                (target_dialog.target_x_ctrl, 0, wx.EXPAND, 0),
                (simple_statictext(target_dialog, f'Y ({self._XYZ_UNIT}):', 60), 0,
                    wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 20),
                (target_dialog.target_y_ctrl, 0, wx.EXPAND, 0),
                (simple_statictext(target_dialog, f'Z ({self._XYZ_UNIT}):', 60), 0,
                    wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 20),
                (target_dialog.target_z_ctrl, 0, wx.EXPAND, 0)
            ])

            target_dialog.Sizer.Add(grid, 0, wx.ALL|wx.EXPAND, 10)

            button_sizer = target_dialog.CreateStdDialogButtonSizer(0)
            target_dialog.affirmative_button = wx.Button(target_dialog, wx.ID_OK)
            button_sizer.SetAffirmativeButton(target_dialog.affirmative_button)
            button_sizer.SetCancelButton(wx.Button(target_dialog, wx.ID_CANCEL))
            button_sizer.Realize()

            target_dialog.Sizer.Add(button_sizer, 0, wx.ALL|wx.EXPAND, 10)

            target_dialog.Layout()
            target_dialog.SetMinSize(dialog_size)
            target_dialog.Fit()

            with target_dialog as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    target = vec3(
                        dlg.target_x_ctrl.num_value,
                        dlg.target_y_ctrl.num_value,
                        dlg.target_z_ctrl.num_value)

                    self.parent.core.imaging_target = target
        else:
            proxy_bbox = self.parent.core.project.proxies[proxy_index].bbox

            if item.ItemLabel == self._TARGET_CTX_CHOICES.ceiling_center:
                self.parent.core.imaging_target = proxy_bbox.ceiling_center
            elif item.ItemLabel == self._TARGET_CTX_CHOICES.floor_center:
                self.parent.core.imaging_target = proxy_bbox.floor_center
            else: # Target center of proxy object's bounding box.
                self.parent.core.imaging_target = proxy_bbox.volume_center

        end_pan, end_tilt = get_heading(vec3(self.x, self.y, self.z),
            self.parent.core.imaging_target)

        self.p = rad_to_dd(end_pan)
        self.t = rad_to_dd(end_tilt)

        self.parent.core.update_selected_pose_position([self.x, self.y, self.z,
            sanitize_number(end_pan), sanitize_number(end_tilt)])

    def _on_target_button(self, event: wx.CommandEvent) -> None:
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

    def _generate_commands(self, name, args = None):
        if args == None:
            args = []

        atype = None
        device_id = self._device.device_id

        if name == 'G91':
            atype = ActionType.G91
        elif name == 'G1':
            atype = ActionType.G1
        else:
            raise ValueError(f'Unsupported jog command {name}.')

        return Action(atype, device_id, len(args), args)

    def _handle_jog(self, event: wx.CommandEvent) -> None:
        button = event.EventObject

        if button.Name == 'xy':
            return

        btn = button.Name
        cmd_tokens = []
        xyz_step = 0
        pt_step = 0
        feed_rate = float(self._feed_rate_ctrl.Value)
        pos_names = ''
        pos_values = []

        if btn[0] in 'xyzns':
            xyz_step = self._xyz_step_ctrl.num_value
        else: # Button name in 'pt'.
            # Convert to radians before sending to command processor.
            pt_step = dd_to_rad(self._pt_step_ctrl.num_value)


        if btn[0] in 'ns':
            cmd_tokens = list(btn)
            cmd_tokens.reverse()
            cmd_tokens = [ 'X+' if i == 'e' else i for i in cmd_tokens ]
            cmd_tokens = [ 'Y+' if i == 'n' else i for i in cmd_tokens ]
            cmd_tokens = [ 'X-' if i == 'w' else i for i in cmd_tokens ]
            cmd_tokens = [ 'Y-' if i == 's' else i for i in cmd_tokens ]
        else:
            cmd_tokens.append(btn.upper())

        for token in cmd_tokens:
            sign = int(f'{token[1]}1')
            step = xyz_step if token[0] in 'XYZ' else pt_step
            pos_names += token[0]
            pos_values.append(sign * step)

        if 'Z' not in pos_names:
            # Ignore feed rate for z axis.
            # Screw motor axis doesn't work properly at high speeds.
            pos_values.append(feed_rate)
            pos_names += 'F'

        args = create_action_args(pos_values, pos_names)
        action = self._generate_commands('G1', args)
        self.parent.core.jog(action)

    def _on_step_button(self, event: wx.CommandEvent) -> None:
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

        if self._is_live:
            self._handle_jog(event)
        else:
            self.parent.core.update_selected_pose_position([
                self.x, self.y, self.z, dd_to_rad(self.p), dd_to_rad(self.t)])

    def _on_text_updated(self, event: wx.Event) -> None:
        """Handles fancy text updated events."""
        ctrl = event.GetEventObject()
        self.set_value(ctrl.Name, ctrl.num_value)

        # Update pose.
        if ctrl.Name in 'xyzpt':
            self.parent.core.update_selected_pose_position([
                self.x, self.y, self.z, dd_to_rad(self.p), dd_to_rad(self.t)])

    def _set_text_controls(self, position: Point5) -> None:
        """Set text controls given a position."""
        x, y, z, p, t = position

        self.x, self.y, self.z, self.p, self.t = x, y, z, rad_to_dd(
            p), rad_to_dd(t)

    def set_pose(self, pose: Pose) -> None:
        """Parses the selected pose into the panel."""
        self._pose = pose
        args = get_action_args_values(pose.position.args)

        self._set_text_controls(Point5(*args[:5]))

    def set_device(self, device: Device) -> None:
        """Parses the selected device into the panel."""
        self._device = device
        args = get_action_args_values(device.position)

        self._set_text_controls(Point5(*args[:5]))

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