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

from itertools import groupby
import wx

from pydispatch import dispatcher

from copis.gui.wxutils import simple_static_text


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
        c_key = lambda p: p.position.device

        def get_arg_value(arg_col, arg_key):
            arg = next(filter(lambda a, k=arg_key: a[0] == k, arg_col), 0)
            return float(arg[1]) if arg and arg[1] else arg

        def get_counts_lbl(p_count, i_count):
            return f'{p_count or "No"} ({i_count} image{"s" if i_count != 1 else ""})'

        count_imgs = lambda p_list: len([a for p in p_list for a in p.get_actions() if a.atype in self._core.SNAP_COMMANDS])

        count_stack_imgs = lambda p_list: sum([get_arg_value(a.args, 'V') + 1 for p in p_list for a in p.get_actions() if a.atype in self._core.F_STACK_COMMANDS])

        sets = self._core.project.pose_sets

        if sets:
            poses = sorted(self._core.project.poses, key=c_key)
            groups = groupby(poses, c_key)

            pose_count = len(poses)
            img_count = int(count_imgs(poses) + count_stack_imgs(poses))

            self._set_count_caption.SetLabel(str(len(sets)))
            self._pose_count_caption.SetLabel(get_counts_lbl(pose_count, img_count))

            for key, group in groups:
                if key in [d.d_id for d in self._core.project.devices]:
                    poses = list(group)
                    pose_count = len(poses)
                    img_count = count_imgs(poses) + count_stack_imgs(poses)
                    self._dvc_captions[key].SetLabel(get_counts_lbl(pose_count, img_count))

    def _estimate_execution_time(self):
        # TODO: It would be nice to have this feature.
        pass
