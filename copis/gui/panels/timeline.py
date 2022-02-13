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

import copy
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
        self._buttons = {}
        self._copied_pose = None

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
            self._toggle_buttons()

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
        data = self.timeline.GetItemData(set_node)
        self._toggle_buttons(data)

        self.timeline.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_selection_changed)

    def _on_pose_deselected(self, pose_index):

        root = self.timeline.GetRootItem()

        if not root.IsOk():
            return

        set_index, idx_in_set = self._place_pose_in_sets(pose_index)
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
            self._toggle_buttons()

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
        data = self.timeline.GetItemData(dvc_node)
        self._toggle_buttons(data)

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

    def _toggle_buttons(self, data=None):
        for key in self._buttons:
            self._buttons[key].Enable(False)

        if data:
            self._buttons['add_btn'].Enable(True)
            self._buttons['delete_btn'].Enable(True)
            self._buttons['play_btn'].Enable(True)
            self._buttons['image_btn'].Enable(True)

            if data['item'] == 'set':
                set_index = data['index']
                self._buttons['set_up_btn'].Enable(True)
                self._buttons['set_down_btn'].Enable(True)

            if data['item'] == 'pose':
                set_index = data['set index']
                self._buttons['copy_pose_btn'].Enable(True)

            if self._copied_pose:
                device_id = self._copied_pose.position.device

                if self.core.project.can_add_pose(set_index, device_id):
                    self._buttons['paste_pose_btn'].Enable(True)

    def _get_index_poses(self, set_index, pose_index):
        sets = self.core.project.pose_sets

        if set_index > 0:
            idx_in_poses = sum([len(s) for s in sets[:set_index]]) + pose_index
        else:
            idx_in_poses = pose_index

        return idx_in_poses

    def _on_selection_changed(self, event: wx.TreeEvent) -> None:
        obj = event.EventObject
        item = event.GetItem()
        data = obj.GetItemData(item)

        if not data:
            return

        self._toggle_buttons(data)

        if data['item'] == 'pose':
            set_index = data['set index']
            index = data['index']
            idx_in_poses = self._get_index_poses(set_index, index)

            self.core.select_pose(idx_in_poses)
        elif data['item'] == 'set':
            self.core.select_pose_set(data['index'])

    def init_gui(self) -> None:
        """Initialize gui elements."""
        timeline_sizer = wx.BoxSizer(wx.VERTICAL)
        self.timeline = wx.TreeCtrl(self)
        btn_size = (75, -1)

        # Bind events
        self.timeline.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_selection_changed)

        timeline_sizer.Add(self.timeline, 1, wx.EXPAND)
        self.Sizer.Add(timeline_sizer, 2, wx.EXPAND)
        btn_sizer = wx.BoxSizer(wx.VERTICAL)

        set_up_btn = wx.Button(self, label='Set up', size=btn_size)
        set_up_btn.direction = 'up'
        set_up_btn.Bind(wx.EVT_BUTTON, self.on_move_command)
        self._buttons['set_up_btn'] = set_up_btn

        set_down_btn = wx.Button(self, label='Set down', size=btn_size)
        set_down_btn.direction = 'down'
        set_down_btn.Bind(wx.EVT_BUTTON, self.on_move_command)
        self._buttons['set_down_btn'] = set_down_btn

        copy_pose_btn = wx.Button(self, label='Copy pose', size=btn_size)
        copy_pose_btn.Bind(wx.EVT_BUTTON, self.on_copy_command)
        self._buttons['copy_pose_btn'] = copy_pose_btn

        paste_pose_btn = wx.Button(self, label='Paste pose', size=btn_size)
        paste_pose_btn.Bind(wx.EVT_BUTTON, self.on_paste_command)
        self._buttons['paste_pose_btn'] = paste_pose_btn

        # Set & pose operations.
        add_btn = wx.Button(self, label='Add', size=btn_size)
        self._buttons['add_btn'] = add_btn

        delete_btn = wx.Button(self, label='Delete', size=btn_size)
        delete_btn.Bind(wx.EVT_BUTTON, self.on_delete_command)
        self._buttons['delete_btn'] = delete_btn

        play_btn = wx.Button(self, label='Play', size=btn_size)
        self._buttons['play_btn'] = play_btn

        image_btn = wx.Button(self, label='Play all', size=btn_size)
        self._buttons['image_btn'] = image_btn
        # ----

        btn_sizer.AddMany([
            (set_up_btn, 0, 0, 0),
            (set_down_btn, 0, 0, 0),
            (copy_pose_btn, 0, 0, 0),
            (paste_pose_btn, 0, 0, 0),
            (add_btn, 0, 0, 0),
            (delete_btn, 0, 0, 0),
            (play_btn, 0, 0, 0),
            (image_btn, 0, 0, 0)
        ])

        self._toggle_buttons()

        self.Sizer.Add(btn_sizer, 0, wx.EXPAND, 0)

    def on_copy_command(self, _):
        """Copies the selected pose."""
        data = self.timeline.GetItemData(self.timeline.Selection)

        if data['item'] == 'pose':
            set_index = data['set index']
            index = data['index']
            self._copied_pose = self.core.project.pose_sets[set_index][index]
            self._toggle_buttons(data)

    def on_paste_command(self, _):
        """Pastes the copied pose into the selected set if possible. """
        data = self.timeline.GetItemData(self.timeline.Selection)

        if data and self._copied_pose:
            set_index = data['index'] if data['item'] == 'set' else data['set index']

            if self.core.project.can_add_pose(set_index, self._copied_pose.position.device):
                self.core.project.add_pose(set_index, copy.deepcopy(self._copied_pose))
                self.core.select_pose_set(set_index)

    def on_move_command(self, event: wx.CommandEvent) -> None:
        """Moves a set up or down"""
        data = self.timeline.GetItemData(self.timeline.Selection)

        if data and data['item'] == 'set':
            index = data['index']
            direction = event.EventObject.direction
            set_count = len(self.core.project.pose_sets)
            new_index = None

            if direction == 'up' and index > 0:
                self.core.project.move_set(index, -1)
                new_index = index - 1
            elif direction == 'down' and index < set_count - 1:
                self.core.project.move_set(index, 1)
                new_index = index + 1

            if new_index is not None and new_index >= 0:
                self.core.select_pose_set(new_index)
                self._toggle_buttons(data)

    def on_delete_command(self, _) -> None:
        """Deletes the selected pose or pose set."""
        data = self.timeline.GetItemData(self.timeline.Selection)

        if data:
            if data['item'] == 'set':
                set_index = data['index']

                self.core.select_pose_set(-1)
                self.core.project.delete_pose_set(set_index)
                self.core.select_pose_set(set_index - 1)
            elif data['item'] == 'pose':
                set_index = data['set index']
                pose_index = data['index']
                prev_pose_index = pose_index - 1

                self.core.select_pose(-1)
                self.core.project.delete_pose(set_index, pose_index)

                if prev_pose_index < 0:
                    self.core.select_pose_set(set_index)
                else:
                    idx_in_poses = self._get_index_poses(set_index, prev_pose_index)
                    self.core.select_pose(idx_in_poses)


    def update_timeline(self) -> None:
        """When points are modified, redisplay timeline commands.

        Handles ntf_a_list_changed signal sent by self.core.
        """
        sets = self.core.project.pose_sets
        self.timeline.DeleteAllItems()
        self._toggle_buttons()

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
