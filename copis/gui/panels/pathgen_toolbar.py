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

"""PathgenToolbar class."""

import logging
import math

import glm
import numpy as np
import wx
import wx.lib.agw.aui as aui
from copis.enums import ActionType, PathIds, ToolIds, Action
from copis.gui.wxutils import (FancyTextCtrl, create_scaled_bitmap,
                               simple_statictext)
from copis.helpers import xyz_units
from copis.pathutils import get_circle, get_helix


class PathgenToolbar(aui.AuiToolBar):
    """Manage pathgen toolbar panel."""

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits ToolbarPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT, agwStyle=
            aui.AUI_TB_PLAIN_BACKGROUND|aui.AUI_TB_OVERFLOW)
        self.parent = parent
        self.core = self.parent.c

        self.serial_controller = None

        self._path_dialogs = {}

        self.init_toolbar()

        self.Bind(wx.EVT_TOOL, self.on_tool_selected)

    def init_toolbar(self) -> None:
        """Initialize and populate toolbar.

        Icons taken from https://material.io/resources/icons/?style=baseline.
        """
        # add path shape adders
        _bmp = create_scaled_bitmap('cylinder_wire', 24)
        self.AddTool(PathIds.CYLINDER.value, 'Cylinder', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add cylinder path')
        _bmp = create_scaled_bitmap('add', 24)
        self.AddTool(PathIds.HELIX.value, 'Helix', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add helix path')
        _bmp = create_scaled_bitmap('sphere_wire', 24)
        self.AddTool(PathIds.SPHERE.value, 'Sphere', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add sphere path')
        _bmp = create_scaled_bitmap('line_wire', 24)
        self.AddTool(PathIds.LINE.value, 'Line', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Add line path')

        self.AddSeparator()

        # add settings tool
        _bmp = create_scaled_bitmap('settings', 24)
        self.AddTool(ToolIds.SETTINGS.value, 'Settings', _bmp, _bmp, aui.ITEM_NORMAL, short_help_string='Edit simulation settings')

    def on_tool_selected(self, event: wx.CommandEvent) -> None:
        """On toolbar tool selected, check which and process accordingly.

        TODO: Link with copiscore when implemented.
        """
        if event.Id == PathIds.CYLINDER.value:
            with _PathgenCylinder(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    num_cams = int(dlg.num_cams_choice.GetString(dlg.num_cams_choice.Selection))
                    radius = dlg.radius_ctrl.num_value
                    height = dlg.height_ctrl.num_value
                    z_div = int(dlg.z_div_ctrl.GetValue())
                    points = int(dlg.points_ctrl.GetValue())

                    new_actions = []
                    for i in range(z_div):
                        z = i * (height / (z_div - 1))
                        vertices, count = get_circle(
                            glm.vec3(0, -height/2 + z, 0), glm.vec3(0, 1, 0), radius, points)

                        for j in range(count - 1):
                            point5 = [
                                vertices[j * 3],
                                vertices[j * 3 + 1],
                                vertices[j * 3 + 2],
                                math.atan2(vertices[j*3+2], vertices[j*3]) + math.pi,
                                math.atan(vertices[j*3+1]/math.sqrt(vertices[j*3]**2+vertices[j*3+2]**2))]

                            device_id = 0
                            if num_cams == 2 and vertices[j*3+1] < 0:
                                device_id = 1
                            new_actions.append(Action(ActionType.G0, device_id, 5, point5))
                            new_actions.append(Action(ActionType.C0, device_id))

                    self.core.actions.extend(new_actions)

        elif event.Id == PathIds.HELIX.value:
            with _PathgenHelix(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    num_cams = int(dlg.num_cams_choice.GetString(dlg.num_cams_choice.Selection))
                    radius = dlg.radius_ctrl.num_value
                    height = dlg.height_ctrl.num_value
                    rotations = int(dlg.rotation_ctrl.GetValue())
                    points = int(dlg.points_ctrl.GetValue())

                    pitch = height / rotations

                    vertices, count = get_helix(
                        glm.vec3(0, -height/2, 0), glm.vec3(0, 1, 0), radius, pitch, rotations, points)

                    new_actions = []
                    for j in range(count - 1):
                        point5 = [
                            vertices[j * 3],
                            vertices[j * 3 + 1],
                            vertices[j * 3 + 2],
                            math.atan2(vertices[j*3+2], vertices[j*3]) + math.pi,
                            math.atan(vertices[j*3+1]/math.sqrt(vertices[j*3]**2+vertices[j*3+2]**2))]

                        device_id = 0
                        if num_cams == 2 and vertices[j*3+1] < 0:
                            device_id = 1
                        new_actions.append(Action(ActionType.G0, device_id, 5, point5))
                        new_actions.append(Action(ActionType.C0, device_id))

                    self.core.actions.extend(new_actions)

        elif event.Id == PathIds.SPHERE.value:
            with _PathgenSphere(self) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    num_cams = int(dlg.num_cams_choice.GetString(dlg.num_cams_choice.Selection))
                    radius = dlg.radius_ctrl.num_value
                    z_div = int(dlg.z_div_ctrl.GetValue())
                    distance = dlg.distance_ctrl.num_value

                    new_actions = []
                    for i in range(z_div):
                        z = i * (radius*0.8 * 2 / (z_div - 1)) - radius*0.8
                        r = math.sqrt(radius * radius - z * z)
                        num = int(2 * math.pi * r / distance)

                        vertices, count = get_circle(
                            glm.vec3(0, z, 0), glm.vec3(0, 1, 0), r, num)

                        for j in range(count - 1):
                            point5 = [
                                vertices[j * 3],
                                vertices[j * 3 + 1],
                                vertices[j * 3 + 2],
                                math.atan2(vertices[j*3+2], vertices[j*3]) + math.pi,
                                math.atan(vertices[j*3+1]/math.sqrt(vertices[j*3]**2+vertices[j*3+2]**2))]

                            device_id = 0
                            if num_cams == 2 and vertices[j*3+1] < 0:
                                device_id = 1
                            new_actions.append(Action(ActionType.G0, device_id, 5, point5))
                            new_actions.append(Action(ActionType.C0, device_id))

                    self.core.actions.extend(new_actions)

        elif event.Id == PathIds.LINE.value:
            print('LINE')

    def __del__(self) -> None:
        pass


class _PathgenCylinder(wx.Dialog):
    """TODO"""

    def __init__(self, parent):
        """Inits _PathgenCylinder with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Cylinder Path', size=(250, -1))
        self.parent = parent

        self._camera_num_choices = list('123456')

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        options_grid = wx.FlexGridSizer(5, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.num_cams_choice = wx.Choice(self, choices=self._camera_num_choices)
        self.radius_ctrl = FancyTextCtrl(
            self, size=(48, -1), max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.height_ctrl = FancyTextCtrl(
            self, size=(48, -1), max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.z_div_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.points_ctrl = wx.TextCtrl(self, size=(48, -1))

        options_grid.AddMany([
            (simple_statictext(self, 'Number of Cameras:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.num_cams_choice, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Radius:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.radius_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Height:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.height_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Number of Divisions:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.z_div_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Points Per Circle:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.points_ctrl, 0, wx.EXPAND, 0),
        ])

        self.Sizer.Add(options_grid, 1, wx.ALL | wx.EXPAND, 4)

        self.Sizer.AddSpacer(8)

        self.Sizer.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 4)

        self.Layout()


class _PathgenHelix(wx.Dialog):
    """TODO"""

    def __init__(self, parent):
        """Inits _PathgenHelix with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Helix Path', size=(250, -1))
        self.parent = parent

        self._camera_num_choices = list('123456')

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        options_grid = wx.FlexGridSizer(5, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.num_cams_choice = wx.Choice(self, choices=self._camera_num_choices)
        self.radius_ctrl = FancyTextCtrl(
            self, size=(48, -1), max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.height_ctrl = FancyTextCtrl(
            self, size=(48, -1), max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.rotation_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.points_ctrl = wx.TextCtrl(self, size=(48, -1))

        options_grid.AddMany([
            (simple_statictext(self, 'Number of Cameras:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.num_cams_choice, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Radius:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.radius_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Height:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.height_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Number of Rotations:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.rotation_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Points per Rotation:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.points_ctrl, 0, wx.EXPAND, 0),
        ])

        self.Sizer.Add(options_grid, 1, wx.ALL | wx.EXPAND, 4)

        self.Sizer.AddSpacer(8)

        self.Sizer.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 4)

        self.Layout()


class _PathgenSphere(wx.Dialog):
    """TODO"""

    def __init__(self, parent):
        """Inits _PathgenSphere with constructors."""
        super().__init__(parent, wx.ID_ANY, 'Add Sphere Path', size=(250, -1))
        self.parent = parent

        self._camera_num_choices = list('123456')

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        # ---

        options_grid = wx.FlexGridSizer(5, 2, 12, 8)
        options_grid.AddGrowableCol(1, 0)

        self.num_cams_choice = wx.Choice(self, choices=self._camera_num_choices)
        self.radius_ctrl = FancyTextCtrl(
            self, size=(48, -1), max_precision=0, default_unit='mm', unit_conversions=xyz_units)
        self.z_div_ctrl = wx.TextCtrl(self, size=(48, -1))
        self.distance_ctrl = FancyTextCtrl(
            self, size=(48, -1), max_precision=0, default_unit='mm', unit_conversions=xyz_units)

        options_grid.AddMany([
            (simple_statictext(self, 'Number of Cameras:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.num_cams_choice, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Radius:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.radius_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Number of Height Divisions:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.z_div_ctrl, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Distance Between Points:', 120), 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (self.distance_ctrl, 0, wx.EXPAND, 0),
        ])

        self.Sizer.Add(options_grid, 1, wx.ALL | wx.EXPAND, 4)

        self.Sizer.AddSpacer(8)

        self.Sizer.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 4)

        self.Layout()