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

"""COPIS path section of stats panel."""

from itertools import groupby
import wx

from pydispatch import dispatcher

from copis.gui.wxutils import simple_statictext


class PathStats(wx.Panel):
    """Show info related to the path, in the stats panel."""

    def __init__(self, parent):
        text_ctrl = lambda s=wx.ALIGN_RIGHT | wx.TEXT_ALIGNMENT_RIGHT, f=None: simple_statictext(
            self, label='',
            style=s,
            font=f)

        super().__init__(parent, style=wx.BORDER_DEFAULT)

        self._parent = parent
        self._core = parent.core
        self._box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Path Stats'), wx.VERTICAL)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        path_grid = wx.FlexGridSizer(3, 2, 0, 0)
        path_grid.AddGrowableCol(1, 0)

        device_grid = wx.FlexGridSizer(len(self._core.project.devices), 3, 0, 0)
        device_grid.AddGrowableCol(1, 0)
        device_grid.AddGrowableCol(2, 0)

        self._set_count_caption = text_ctrl(f=self._parent.font)
        self._pose_count_caption = text_ctrl(f=self._parent.font)

        path_grid.AddMany([
            (simple_statictext(self, 'Total set count:',
             150, font=self._parent.font), 0, wx.EXPAND, 0),
            (self._set_count_caption, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Total pose count:',
             150, font=self._parent.font), 0, wx.EXPAND, 0),
            (self._pose_count_caption, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Per device pose count',
             150, font=self._parent.font), 0, wx.EXPAND, 0)
        ])

        self._dvc_captions = {}

        for dvc in self._core.project.devices:
            self._dvc_captions[dvc.device_id] = text_ctrl(f=self._parent.font)
            name = f'{dvc.name} {dvc.type} ({dvc.device_id})'
            device_grid.AddMany([
                (20, 0),
                (simple_statictext(
                    self, f'{name}:', 80, font=self._parent.font), 0, wx.EXPAND, 0),
                (self._dvc_captions[dvc.device_id], 0, wx.EXPAND, 0)])

        self._box_sizer.Add(path_grid, 0,
            wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        self._box_sizer.Add(device_grid, 0,
            wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

        self.Sizer.Add(self._box_sizer, 0, wx.ALL |wx.EXPAND, 5)
        self.Layout()

        self._update_path_stats()

        # Bind listeners.
        dispatcher.connect(self.on_path_changed, signal='ntf_a_list_changed')

    def _update_path_stats(self):
        c_key = lambda p: p.position.device

        sets = self._core.project.pose_sets

        if sets:
            poses = sorted(self._core.project.poses, key=c_key)
            groups = groupby(poses, c_key)

            self._set_count_caption.SetLabel(str(len(sets)))
            self._pose_count_caption.SetLabel(str(len(poses)))

            for key, group in groups:
                self._dvc_captions[key].SetLabel(str(len(list(group))))

    def _estimate_execution_time(self):
        # TODO
        pass

    def on_path_changed(self):
        """Handles path change event."""
        wx.CallAfter(self._update_path_stats)