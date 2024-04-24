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

from logging.handlers import RotatingFileHandler
import math

from collections import defaultdict
from multiprocessing import Value
from tkinter import Label
from typing import List, Tuple
from glm import vec3
from numpy import rot90

import wx
import wx.aui as x_aui
import wx.lib.agw.aui as aui
from copis.classes.device import Device

from copis.globals import PathIds, Point5
from copis.gui.wxutils import (
    FancyTextCtrl, create_scaled_bitmap, simple_statictext)
from copis.helpers import is_number, print_debug_msg, xyz_units, pt_units, dd_to_rad
from copis.pathutils import (build_pose_from_XYZPT, build_pose_sets, create_circle, create_helix, create_line,
    interleave_poses, process_path, create_slot_along_x, get_heading, build_poses_from_XYZPT)


class PathgenToolbar(aui.AuiToolBar):
    """Manage pathgen toolbar. Spawns a bunch of dialogs."""

    def __init__(self, parent) -> None:
        """Initializes PathgenToolbar with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT, agwStyle=aui.AUI_TB_PLAIN_BACKGROUND)

        self.parent = parent
        self.core = self.parent.core

        self._path_dialogs = {}
        self.init_toolbar()

        # Using the aui.AUI_TB_OVERFLOW style flag means that the overflow button always shows
        # when the toolbar is floating, even if all the items fit.
        # This allows the overflow button to be visible only when they don't;
        # no matter if the toolbar is floating or docked.
        self.Bind(wx.EVT_MOTION, lambda _: self.SetOverflowVisible(not self.GetToolBarFits()))
        self.Bind(wx.EVT_TOOL, self.on_tool_selected)
        
        
    def init_toolbar(self) -> None:
        """Initialize and populate toolbar.

        Icons taken from https://material.io/resources/icons/?style=baseline.
        """
        # add path shape adders
        _bmp = create_scaled_bitmap('cylinder_path', 24)
        self.AddTool(PathIds.CYLINDER.value, 'Cylinder', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add cylinder path')
        _bmp = create_scaled_bitmap('helix_path', 24)
        self.AddTool(PathIds.HELIX.value, 'Helix', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add helix path')
        _bmp = create_scaled_bitmap('sphere_path', 24)
        self.AddTool(PathIds.SPHERE.value, 'Sphere', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add sphere path')
        _bmp = create_scaled_bitmap('capsule_path', 24)
        self.AddTool(PathIds.CAPSULE.value, 'Capsule', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add capsule path')
        _bmp = create_scaled_bitmap('line_path', 24)
        self.AddTool(PathIds.LINE.value, 'Line', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add line path')
        _bmp = create_scaled_bitmap('grid_path', 24)
        self.AddTool(PathIds.GRID.value, 'Grid', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add grid')
        _bmp = create_scaled_bitmap('turn_table_path', 24)
        self.AddTool(PathIds.TURNTABLE.value, 'Turntable', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add turntable')
        self.AddSeparator()
        _bmp = create_scaled_bitmap('add_circle_outline', 24)
        self.AddTool(PathIds.POINT.value, 'Single Point', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add single path point')
        self.AddSeparator()
        self.AddSpacer(5)
        self.Bind(wx.EVT_BUTTON, self.on_interleave_paths, self.AddControl(wx.Button(self, wx.ID_ANY, label='Interleave Paths', size=(110, -1))))
        self.AddSpacer(5)
        self.Bind(wx.EVT_BUTTON, self.on_clear_path, self.AddControl(wx.Button(self, wx.ID_ANY, label='Clear Path', size=(75, -1))))
        self.AddSpacer(5)
        
    def on_interleave_paths(self, _) -> None:
        """On interleave paths button pressed, rearrange poses to alternate by
        camera.
        This allows us to simultaneously play paths that have be created sequentially."""
        interleaved = interleave_poses(self.core.project.poses)
        self.core.project.pose_sets.clear(False)
        self.core.project.pose_sets.extend(build_pose_sets(interleaved))

    def on_clear_path(self, _) -> None:
        """On clear button pressed, clear core action list"""
        if len(self.core.project.pose_sets) > 0:
            self.core.select_pose_set(-1)
            self.core.select_pose(-1)
            self.core.project.pose_sets.clear()

    def on_tool_selected(self, event: wx.CommandEvent) -> None:
        """On toolbar tool selected, create pathgen dialog and process accordingly.
        """
        if event.Id == PathIds.CYLINDER.value:
            with _PathgenCylinder(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Cylinder path added', self.core.is_dev_env)
                    selected_devices = dlg.device_checklist.CheckedItems
                    radius = dlg.radius_ctrl.num_value
                    height = dlg.height_ctrl.num_value
                    z_div = int(dlg.z_div_ctrl.GetValue())
                    points = int(dlg.points_ctrl.GetValue())
                    vertices = []
                    count = 0
                    for i in range(z_div):
                        z = 0 if z_div == 1 else i * (height / (z_div - 1))
                        v, c = create_circle(vec3(dlg.base_x_ctrl.num_value, dlg.base_y_ctrl.num_value, dlg.base_z_ctrl.num_value + z), vec3(0, 0, 1 if height > 0 else -1), radius, points)
                        vertices.extend(v[:-3].tolist())
                        count += c - 1
                    lookat = vec3(dlg.lookat_x_ctrl.num_value, dlg.lookat_y_ctrl.num_value, dlg.lookat_z_ctrl.num_value)
                    self._extend_actions(vertices, count, lookat, selected_devices)
        elif event.Id == PathIds.HELIX.value:
            with _PathgenHelix(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Helix path added', self.core.is_dev_env)
                    selected_devices = dlg.device_checklist.CheckedItems
                    radius = dlg.radius_ctrl.num_value
                    height = dlg.height_ctrl.num_value
                    rotations = int(dlg.rotation_ctrl.GetValue())
                    points = int(dlg.points_ctrl.GetValue())
                    pitch = abs(height) / rotations
                    vertices, count = create_helix(vec3(dlg.base_x_ctrl.num_value, dlg.base_y_ctrl.num_value, dlg.base_z_ctrl.num_value), vec3(0, 0, 1 if height > 0 else -1), radius, pitch, rotations, points)
                    lookat = vec3(dlg.lookat_x_ctrl.num_value, dlg.lookat_y_ctrl.num_value, dlg.lookat_z_ctrl.num_value)
                    self._extend_actions(vertices, count, lookat, selected_devices)
        elif event.Id == PathIds.SPHERE.value:
            with _PathgenSphere(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Sphere path added', self.core.is_dev_env)
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
                    lookat = vec3(dlg.center_x_ctrl.num_value, dlg.center_y_ctrl.num_value, dlg.center_z_ctrl.num_value)
                    self._extend_actions(vertices, count, lookat, selected_devices)
        elif event.Id == PathIds.LINE.value:
            with _PathgenLine(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Line path added', self.core.is_dev_env)
                    device_id = int(dlg.device_choice.GetString(dlg.device_choice.Selection).split(' ')[0])
                    points = int(dlg.points_ctrl.GetValue())
                    start = vec3(dlg.start_x_ctrl.num_value, dlg.start_y_ctrl.num_value, dlg.start_z_ctrl.num_value)
                    end = vec3(dlg.end_x_ctrl.num_value, dlg.end_y_ctrl.num_value, dlg.end_z_ctrl.num_value)
                    vertices, count = create_line(start, end, points)
                    lookat = vec3(dlg.lookat_x_ctrl.num_value, dlg.lookat_y_ctrl.num_value, dlg.lookat_z_ctrl.num_value)
                    self._extend_actions(vertices, count, lookat, (device_id,))
        elif event.Id == PathIds.POINT.value:
            with PathgenPoint(self, self.parent.core.project.devices) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Point path added', self.core.is_dev_env)
                    device_id = int(dlg.device_choice.GetString(dlg.device_choice.Selection).split(' ')[0])
                    x = dlg.x_ctrl.num_value
                    y = dlg.y_ctrl.num_value
                    z = dlg.z_ctrl.num_value
                    lookat = vec3(dlg.lookat_x_ctrl.num_value, dlg.lookat_y_ctrl.num_value, dlg.lookat_z_ctrl.num_value)
                    self._extend_actions((x, y, z), 1, lookat, (device_id,))
        elif event.Id == PathIds.CAPSULE.value:
            with _PathgenCapsule(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Capsule path added', self.core.is_dev_env)
                    selected_devices = dlg.device_checklist.CheckedItems
                    center_points = int(dlg.centerline_points_ctrl.GetValue())
                    semicicle_points = int(dlg.semicircle_points_ctrl.GetValue())
                    buffer_dist = dlg.buffer_dist_ctrl.num_value
                    start = vec3(dlg.start_x_ctrl.num_value, dlg.centerline_y_ctrl.num_value, dlg.start_z_ctrl.num_value)
                    end = vec3(dlg.end_x_ctrl.num_value, dlg.centerline_y_ctrl.num_value, dlg.end_z_ctrl.num_value)
                    z_tilt_target = dlg.tilt_z_target_ctrl.num_value
                    vertices, count = create_slot_along_x(start, end, buffer_dist, center_points, semicicle_points, z_tilt_target)
                    devices = self.core.project.devices
                    grouped_points = defaultdict(list)
                    max_zs = defaultdict(float)
                    # group points into devices
                    for i in range(count):
                        point = vec3(vertices[i*5 : i*5+3])
                        p5 = Point5(vertices[i*5], vertices[i*5+1], vertices[i*5+2], vertices[i*5+3], vertices[i*5+4])
                        device_id = -1
                        for id_ in selected_devices:
                            max_zs[id_] = devices[id_].range_3d.upper.z
                            if devices[id_].range_3d.vec3_intersect(point, 0.0):
                                device_id = id_
                        # ignore if point not in bounds of any device
                        if device_id != -1:
                            grouped_points[device_id].append((p5,True))
                    poses = build_poses_from_XYZPT(grouped_points, [])
                    poses = interleave_poses(poses)
                    pose_sets = build_pose_sets(poses)                    
                    self.core.project.pose_sets.extend(pose_sets)
        elif event.Id == PathIds.TURNTABLE.value:
            with PathgenTurnTable(self, self.parent.core.project.devices) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Turntable path added', self.core.is_dev_env)
                    device_id = int(dlg.device_choice.GetString(dlg.device_choice.Selection).split(' ')[0])
                    x = dlg.x_ctrl.num_value
                    y = dlg.y_ctrl.num_value
                    z = dlg.z_ctrl.num_value
                    t = dlg.t_ctrl.num_value
                    p_start = dlg.p_start_ctrl.num_value
                    p_end = dlg.p_end_ctrl.num_value
                    p_total = p_end - p_start
                    p_stops = int(dlg.p_num_positions_ctrl.GetValue()) +2
                    increment = p_total/(p_stops - 1)
                    devices = self.core.project.devices
                    max_zs = defaultdict(float)
                    gen_shutter = False
                    pose_sets = [] #List[List[Pose]]
                    for i in range(p_stops):
                        if i == p_stops -1:
                            p = p_end
                        else:
                            p = p_start + (increment * i)
                        point = vec3((x,y,z))
                        p5 = Point5(x,y,z,dd_to_rad(p),dd_to_rad(t))
                        _id = -1
                        max_zs[device_id] = devices[device_id].range_3d.upper.z
                        if devices[device_id].range_3d.vec3_intersect(point, 0.0):
                            _id = device_id
                        if _id != -1:  # ignore if point not in bounds of any device
                            if dlg.shutter_chkbx.GetValue():
                                d2 = int(dlg.device2_choice.GetString(dlg.device2_choice.Selection).split(' ')[0])  
                                if d2 == device_id:
                                    pose_sets.append([build_pose_from_XYZPT(device_id,p5,True)])
                                else:
                                    x2 = dlg.x2_ctrl.num_value
                                    y2 = dlg.y2_ctrl.num_value
                                    z2 = dlg.z2_ctrl.num_value
                                    t2 = dlg.t2_ctrl.num_value
                                    p2 = dlg.p2_ctrl.num_value
                                    p5_static = Point5(x2,y2,z2,dd_to_rad(p2),dd_to_rad(t2))
                                    pose_sets.append([build_pose_from_XYZPT(device_id,p5,False)])
                                    pose_sets.append([build_pose_from_XYZPT(d2,p5_static,True)])
                            else:
                                pose_sets.append([build_pose_from_XYZPT(device_id,p5,False)])                  
                    self.core.project.pose_sets.extend(pose_sets)
        elif event.Id == PathIds.GRID.value:
            with _PathgenGrid(self, self.parent.core.project.devices) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    print_debug_msg(self.core.console, 'Gridded path added', self.core.is_dev_env)
                    devices = self.core.project.devices
                    selected_devices = dlg.device_checklist.CheckedItems
                    x = dlg.x_start_ctrl.num_value
                    y = dlg.y_start_ctrl.num_value
                    z = dlg.z_start_ctrl.num_value
                    p = dlg.p_start_ctrl.num_value
                    t = dlg.t_start_ctrl.num_value
                    x_num = int(dlg.x_poses_ctrl.GetValue())
                    y_num = int(dlg.y_poses_ctrl.GetValue())
                    z_num = int(dlg.z_poses_ctrl.GetValue())
                    p_num = int(dlg.p_poses_ctrl.GetValue())
                    t_num = int(dlg.t_poses_ctrl.GetValue())
                    x_inc = dlg.x_increment_ctrl.num_value
                    y_inc = dlg.y_increment_ctrl.num_value
                    z_inc = dlg.z_increment_ctrl.num_value
                    p_inc = dlg.p_increment_ctrl.num_value
                    t_inc = dlg.t_increment_ctrl.num_value
                    vertices = []
                    grouped_points = defaultdict(list)
                    max_zs = defaultdict(float)
                    for i_z in range(z_num):
                        for i_y in range(y_num):
                            for i_x in range(x_num):
                                for i_p in range(p_num):
                                    for i_t in range(t_num):
                                        p5 = Point5(x + x_inc * i_x, y + y_inc * i_y, z + z_inc * i_z, dd_to_rad(p + p_inc * i_p), dd_to_rad(t + t_inc * i_t))
                                        vertices.append(p5)
                                        # group points into devices
                                        device_id = -1
                                        for id_ in selected_devices:
                                             max_zs[id_] = devices[id_].range_3d.upper.z
                                             if devices[id_].range_3d.vec3_intersect(vec3(p5.x,p5.y,p5.z), 0.0):
                                                 device_id = id_
                                         # ignore if point not in bounds of any device
                                        if device_id != -1:
                                             grouped_points[device_id].append((p5,True))
                        poses = build_poses_from_XYZPT(grouped_points, [])
                    poses = build_poses_from_XYZPT(grouped_points, [])
                    poses = interleave_poses(poses)
                    pose_sets = build_pose_sets(poses)                    
                    self.core.project.pose_sets.extend(pose_sets)

    def _extend_actions(self, vertices,count: int, lookat: vec3, device_list: Tuple[int]) -> None:
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

        pose_sets = process_path(grouped_points, self.core.project.proxies, max_zs, lookat)
        self.core.project.pose_sets.extend(pose_sets)
        self.core.imaging_target = lookat

    def __del__(self) -> None:
        pass


class _PathgenCylinder(wx.Dialog):
    """Dialog to generate a cylinder path."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes _PathgenCylinder with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Cylinder Path', size=(200, -1))
        self.parent = parent
        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})', self.parent.core.project.devices))
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        options_grid = wx.FlexGridSizer(13, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)
        unit = 'mm'
        indent = '    '
        self.device_checklist = wx.CheckListBox(self, choices=self._device_choices)
        self.base_x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.base_y_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.base_z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.radius_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=100, default_unit=unit, unit_conversions=xyz_units)
        self.height_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=100, default_unit=unit, unit_conversions=xyz_units)
        self.z_div_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.points_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.lookat_x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.lookat_y_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.lookat_z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        options_grid.AddMany([
            (simple_statictext(self, 'Devices:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.device_checklist, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Base', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent}X ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.base_x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Y ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.base_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Z ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.base_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'Radius ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.radius_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, f'Height ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.height_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Z Divisions:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.z_div_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Points Per Circle:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.points_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Target', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent}X ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Y ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Z ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
        ])
        self.Sizer.Add(options_grid, 1, wx.ALL|wx.EXPAND, 4)
        self.Sizer.AddSpacer(8)
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
        self.device_checklist.Bind(wx.EVT_CHECKLISTBOX, self._on_ctrl_update)
        self.z_div_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)
        self.points_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)

    def _on_ctrl_update(self, _) -> None:
        """Enable the affirmative (OK) button if all fields have values."""
        if (not self.device_checklist.CheckedItems or
            self.z_div_ctrl.Value == '' or self.points_ctrl.Value == '' or
            not is_number(self.z_div_ctrl.Value) or not is_number(self.points_ctrl.Value)):
            self._affirmative_button.Disable()
            return

        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()


class _PathgenHelix(wx.Dialog):
    """Dialog to generate a helix path."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes _PathgenHelix with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Helix Path', size=(200, -1))
        self.parent = parent
        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})', self.parent.core.project.devices))
        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---
        unit = 'mm'
        indent = '    '

        options_grid = wx.FlexGridSizer(13, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.device_checklist = wx.CheckListBox(self, choices=self._device_choices)
        self.base_x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.base_y_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.base_z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.radius_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=100, default_unit=unit, unit_conversions=xyz_units)
        self.height_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=100, default_unit=unit, unit_conversions=xyz_units)
        self.rotation_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.points_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.lookat_x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.lookat_y_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.lookat_z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Devices:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.device_checklist, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Base', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent}X ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.base_x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Y ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.base_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Z ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.base_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'Radius ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.radius_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, f'Height ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.height_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Number of Rotations:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.rotation_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Points per Rotation:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.points_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Target', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent}X ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Y ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Z ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
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

        self.device_checklist.Bind(wx.EVT_CHECKLISTBOX, self._on_ctrl_update)
        self.rotation_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)
        self.points_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)

    def _on_ctrl_update(self, _) -> None:
        """Enable the affirmative (OK) button if all fields have values."""
        if (not self.device_checklist.CheckedItems or
            self.rotation_ctrl.Value == '' or self.points_ctrl.Value == '' or
            not is_number(self.rotation_ctrl.Value) or not is_number(self.points_ctrl.Value)):
            self._affirmative_button.Disable()
            return
        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()


class _PathgenSphere(wx.Dialog):
    """Dialog to generate a sphere path."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes _PathgenSphere with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Sphere Path', size=(200, -1))
        self.parent = parent
        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})', self.parent.core.project.devices))
        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        indent = '    '
        unit = 'mm'

        options_grid = wx.FlexGridSizer(8, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.device_checklist = wx.CheckListBox(self, choices=self._device_choices)
        self.center_x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.center_y_ctrl = FancyTextCtrl( self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.center_z_ctrl = FancyTextCtrl( self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.radius_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=100, default_unit=unit, unit_conversions=xyz_units)
        self.z_div_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.distance_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=10, default_unit=unit, unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Devices:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.device_checklist, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Target', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent}X ({unit}):', 120), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.center_x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Y ({unit}):', 120), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.center_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Z ({unit}):', 120), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.center_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'Radius ({unit}):', 120), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.radius_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Z Divisions:', 120), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.z_div_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, f'Spacing Distance ({unit}):', 130), 0,
                wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
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
        self.SetMinSize((200, -1))
        self.Fit()
        # ---

        self.device_checklist.Bind(wx.EVT_CHECKLISTBOX, self._on_ctrl_update)
        self.z_div_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)

    def _on_ctrl_update(self, _) -> None:
        """Enable the affirmative (OK) button if all fields have values."""
        if (not self.device_checklist.CheckedItems or self.z_div_ctrl.Value == '' or
            not is_number(self.z_div_ctrl.Value)):
            self._affirmative_button.Disable()
            return

        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()


class _PathgenCapsule(wx.Dialog):
    """Dialog to generate a capsule path."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes _PathgenCapsule with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Capsule Path', size=(200, -1))
        self.parent = parent

        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})',self.parent.core.project.devices))

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        indent = '    '
        unit = 'mm'

        options_grid = wx.FlexGridSizer(14, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)
        
        self.device_checklist = wx.CheckListBox(self, choices=self._device_choices)
        self.start_x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.start_z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.end_x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.end_z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.centerline_y_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.buffer_dist_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.tilt_z_target_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.centerline_points_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.semicircle_points_ctrl = wx.TextCtrl(self, size=(48, -1))


        options_grid.AddMany([
            (simple_statictext(self, 'Devices:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.device_checklist, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Start', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent} X ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.start_x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            #(simple_statictext(self, f'{indent} Y ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            #(self.start_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent} Z ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.start_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'End', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent} X ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.end_x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent} Z ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.end_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'Centerline Y ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.centerline_y_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, f'Buffer ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.buffer_dist_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, f'Tilt to Target Z ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.tilt_z_target_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Number of Points', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent} Centerline', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.centerline_points_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent} Semicircle', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.semicircle_points_ctrl, 0, wx.EXPAND|wx.TOP, -11),
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
        self.device_checklist.Bind(wx.EVT_CHECKLISTBOX, self._on_ctrl_update)
        self.centerline_points_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)
        self.semicircle_points_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)

    def _on_ctrl_update(self, _) -> None:
        """Enable the affirmative (OK) button if all fields have values."""
        if (not self.device_checklist.CheckedItems or
            self.semicircle_points_ctrl.Value == '' or not is_number(self.semicircle_points_ctrl.Value) or
            self.centerline_points_ctrl.Value == '' or not is_number(self.centerline_points_ctrl.Value)):
            self._affirmative_button.Disable()
            return

        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()


class _PathgenLine(wx.Dialog):
    """Dialog to generate a line path."""

    def __init__(self, parent, *args, **kwargs):
        """Initializes _PathgenCapsule with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Line Path', size=(200, -1))
        self.parent = parent

        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})',
            self.parent.core.project.devices))

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        indent = '    '
        unit = 'mm'

        options_grid = wx.FlexGridSizer(14, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.device_choice = wx.Choice(self, choices=self._device_choices)
        self.start_x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.start_y_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.start_z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.end_x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.end_y_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.end_z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.points_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.lookat_x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.lookat_y_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.lookat_z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Device:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.device_choice, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Start', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent} X ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.start_x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent} Y ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.start_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent} Z ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.start_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'End', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent} X ({unit}):', 72), 0,  wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.end_x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent} Y ({unit}):', 72), 0,  wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.end_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent} Z ({unit}):', 72), 0,  wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.end_z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Number of Points:', 120), 0,  wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.points_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Target', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent} X ({unit}):', 120), 0,  wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent} Y ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent} Z ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
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
            self.points_ctrl.Value == '' or not is_number(self.points_ctrl.Value)):
            self._affirmative_button.Disable()
            return

        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()


class PathgenPoint(wx.Dialog):
    """Dialog to generate a single point."""

    def __init__(self, parent, allowed_devices: List[Device], *args, **kwargs):
        """Initializes PathgenPoint with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Path Point', size=(200, -1))
        self.parent = parent

        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})', allowed_devices))

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        indent = '    '
        unit = 'mm'

        options_grid = wx.FlexGridSizer(9, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.device_choice = wx.Choice(self, choices=self._device_choices)
        self.x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.y_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.lookat_x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.lookat_y_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.lookat_z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Device:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.device_choice, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Position', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent}X ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Y ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Z ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.z_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, 'Target', 72), 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0),
            (0, 0),
            (simple_statictext(self, f'{indent}X ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_x_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Y ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
            (self.lookat_y_ctrl, 0, wx.EXPAND|wx.TOP, -11),
            (simple_statictext(self, f'{indent}Z ({unit}):', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
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
        if self.device_choice.CurrentSelection == wx.NOT_FOUND:
            self._affirmative_button.Disable()
            return

        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()


class PathgenTurnTable(wx.Dialog):
    """Dialog to generate a single point."""

    def __init__(self, parent, allowed_devices: List[Device], *args, **kwargs):
        """Initializes PathgenPoint with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Path Turntable', size=(200, -1))
        self.parent = parent
        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})', allowed_devices))
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        indent = '    '
        linear_unit = 'mm'
        rotational_unit = 'dd'
        options_grid = wx.FlexGridSizer(16, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)
        self.device_choice = wx.Choice(self, choices=self._device_choices)
        self.x_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=linear_unit, unit_conversions=xyz_units)
        self.y_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=linear_unit, unit_conversions=xyz_units)
        self.z_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=linear_unit, unit_conversions=xyz_units)
        self.t_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=rotational_unit, unit_conversions=pt_units)
        self.p_start_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=rotational_unit, unit_conversions=pt_units)
        self.p_end_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=rotational_unit, unit_conversions=pt_units)
        self.p_num_positions_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.device2_choice = wx.Choice(self, choices=self._device_choices)
        self.shutter_chkbx = wx.CheckBox(self,label="Add Camera Shutter")
        self.x2_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=linear_unit, unit_conversions=xyz_units)
        self.y2_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=linear_unit, unit_conversions=xyz_units)
        self.z2_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=linear_unit, unit_conversions=xyz_units)
        self.t2_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=rotational_unit, unit_conversions=pt_units)
        self.p2_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=rotational_unit, unit_conversions=pt_units)
        self.x2_ctrl.Enable(False)
        self.y2_ctrl.Enable(False)
        self.z2_ctrl.Enable(False)
        self.p2_ctrl.Enable(False)
        self.t2_ctrl.Enable(False)
        self.device2_choice.Enable(False)
        options_grid.Add(simple_statictext(self, 'Device:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
        options_grid.Add(self.device_choice, 0, wx.EXPAND, 0)
        options_grid.Add(simple_statictext(self, 'Turntable', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
        options_grid.Add(0, 0)
        options_grid.Add(simple_statictext(self, f'{indent}X ({linear_unit}):', 72), 0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.x_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent}Y ({linear_unit}):', 72), 0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.y_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent}Z ({linear_unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.z_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent}T ({rotational_unit}):', 120), 0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
        options_grid.Add(self.t_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent}P Start ({rotational_unit}):', 120), 0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.p_start_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent}P End ({rotational_unit}):', 120), 0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.p_end_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent}No. of Positions', 120), 0,  wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.p_num_positions_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(self.shutter_chkbx, 0, wx.EXPAND, 0)
        options_grid.Add(0, 0)
        options_grid.Add(simple_statictext(self, 'Device:', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
        options_grid.Add(self.device2_choice, 0, wx.EXPAND, 0)
        options_grid.Add(simple_statictext(self, f'{indent}X ({linear_unit}):', 72), 0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.x2_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent}Y ({linear_unit}):', 72), 0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.y2_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent}Z ({linear_unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.z2_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent}T ({rotational_unit}):', 120), 0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11),
        options_grid.Add(self.t2_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent}P ({rotational_unit}):', 120), 0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.p2_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        self.Sizer.Add(options_grid, 1, wx.ALL | wx.EXPAND, 4)
        self.Sizer.AddSpacer(8)
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
        #self.device_choice.Bind(wx.EVT_CHOICE, self._on_ctrl_update)
        self.shutter_chkbx.Bind(wx.EVT_CHECKBOX, self._on_checkbox_toggle)
        self.device2_choice.Bind(wx.EVT_CHOICE, self._on_device2_choice_change)
        self.device_choice.Bind(wx.EVT_CHOICE, self._on_device2_choice_change)
        self.p_num_positions_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)

    def _validate(self):
        if (
            (self.device_choice.CurrentSelection == wx.NOT_FOUND or self.p_num_positions_ctrl.Value == '' or not is_number(self.p_num_positions_ctrl.Value)) 
            or 
            (self.shutter_chkbx.GetValue() and self.device2_choice.CurrentSelection == wx.NOT_FOUND)
            ):
                self._affirmative_button.Disable()
                return
        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()

    def _on_checkbox_toggle(self, event):
        checkbox = event.GetEventObject()
        checked = checkbox.GetValue()
        self.x2_ctrl.Enable(checked)
        self.y2_ctrl.Enable(checked)
        self.z2_ctrl.Enable(checked)
        self.p2_ctrl.Enable(checked)
        self.t2_ctrl.Enable(checked)
        self.device2_choice.Enable(checked)
        self._validate()

    def _on_device2_choice_change(self, event):
        selection1 = self.device_choice.GetStringSelection()
        selection2 = self.device2_choice.GetStringSelection()
        if self.shutter_chkbx.GetValue():
            if selection1 == selection2:
                self.x2_ctrl.Enable(False)
                self.y2_ctrl.Enable(False)
                self.z2_ctrl.Enable(False)
                self.p2_ctrl.Enable(False)
                self.t2_ctrl.Enable(False)
            else:
                self.x2_ctrl.Enable(True)
                self.y2_ctrl.Enable(True)
                self.z2_ctrl.Enable(True)
                self.p2_ctrl.Enable(True)
                self.t2_ctrl.Enable(True)
        self._validate()
        
    def _on_ctrl_update(self, _) -> None:
        self._validate()


class _PathgenGrid(wx.Dialog):
    """Dialog to generate a gridded path."""
    def __init__(self, parent, *args, **kwargs):
        indent = '    '
        unit = 'mm'
        rotational_unit = 'dd'
        options_grid = wx.FlexGridSizer(rows=14, cols=2, vgap=12, hgap=8)

        options_grid_2 = wx.FlexGridSizer(rows=6, cols=3, vgap=12, hgap=8)
        options_grid_2.AddGrowableCol(1, 0)

        super().__init__(parent=parent, id=wx.ID_ANY, title='Add Gridded Path', size=(200, -1))
        
        self.parent = parent
        self._device_choices = list(map(lambda x: f'{x.device_id} ({x.name})',self.parent.core.project.devices))
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.device_checklist = wx.CheckListBox(self, choices=self._device_choices)
        
        self.x_start_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.y_start_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.z_start_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.p_start_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=rotational_unit, unit_conversions=pt_units)   
        self.t_start_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=rotational_unit, unit_conversions=pt_units)
        self.x_poses_ctrl = wx.TextCtrl(self, size=(48, -1), value='1')     
        self.y_poses_ctrl = wx.TextCtrl(self, size=(48, -1), value='1')   
        self.z_poses_ctrl = wx.TextCtrl(self, size=(48, -1), value='1')   
        self.p_poses_ctrl = wx.TextCtrl(self, size=(48, -1), value='1')   
        self.t_poses_ctrl = wx.TextCtrl(self, size=(48, -1), value='1')   
        self.x_increment_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.y_increment_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.z_increment_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=unit, unit_conversions=xyz_units)
        self.p_increment_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=rotational_unit, unit_conversions=pt_units)
        self.t_increment_ctrl = FancyTextCtrl(self, size=(48, -1), num_value=0, default_unit=rotational_unit, unit_conversions=pt_units)


        options_grid.Add(simple_statictext(self, label='Devices:', width=120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
        options_grid.Add(self.device_checklist, 0, wx.EXPAND, 0)
        options_grid.Add(simple_statictext(self, 'Start Pose', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
        options_grid.Add(0, 0)
        options_grid.Add(simple_statictext(self, f'{indent} X ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.x_start_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent} Y ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.y_start_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent} Z ({unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.z_start_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent} P ({rotational_unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.p_start_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid.Add(simple_statictext(self, f'{indent} T ({rotational_unit}):', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid.Add(self.t_start_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        
        options_grid_2.Add(0,0)
        options_grid_2.Add(simple_statictext(self, 'Num Poses', 72), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
        options_grid_2.Add(simple_statictext(self, 'Increment (mm or dd)', width=120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
        
        options_grid_2.Add(simple_statictext(self, f'{indent} X:', 30), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid_2.Add(self.x_poses_ctrl, 0, wx.EXPAND|wx.TOP, -11)   
        options_grid_2.Add(self.x_increment_ctrl, 0, wx.EXPAND|wx.TOP, -11)   

        options_grid_2.Add(simple_statictext(self, f'{indent} Y:', 30), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid_2.Add(self.y_poses_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid_2.Add(self.y_increment_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        
        options_grid_2.Add(simple_statictext(self, f'{indent} Z:', 30), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid_2.Add(self.z_poses_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid_2.Add(self.z_increment_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        
        options_grid_2.Add(simple_statictext(self, f'{indent} P:', 30), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid_2.Add(self.p_poses_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid_2.Add(self.p_increment_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        
        options_grid_2.Add(simple_statictext(self, f'{indent} T:', 30), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, -11)
        options_grid_2.Add(self.t_poses_ctrl, 0, wx.EXPAND|wx.TOP, -11)
        options_grid_2.Add(self.t_increment_ctrl, 0, wx.EXPAND|wx.TOP, -11)


        self.Sizer.Add(options_grid, 1, wx.ALL | wx.EXPAND, 4)
        self.Sizer.AddSpacer(8)

        self.Sizer.Add(options_grid_2, 1, wx.ALL | wx.EXPAND, 4)
        self.Sizer.AddSpacer(8)

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
        self.device_checklist.Bind(wx.EVT_CHECKLISTBOX, self._on_ctrl_update)
        self.x_poses_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)
        self.y_poses_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)
        self.z_poses_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)
        self.p_poses_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)
        self.t_poses_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)
       
    def _on_ctrl_update(self, _) -> None:
        """Enable the affirmative (OK) button if all fields have values."""
        if (not self.device_checklist.CheckedItems or
            self.x_poses_ctrl.Value == '' or not is_number(self.x_poses_ctrl.Value) or
            self.y_poses_ctrl.Value == '' or not is_number(self.y_poses_ctrl.Value) or
            self.z_poses_ctrl.Value == '' or not is_number(self.z_poses_ctrl.Value) or
            self.p_poses_ctrl.Value == '' or not is_number(self.p_poses_ctrl.Value) or
            self.t_poses_ctrl.Value == '' or not is_number(self.t_poses_ctrl.Value)):        
                self._affirmative_button.Disable()
                return
        if (not self.x_poses_ctrl.Value.isdigit() or
            not self.y_poses_ctrl.Value.isdigit() or
            not self.z_poses_ctrl.Value.isdigit() or
            not self.p_poses_ctrl.Value.isdigit() or
            not self.t_poses_ctrl.Value.isdigit()):        
                self._affirmative_button.Disable()
                return
        if (int(self.x_poses_ctrl.Value) < 1 or
            int(self.y_poses_ctrl.Value) < 1 or
            int(self.z_poses_ctrl.Value) < 1 or
            int(self.p_poses_ctrl.Value) < 1 or
            int(self.t_poses_ctrl.Value) < 1):        
                self._affirmative_button.Disable()
                return

        self._affirmative_button.Enable()
        self._affirmative_button.SetDefault()
