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

"""PathgenToolbar class."""

import math
import glm

from collections import defaultdict
from typing import List, Tuple
from itertools import groupby
from glm import vec2, vec3

import wx
import wx.lib.agw.aui as aui

from copis.classes import Action, Object3D, Pose
from copis.globals import ActionType, PathIds
from copis.gui.wxutils import (
    FancyTextCtrl, create_scaled_bitmap, simple_statictext)
from copis.helpers import (create_action_args, interleave_lists, print_debug_msg,
    sanitize_number, sanitize_point,
    xyz_units)
from copis.pathutils import create_circle, create_helix, create_line, process_path


class PathgenToolbar(aui.AuiToolBar):
    """Manage pathgen toolbar panel. Spawns a bunch of dialogs."""

    def __init__(self, parent, *args, **kwargs) -> None:
        """Initializes ToolbarPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT, agwStyle=
            aui.AUI_TB_PLAIN_BACKGROUND|aui.AUI_TB_OVERFLOW)
        self.parent = parent
        self.core = self.parent.core

        self._path_dialogs = {}
        self.init_toolbar()

        self.Bind(wx.EVT_TOOL, self.on_tool_selected)

    def init_toolbar(self) -> None:
        """Initialize and populate toolbar.

        Icons taken from https://material.io/resources/icons/?style=baseline.
        """
        # add path shape adders
        _bmp = create_scaled_bitmap('cylinder_path', 24)
        self.AddTool(PathIds.CYLINDER.value, 'Cylinder', _bmp, _bmp,
            aui.ITEM_NORMAL, short_help_string='Add cylinder path')
        _bmp = create_scaled_bitmap('helix_path', 24)
        self.AddTool(PathIds.HELIX.value, 'Helix', _bmp, _bmp,
            aui.ITEM_NORMAL, short_help_string='Add helix path')
        _bmp = create_scaled_bitmap('sphere_path', 24)
        self.AddTool(PathIds.SPHERE.value, 'Sphere', _bmp, _bmp,
            aui.ITEM_NORMAL, short_help_string='Add sphere path')
        _bmp = create_scaled_bitmap('line_path', 24)
        self.AddTool(PathIds.LINE.value, 'Line', _bmp, _bmp,
            aui.ITEM_NORMAL, short_help_string='Add line path')

        self.AddSeparator()

        # add single point adder
        _bmp = create_scaled_bitmap('add_circle_outline', 24)
        self.AddTool(PathIds.POINT.value, 'Single Point', _bmp, _bmp,
            aui.ITEM_NORMAL, short_help_string='Add single path point')

        self.AddSeparator()

        self.Bind(wx.EVT_BUTTON, self.on_interleave_paths,
            self.AddControl(wx.Button(self, wx.ID_ANY, label='Interleave paths', size=(110, -1))))
        self.AddSpacer(8)
        self.Bind(wx.EVT_BUTTON, self.on_clear_path,
            self.AddControl(wx.Button(self, wx.ID_ANY, label='Clear path', size=(75, -1))))

    def on_interleave_paths(self, _) -> None:
        """On interleave paths button pressed, rearrange actions to alternate by
        camera.
        This allows us to simultaneously play paths that have be created sequentially."""
        get_device = lambda a: a.position.device

        poses = sorted(self.core.project.poses, key=get_device)

        if poses and len(poses):
            grouped  = groupby(poses, get_device)
            groups = []

            for _, g in grouped:
                groups.append(list(g))

            interleaved = interleave_lists(*groups)

            self.core.project.poses.clear(False)
            self.core.project.poses.extend(interleaved)

    def on_clear_path(self, _) -> None:
        """On clear button pressed, clear core action list"""
        if len(self.core.project.poses) > 0:
            self.core.project.poses.clear()

    def on_tool_selected(self, event: wx.CommandEvent) -> None:
        """On toolbar tool selected, create pathgen dialog and process accordingly.
        """
        if event.Id == PathIds.CYLINDER.value:
            with _PathgenCylinder(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Cylinder path added.', self.core.is_dev_env)
                    selected_devices = dlg.device_checklist.CheckedItems
                    radius = dlg.radius_ctrl.num_value
                    height = dlg.height_ctrl.num_value
                    z_div = int(dlg.z_div_ctrl.GetValue())
                    points = int(dlg.points_ctrl.GetValue())

                    vertices = []
                    count = 0
                    for i in range(z_div):
                        z = 0 if z_div == 1 else i * (height / (z_div - 1))
                        v, c = create_circle(
                            vec3(dlg.base_x_ctrl.num_value,
                                     dlg.base_y_ctrl.num_value,
                                     dlg.base_z_ctrl.num_value + z),
                            vec3(0, 0, 1 if height > 0 else -1), radius, points)

                        vertices.extend(v[:-3].tolist())
                        count += c - 1

                    lookat = vec3(dlg.lookat_x_ctrl.num_value,
                                      dlg.lookat_y_ctrl.num_value,
                                      dlg.lookat_z_ctrl.num_value)

                    self._extend_actions(vertices, count, lookat, selected_devices)

        elif event.Id == PathIds.HELIX.value:
            with _PathgenHelix(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Helix path added.', self.core.is_dev_env)
                    selected_devices = dlg.device_checklist.CheckedItems
                    radius = dlg.radius_ctrl.num_value
                    height = dlg.height_ctrl.num_value
                    rotations = int(dlg.rotation_ctrl.GetValue())
                    points = int(dlg.points_ctrl.GetValue())
                    pitch = abs(height) / rotations

                    vertices, count = create_helix(
                        vec3(dlg.base_x_ctrl.num_value,
                                 dlg.base_y_ctrl.num_value,
                                 dlg.base_z_ctrl.num_value),
                        vec3(0, 0, 1 if height > 0 else -1), radius, pitch, rotations, points)

                    lookat = vec3(dlg.lookat_x_ctrl.num_value,
                                      dlg.lookat_y_ctrl.num_value,
                                      dlg.lookat_z_ctrl.num_value)

                    self._extend_actions(vertices, count, lookat, selected_devices)

        elif event.Id == PathIds.SPHERE.value:
            with _PathgenSphere(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Sphere path added.', self.core.is_dev_env)
                    selected_devices = dlg.device_checklist.CheckedItems
                    radius = dlg.radius_ctrl.num_value
                    z_div = int(dlg.z_div_ctrl.GetValue())
                    distance = dlg.distance_ctrl.num_value

                    vertices = []
                    count = 0
                    for i in range(z_div):
                        z = i * (radius*0.8 * 2 / (z_div - 1)) - radius*0.8
                        r = math.sqrt(radius * radius - z * z)
                        num = int(2 * math.pi * r / distance)

                        v, c = create_circle(
                            vec3(dlg.center_x_ctrl.num_value,
                                     dlg.center_y_ctrl.num_value,
                                     dlg.center_z_ctrl.num_value + z),
                            vec3(0, 0, 1), r, num)
                        vertices.extend(v[:-3].tolist())
                        count += c - 1

                    lookat = vec3(dlg.center_x_ctrl.num_value,
                                      dlg.center_y_ctrl.num_value,
                                      dlg.center_z_ctrl.num_value)

                    self._extend_actions(vertices, count, lookat, selected_devices)

        elif event.Id == PathIds.LINE.value:
            with _PathgenLine(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Line path added.', self.core.is_dev_env)
                    device_id = int(dlg.device_choice.GetString(dlg.device_choice.Selection)
                        .split(' ')[0])
                    points = int(dlg.points_ctrl.GetValue())

                    start = vec3(dlg.start_x_ctrl.num_value,
                                     dlg.start_y_ctrl.num_value,
                                     dlg.start_z_ctrl.num_value)
                    end = vec3(dlg.end_x_ctrl.num_value,
                                   dlg.end_y_ctrl.num_value,
                                   dlg.end_z_ctrl.num_value)
                    vertices, count = create_line(start, end, points)

                    lookat = vec3(dlg.lookat_x_ctrl.num_value,
                                      dlg.lookat_y_ctrl.num_value,
                                      dlg.lookat_z_ctrl.num_value)

                    self._extend_actions(vertices, count, lookat, (device_id,))

        elif event.Id == PathIds.POINT.value:
            with _PathgenPoint(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Point path added.', self.core.is_dev_env)
                    device_id = int(dlg.device_choice.GetString(dlg.device_choice.Selection)
                        .split(' ')[0])
                    x = dlg.x_ctrl.num_value
                    y = dlg.y_ctrl.num_value
                    z = dlg.z_ctrl.num_value
                    lookat = vec3(dlg.lookat_x_ctrl.num_value,
                                      dlg.lookat_y_ctrl.num_value,
                                      dlg.lookat_z_ctrl.num_value)

                    self._extend_actions((x, y, z), 1, lookat, (device_id,))

    def _extend_actions(self,
                        vertices,
                        count: int,
                        lookat: vec3,
                        device_list: Tuple[int]) -> None:
        """Extend core actions list by given vertices.

        TODO: #120: move this somewhere else
            https://github.com/YPM-Informatics/COPISClient/issues/120
        TODO: think of ways to improve path planning

        Args:
            vertices: A flattened list of vertices, where length = count * 3.
            count: An integer representing the number of vertices.
            lookat: A vec3 representing the lookat point in space.
        """

        devices = self.core.project.devices
        grouped_points = defaultdict(list)
        max_zs = defaultdict(float)

        # group points into devices
        for i in range(count):
            point = vec3(vertices[i * 3:i * 3 + 3])
            device_id = -1
            for id_ in device_list:
                max_zs[id_] = devices[id_].range_3d.upper.z
                if devices[id_].range_3d.vec3_intersect(point, 0.0):
                    device_id = id_

            # ignore if point not in bounds of any device
            if device_id != -1:
                grouped_points[device_id].append(point)

        interlaced_poses = process_path(grouped_points, self.core.project.proxies, max_zs, lookat)
        self.core.project.poses.extend(interlaced_poses)

    def __del__(self) -> None:
        pass


class _PathgenCylinder(wx.Dialog):
    """Dialog to generate a cylinder path."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes _PathgenCylinder with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Cylinder Path', size=(250, -1))
        self.parent = parent

        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})', self.parent.core.project.devices))

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        options_grid = wx.FlexGridSizer(11, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.device_checklist = wx.CheckListBox(self, choices=self._device_choices)
        self.base_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.base_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.base_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.radius_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=100, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.height_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=100, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.z_div_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.points_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.lookat_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.lookat_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.lookat_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Devices:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.device_checklist, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Base X:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.base_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.base_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.base_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Radius:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.radius_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Height:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.height_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Z Divisions:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.z_div_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Points Per Circle:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.points_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Lookat X:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.lookat_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
        ])

        self.Sizer.Add(options_grid, 1, wx.ALL|wx.EXPAND, 4)
        self.Sizer.AddSpacer(8)

        # ---

        button_sizer = self.CreateStdDialogButtonSizer(0)
        self._affirmative_button = wx.Button(self, wx.ID_OK)
        self._affirmative_button.Disable()
        button_sizer.SetAffirmativeButton(self._affirmative_button)
        button_sizer.SetCancelButton(wx.Button(self, wx.ID_CANCEL))
        button_sizer.Realize()

        self.Sizer.Add(button_sizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 4)

        self.Layout()
        self.SetMinSize((250, -1))
        self.Fit()

        # ---

        self.device_checklist.Bind(wx.EVT_CHECKLISTBOX, self._on_ctrl_update)
        self.z_div_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)
        self.points_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)

    def _on_ctrl_update(self, _) -> None:
        """Enable the affirmative (OK) button if all fields have values."""
        if (not self.device_checklist.CheckedItems or
            self.z_div_ctrl.Value == '' or self.points_ctrl.Value == ''):
            self._affirmative_button.Disable()
            return

        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()


class _PathgenHelix(wx.Dialog):
    """Dialog to generate a helix path."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes _PathgenHelix with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Helix Path', size=(250, -1))
        self.parent = parent

        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})', self.parent.core.project.devices))

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        options_grid = wx.FlexGridSizer(11, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.device_checklist = wx.CheckListBox(self, choices=self._device_choices)
        self.base_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.base_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.base_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.radius_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=100, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.height_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=100, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.rotation_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.points_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.lookat_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.lookat_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.lookat_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Devices:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.device_checklist, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Base X:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.base_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.base_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.base_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Radius:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.radius_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Height:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.height_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Number of Rotations:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.rotation_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Points per Rotation:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.points_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Lookat X:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.lookat_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
        ])

        self.Sizer.Add(options_grid, 1, wx.ALL | wx.EXPAND, 4)
        self.Sizer.AddSpacer(8)

        # ---

        button_sizer = self.CreateStdDialogButtonSizer(0)
        self._affirmative_button = wx.Button(self, wx.ID_OK)
        self._affirmative_button.Disable()
        button_sizer.SetAffirmativeButton(self._affirmative_button)
        button_sizer.SetCancelButton(wx.Button(self, wx.ID_CANCEL))
        button_sizer.Realize()

        self.Sizer.Add(button_sizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 4)

        self.Layout()
        self.SetMinSize((250, -1))
        self.Fit()

        # ---

        self.device_checklist.Bind(wx.EVT_CHECKLISTBOX, self._on_ctrl_update)
        self.rotation_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)
        self.points_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)

    def _on_ctrl_update(self, _) -> None:
        """Enable the affirmative (OK) button if all fields have values."""
        if (not self.device_checklist.CheckedItems or
            self.rotation_ctrl.Value == '' or self.points_ctrl.Value == ''):
            self._affirmative_button.Disable()
            return

        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()


class _PathgenSphere(wx.Dialog):
    """Dialog to generate a sphere path."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes _PathgenSphere with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Sphere Path', size=(250, -1))
        self.parent = parent

        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})', self.parent.core.project.devices))

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        options_grid = wx.FlexGridSizer(7, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.device_checklist = wx.CheckListBox(self, choices=self._device_choices)
        self.center_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.center_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.center_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.radius_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=100, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.z_div_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.distance_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=10, max_precision=0, default_unit='mm', unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Devices:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.device_checklist, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Center X:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.center_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.center_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.center_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Radius:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.radius_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Z Divisions:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.z_div_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Spacing Distance:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.distance_ctrl, 0, wx.EXPAND, 0),
        ])

        self.Sizer.Add(options_grid, 1, wx.ALL | wx.EXPAND, 4)
        self.Sizer.AddSpacer(8)

        # ---

        button_sizer = self.CreateStdDialogButtonSizer(0)
        self._affirmative_button = wx.Button(self, wx.ID_OK)
        self._affirmative_button.Disable()
        button_sizer.SetAffirmativeButton(self._affirmative_button)
        button_sizer.SetCancelButton(wx.Button(self, wx.ID_CANCEL))
        button_sizer.Realize()

        self.Sizer.Add(button_sizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 4)

        self.Layout()
        self.SetMinSize((250, -1))
        self.Fit()

        # ---

        self.device_checklist.Bind(wx.EVT_CHECKLISTBOX, self._on_ctrl_update)
        self.z_div_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)

    def _on_ctrl_update(self, _) -> None:
        """Enable the affirmative (OK) button if all fields have values."""
        if (not self.device_checklist.CheckedItems or self.z_div_ctrl.Value == ''):
            self._affirmative_button.Disable()
            return

        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()


class _PathgenLine(wx.Dialog):
    """Dialog to generate a line path."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes _PathgenLine with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Line Path', size=(200, -1))
        self.parent = parent

        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})', self.parent.core.project.devices))

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        options_grid = wx.FlexGridSizer(11, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.device_choice = wx.Choice(self, choices=self._device_choices)
        self.start_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.start_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.start_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.end_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.end_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.end_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.points_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.lookat_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.lookat_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.lookat_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Device:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.device_choice, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Start X:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.start_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.start_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.start_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'End X:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.end_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.end_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.end_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Number of Points:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.points_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Lookat X:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.lookat_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
        ])

        self.Sizer.Add(options_grid, 1, wx.ALL | wx.EXPAND, 4)
        self.Sizer.AddSpacer(8)

        # ---

        button_sizer = self.CreateStdDialogButtonSizer(0)
        self._affirmative_button = wx.Button(self, wx.ID_OK)
        self._affirmative_button.Disable()
        button_sizer.SetAffirmativeButton(self._affirmative_button)
        button_sizer.SetCancelButton(wx.Button(self, wx.ID_CANCEL))
        button_sizer.Realize()

        self.Sizer.Add(button_sizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 4)

        self.Layout()
        self.SetMinSize((200, -1))
        self.Fit()

        # ---

        self.device_choice.Bind(wx.EVT_CHOICE, self._on_ctrl_update)
        self.points_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)

    def _on_ctrl_update(self, _) -> None:
        """Enable the affirmative (OK) button if all fields have values."""
        if (self.device_choice.CurrentSelection == wx.NOT_FOUND or
            self.points_ctrl.Value == ''):
            self._affirmative_button.Disable()
            return

        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()


class _PathgenPoint(wx.Dialog):
    """Dialog to generate a single point."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes _PathgenPoint with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Path Point', size=(200, -1))
        self.parent = parent

        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})', self.parent.core.project.devices))

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        options_grid = wx.FlexGridSizer(7, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.device_choice = wx.Choice(self, choices=self._device_choices)
        self.x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.lookat_x_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.lookat_y_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.lookat_z_ctrl = FancyTextCtrl(
            self, size=(48, -1), num_value=0, max_precision=0, default_unit='mm', unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Device:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.device_choice, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Position X:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Lookat X:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.lookat_x_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Z:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
        ])

        self.Sizer.Add(options_grid, 1, wx.ALL | wx.EXPAND, 4)
        self.Sizer.AddSpacer(8)

        # ---

        button_sizer = self.CreateStdDialogButtonSizer(0)
        self._affirmative_button = wx.Button(self, wx.ID_OK)
        self._affirmative_button.Disable()
        button_sizer.SetAffirmativeButton(self._affirmative_button)
        button_sizer.SetCancelButton(wx.Button(self, wx.ID_CANCEL))
        button_sizer.Realize()

        self.Sizer.Add(button_sizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 4)

        self.Layout()
        self.SetMinSize((200, -1))
        self.Fit()

        # ---

        self.device_choice.Bind(wx.EVT_CHOICE, self._on_ctrl_update)

    def _on_ctrl_update(self, _) -> None:
        """Enable the affirmative (OK) button if all fields have values."""
        if (self.device_choice.CurrentSelection == wx.NOT_FOUND):
            self._affirmative_button.Disable()
            return

        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()
