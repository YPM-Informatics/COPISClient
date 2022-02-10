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

"""TimelinePanel class.

TODO: Get timeline buttons to actually modify the action list
TODO: Overhaul timeline panel visually
"""

import wx
from pydispatch import dispatcher
from copis.command_processor import serialize_command
from copis.globals import ActionType

from copis.gui.wxutils import show_msg_dialog
from copis.helpers import is_number, rad_to_dd


class TimelinePanel(wx.Panel):
    """Timeline panel.

    Args:
        parent: Pointer to a parent wx.Frame.
    """

    _MOVE_COMMANDS = [ActionType.G0, ActionType.G1]
    _SNAP_COMMANDS = [ActionType.C0, ActionType.C1]

    def __init__(self, parent, *args, **kwargs) -> None:
        """Initializes TimelinePanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self.core = self.parent.core

        self.Sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.timeline = None
        self.timeline_writer = None

        self.init_gui()
        self.update_timeline()

        # Bind listeners.
        dispatcher.connect(self.update_timeline, signal='ntf_a_list_changed')
        dispatcher.connect(self._on_pose_selected, signal='ntf_a_selected')
        dispatcher.connect(self._on_pose_deselected, signal='ntf_a_deselected')
        dispatcher.connect(self._on_pose_set_selected, signal='ntf_s_selected')
        dispatcher.connect(self._on_pose_set_deselected, signal='ntf_s_deselected')

        self.Layout()

    def _get_device(self, device_id):
        return next(filter(lambda d: d.device_id == device_id, self.core.project.devices),
            None)

    def _get_device_caption(self, device_id):
        dvc = self._get_device(device_id)
        caption = ''

        if dvc:
            caption = f'{dvc.name} {dvc.type} ({device_id})'

        return caption.capitalize()

    def _get_action_caption(self, action):
        if action:
            if action.atype in self._MOVE_COMMANDS:
                caption = 'Move to position:'
            elif action.atype in self._SNAP_COMMANDS:
                caption = 'Snap picture within:'
            else:
                caption = serialize_command(action)
        else:
            caption = '<no action>'

        return caption

    def _get_action_arg_caption(self, action_type, arg):
        time_args = {
            'P': 'millisecond',
            'S': 'second',
            'X': 'second'
        }

        key, value = arg
        key = key.upper()

        if is_number(value):
            value = float(value)

        if key in time_args and action_type in self._SNAP_COMMANDS:
            caption = f'{value} {time_args[key]}{"s" if value != 1 else ""}'
        else:
            dd_keys = ["P", "T"]
            value = rad_to_dd(value) if key in dd_keys else value
            units = 'dd' if key in dd_keys else 'mm'
            caption = f'{key}: {value} {units}'

        return caption

    def _on_pose_set_deselected(self, set_index):
        root = self.timeline.GetRootItem()

        if not root.IsOk():
            return

        set_node, cookie = self.timeline.GetFirstChild(root)

        if set_index > 0:
            for _ in range(set_index):
                set_node, cookie = self.timeline.GetNextChild(
                    set_node, cookie)

        self.timeline.Unbind(wx.EVT_TREE_SEL_CHANGED)
        self.timeline.UnselectItem(set_node)
        self.timeline.EnsureVisible(set_node)

        if self.timeline.GetFocusedItem() == set_node:
            self.timeline.ClearFocusedItem()

        self.timeline.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_selection_changed)

    def _on_pose_set_selected(self, set_index):
        root = self.timeline.GetRootItem()

        if not root.IsOk():
            return

        set_node, cookie = self.timeline.GetFirstChild(root)

        if set_index > 0:
            for _ in range(set_index):
                set_node, cookie = self.timeline.GetNextChild(
                    set_node, cookie)

        self.timeline.Unbind(wx.EVT_TREE_SEL_CHANGED)
        self.timeline.SelectItem(set_node, True)
        self.timeline.EnsureVisible(set_node)
        self.timeline.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_selection_changed)

    def _on_pose_deselected(self, pose_index):
        set_index, idx_in_set = self._place_pose_in_sets(pose_index)

        root = self.timeline.GetRootItem()

        if not root.IsOk():
            return

        set_node, cookie = self.timeline.GetFirstChild(root)

        if set_index > 0:
            for _ in range(set_index):
                set_node, cookie = self.timeline.GetNextChild(
                    set_node, cookie)

        pose_node, cookie = self.timeline.GetFirstChild(set_node)

        if idx_in_set > 0:
            for _ in range(idx_in_set):
                pose_node, cookie = self.timeline.GetNextChild(
                    set_node, cookie)

        self.timeline.Unbind(wx.EVT_TREE_SEL_CHANGED)
        self.timeline.UnselectItem(pose_node)
        self.timeline.EnsureVisible(pose_node)

        if self.timeline.GetFocusedItem() == pose_node:
            self.timeline.ClearFocusedItem()

        self.timeline.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_selection_changed)

    def _on_pose_selected(self, pose_index):
        set_index, idx_in_set = self._place_pose_in_sets(pose_index)

        root = self.timeline.GetRootItem()

        if not root.IsOk():
            return

        pose_node, cookie = self.timeline.GetFirstChild(root)

        if set_index > 0:
            for _ in range(set_index):
                pose_node, cookie = self.timeline.GetNextChild(pose_node, cookie)

        dvc_node, cookie = self.timeline.GetFirstChild(pose_node)

        if idx_in_set > 0:
            for _ in range(idx_in_set):
                dvc_node, cookie = self.timeline.GetNextChild(pose_node, cookie)

        self.timeline.Unbind(wx.EVT_TREE_SEL_CHANGED)
        self.timeline.SelectItem(dvc_node, True)
        self.timeline.EnsureVisible(dvc_node)
        self.timeline.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_selection_changed)

    def _place_pose_in_sets(self, pose_index):
        sets = self.core.project.pose_sets
        set_index = 0
        idx_in_set = pose_index

        if pose_index >= len(sets[0]):
            for i in range(1, len(sets) + 1):
                sums = sum([len(s) for s in sets[:i]])
                if sums > pose_index:
                    set_index = i - 1
                    idx_in_set = pose_index - sum([len(s) for s in sets[:set_index]])
                    break

        return set_index, idx_in_set

    def _on_selection_changed(self, event: wx.TreeEvent) -> None:
        obj = event.EventObject
        item = event.GetItem()
        data = obj.GetItemData(item)

        if not data:
            return

        if data['item'] == 'pose':
            set_index = data['set index']
            index = data['index']
            sets = self.core.project.pose_sets

            if set_index > 0:
                idx_in_poses = sum([len(s) for s in sets[:set_index]]) + index
            else:
                idx_in_poses = index

            self.core.select_pose(idx_in_poses)
        elif data['item'] == 'set':
            self.core.select_pose_set(data["index"])

    def init_gui(self) -> None:
        """Initialize gui elements."""
        timeline_sizer = wx.BoxSizer(wx.VERTICAL)

        self.timeline = wx.TreeCtrl(self) # wx.ListBox(self, style=wx.LB_SINGLE)

        # Bind events
        self.timeline.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_selection_changed)

        timeline_sizer.Add(self.timeline, 1, wx.EXPAND)

        cmd_sizer = wx.BoxSizer()
        self.timeline_writer = wx.TextCtrl(self, size=(-1, 22))
        add_btn = wx.Button(self, label='Add', size=(50, -1))
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_command)

        cmd_sizer.AddMany([
            (self.timeline_writer, 1, 0, 0),
            (add_btn, 0, wx.ALL, -1),
        ])

        timeline_sizer.Add(cmd_sizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 2)

        self.Sizer.Add(timeline_sizer, 2, wx.EXPAND)

        # ---

        btn_sizer = wx.BoxSizer(wx.VERTICAL)

        up_btn = wx.Button(self, label='Up')
        up_btn.direction = 'up'
        up_btn.Bind(wx.EVT_BUTTON, self.on_move_command)

        down_btn = wx.Button(self, label='Down')
        down_btn.direction = 'down'
        down_btn.Bind(wx.EVT_BUTTON, self.on_move_command)

        replace_btn = wx.Button(self, label='Replace')
        replace_btn.Bind(wx.EVT_BUTTON, self.on_replace_command)

        delete_btn = wx.Button(self, label='Delete')
        delete_btn.size = 'single'
        delete_btn.Bind(wx.EVT_BUTTON, self.on_delete_command)

        delall_btn = wx.Button(self, label='Delete All')
        delall_btn.size = 'all'
        delall_btn.Bind(wx.EVT_BUTTON, self.on_delete_command)

        savetofile_btn = wx.Button(self, label='Save')
        sendall_btn = wx.Button(self, label='Send All')
        sendsel_btn = wx.Button(self, label='Send Sel')

        btn_sizer.AddMany([
            (up_btn, 0, 0, 0),
            (down_btn, 0, 0, 0),
            (replace_btn, 0, 0, 0),
            (delete_btn, 0, 0, 0),
            (delall_btn, 0, 0, 0),
            (savetofile_btn, 0, 0, 0),
            (sendall_btn, 0, 0, 0),
            (sendsel_btn, 0, 0, 0),
        ])
        self.Sizer.Add(btn_sizer, 0, wx.EXPAND, 0)

    def on_add_command(self, event: wx.CommandEvent) -> None:
        """TODO"""
        cmd = self.timeline_writer.Value
        self.add_command(cmd)
        self.parent.viewport_panel.dirty = True
        self.timeline_writer.Value = ''

    def add_command(self, cmd: str) -> None:
        if cmd != '':
            self.timeline.Append(cmd)

    def on_move_command(self, event: wx.CommandEvent) -> None:
        """TODO"""
        selected = self.timeline.StringSelection

        if selected != '':
            direction = event.EventObject.direction
            index = self.timeline.Selection
            self.timeline.Delete(index)

            if direction == 'up':
                index -= 1
            else:
                index += 1

            self.timeline.InsertItems([selected], index)

    def on_replace_command(self, event: wx.CommandEvent) -> None:
        """TODO"""
        selected = self.timeline.Selection

        if selected != -1:
            replacement = self.timeline_writer.Value

            if replacement != '':
                self.timeline.SetString(selected, replacement)
                self.timeline_writer.Value = ''
            else:
                show_msg_dialog('Please type command to replace.', 'Replace command')
        else:
            show_msg_dialog('Please select the command to replace.', 'Replace command')

    def on_delete_command(self, event: wx.CommandEvent) -> None:
        """TODO"""
        size = event.EventObject.size
        if size == 'single':
            index = self.timeline.Selection
            if index != -1:
                self.core.project.remove_pose(index)
                self.timeline.Delete(index)
            else:
                show_msg_dialog('Please select the command to delete.', 'Delete command')
        else:
            self.core.project.pose_sets.clear()

    def update_timeline(self) -> None:
        """When points are modified, redisplay timeline commands.

        Handles ntf_a_list_changed signal sent by self.core.
        """
        sets = self.core.project.pose_sets
        self.timeline.DeleteAllItems()

        if sets:
            root = self.timeline.AddRoot('Imaging path')

            for i, pose_set in enumerate(sets):
                data = {
                    'item': 'set',
                    'index': i
                }
                node = self.timeline.AppendItem(root, f'Pose set {i}', data=data)

                for j, pose in enumerate(pose_set):
                    data = {
                        'item': 'pose',
                        'set index': i,
                        'index': j
                    }
                    node_1 = self.timeline.AppendItem(node,
                        self._get_device_caption(pose.position.device), data=data)

                    for action in pose.get_actions():
                        node_2 = self.timeline.AppendItem(node_1,
                            self._get_action_caption(action))

                        for arg in action.args:
                            self.timeline.AppendItem(node_2,
                                self._get_action_arg_caption(action.atype, arg))

                self.timeline.Expand(node)
            self.timeline.Expand(root)
