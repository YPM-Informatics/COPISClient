# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""COPIS path section of stats panel."""

import operator as op
from itertools import groupby
import wx

from pydispatch import dispatcher

from copis.gui.wxutils import simple_static_text
from copis.models.g_code import Gcode


class PathStats(wx.Panel):
    """Show info related to the path, in the stats panel."""

    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_DEFAULT)

        self._parent = parent
        self._core = parent.core

        self._build_panel()

        # Bind listeners.
        dispatcher.connect(self._on_path_changed, signal='ntf_a_list_changed')
        dispatcher.connect(self._on_device_list_changed, signal='ntf_d_list_changed')

    def _build_panel(self):
        def text_ctrl():
            return simple_static_text(self, style=wx.ALIGN_RIGHT|wx.TEXT_ALIGNMENT_RIGHT, font=self._parent.font)

        self._box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Path Stats'), wx.VERTICAL)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        path_grid = wx.FlexGridSizer(3, 2, 0, 0)
        path_grid.AddGrowableCol(1, 0)

        device_grid = wx.FlexGridSizer(len(self._core.project.devices), 3, 0, 0)
        device_grid.AddGrowableCol(1, 0)
        device_grid.AddGrowableCol(2, 0)

        self._set_count_caption = text_ctrl()
        self._pose_count_caption = text_ctrl()

        path_grid.AddMany([
            (simple_static_text(self, 'Total set count:',
             150, font=self._parent.font), 0, wx.EXPAND, 0),
            (self._set_count_caption, 0, wx.EXPAND, 0),
            (simple_static_text(self, 'Total pose count:',
             150, font=self._parent.font), 0, wx.EXPAND, 0),
            (self._pose_count_caption, 0, wx.EXPAND, 0),
            (simple_static_text(self, 'Per device pose count',
             150, font=self._parent.font), 0, wx.EXPAND, 0)
        ])

        self._dvc_captions = {}

        for dvc in self._core.project.devices:
            self._dvc_captions[dvc.d_id] = text_ctrl()
            name = f'{dvc.name} {dvc.type} ({dvc.d_id})'
            device_grid.AddMany([
                (20, 0),
                (simple_static_text(
                    self, f'{name}:', 80, font=self._parent.font), 0, wx.EXPAND, 0),
                (self._dvc_captions[dvc.d_id], 0, wx.EXPAND, 0)])

        self._box_sizer.Add(path_grid, 0,
            wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        self._box_sizer.Add(device_grid, 0,
            wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

        self.Sizer.Add(self._box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.Layout()

        self._update_path_stats()

    def _on_device_list_changed(self):
        self.DestroyChildren()
        self._build_panel()

    def _on_path_changed(self):
        """Handles path change event."""
        # Call the specified function after the current and pending event handlers have been completed.
        # This is good for making GUI method calls from non-GUI threads, in order to prevent hangs.
        wx.CallAfter(self._update_path_stats)

    def _update_path_stats(self):
        def get_counts_lbl(p_count, i_count):
            return f'{p_count or "No"} ({i_count} image{"s" if i_count != 1 else ""})'

        def get_img_count(moves):
            return len([m for m in moves \
                        if m.end_pose and m.end_pose.position != (m.start_pose.position if m.start_pose else None) and any(Gcode[a.type.value] in self._core.SNAP_COMMANDS for a in m.end_pose.actions)])

        def get_stack_count(moves):
            actions_lists = [m.end_pose.actions for m in moves \
                        if m.end_pose and m.end_pose.position != (m.start_pose.position if m.start_pose else None) and any(Gcode[a.type.value] in self._core.F_STACK_COMMANDS for a in m.end_pose.actions)]

            return sum(a.step_count + 1 for l in actions_lists for a in l if Gcode[a.type.value] in self._core.F_STACK_COMMANDS)

        move_sets = self._core.project.move_sets

        if move_sets:
            moves = [m for l in move_sets for m in l]
            keyed_moves = groupby(sorted(moves, key=op.attrgetter('device.d_id')), op.attrgetter('device.d_id'))

            pose_count = len([m for m in moves if m.end_pose and m.end_pose.position != (m.start_pose.position if m.start_pose else None)])
            img_count = get_img_count(moves) + get_stack_count(moves)

            self._set_count_caption.SetLabel(str(len(move_sets)))
            self._pose_count_caption.SetLabel(get_counts_lbl(pose_count, img_count))

            for key, group in keyed_moves:
                if key in [d.d_id for d in self._core.project.devices]:
                    g_list = list(group)
                    pose_count = len([m for m in g_list if m.end_pose and m.end_pose.position != (m.start_pose.position if m.start_pose else None)])
                    img_count = get_img_count(g_list) + get_stack_count(g_list)
                    self._dvc_captions[key].SetLabel(get_counts_lbl(pose_count, img_count))

    def _estimate_execution_time(self):
        # TODO: It would be nice to have this feature.
        pass
