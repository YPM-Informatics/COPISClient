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

"""TimelinePanel class."""

from functools import partial

import copy
import wx
import wx.lib.scrolledpanel as scrolled
import wx.lib.agw as aui

from pydispatch import dispatcher

from glm import vec3
from copis.classes.action import Action
from copis.classes.pose import Pose

from copis.command_processor import serialize_command
from copis.globals import ActionType, ToolIds
from copis.gui.panels.pathgen_toolbar import PathgenPoint
from copis.gui.wxutils import prompt_for_imaging_session_path, show_msg_dialog
from copis.helpers import (create_action_args, get_heading, is_number, print_debug_msg,
    rad_to_dd, sanitize_number, sanitize_point)


class TimelinePanel(wx.Panel):
    """Timeline panel.

    Args:
        parent: Pointer to a parent wx.Frame.
    """

    _MOVE_COMMANDS = [ActionType.G0, ActionType.G1]
    _LENS_COMMANDS = [ActionType.C0, ActionType.C1,
        ActionType.EDS_SNAP, ActionType.EDS_FOCUS]

    def __init__(self, parent) -> None:
        """Initializes TimelinePanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self._parent = parent
        self.core = self._parent.core

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
        dispatcher.connect(self._on_device_position_copied, signal='ntf_device_position_copied')

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
                caption = 'Move to position'
            elif action.atype in self._LENS_COMMANDS:
                com_mode = 'EDS' if action.atype.name.startswith('EDS_') else 'SER'

                arg = ' - release shutter in'

                if action.atype == ActionType.EDS_SNAP:
                    arg = ' - do autofocus'

                snaps = [ActionType.C0, ActionType.EDS_SNAP]
                caption = \
                    f'{"snap" if action.atype in snaps else "focus"}{arg}'
                caption = f'{com_mode} {caption}'
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

        if key in time_args and action_type in self._LENS_COMMANDS:
            caption = f'{value} {time_args[key]}{"s" if value != 1 else ""}'
        elif action_type != ActionType.EDS_SNAP:
            dd_keys = ["P", "T"]
            value = rad_to_dd(value) if key in dd_keys else value
            units = 'dd' if key in dd_keys else 'mm'
            caption = f'{key}: {value} {units}'
        else:
            caption = 'yes' if float(value) else 'no'

        return caption

    def _on_device_position_copied(self, data):
        device_id, x, y, z, p, t = data
        g_args = create_action_args([x, y, z, p, t])
        c_args = create_action_args([1.5], 'S')
        payload = [Action(ActionType.C0, device_id, len(c_args), c_args)]

        self._copied_pose = Pose(Action(ActionType.G1, device_id, len(g_args), g_args), payload)

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
        for _, button in self._buttons.items():
            button.Enable(False)

        if self.timeline.GetCount() > 0:
            self._buttons['image_btn'].Enable(True)
            self._buttons['add_btn'].Enable(True)
            self._buttons['reverse_btn'].Enable(True)

        if data:
            self._buttons['delete_btn'].Enable(True)
            self._buttons['play_btn'].Enable(True)

            if data['item'] == 'set':
                set_index = data['index']
                self._buttons['set_top_btn'].Enable(True)
                self._buttons['set_up_btn'].Enable(True)
                self._buttons['set_down_btn'].Enable(True)
                self._buttons['set_bottom_btn'].Enable(True)
                self._buttons['insert_pose_set_btn'].Enable(True)

            if data['item'] == 'pose':
                set_index = data['set index']
                self._buttons['copy_pose_btn'].Enable(True)
                self._buttons['cut_pose_btn'].Enable(True)

            if self._copied_pose:
                device_id = self._copied_pose.position.device

                if self.core.project.can_add_pose(set_index, device_id):
                    self._buttons['paste_pose_btn'].Enable(True)

                self._buttons['insert_pose_btn'].Enable(True)

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
            self._toggle_buttons()
            return

        self._toggle_buttons(data)

        if data['item'] == 'pose':
            set_index = data['set index']
            index = data['index']
            idx_in_poses = self._get_index_poses(set_index, index)

            self.core.select_pose(idx_in_poses)
        elif data['item'] == 'set':
            self.core.select_pose_set(data['index'])

    def _on_key_up(self, event: wx.KeyEvent):
        keycode = event.KeyCode

        # Delete selected treeview item on delete key pressed.
        if keycode == wx.WXK_DELETE:
            self.on_delete_command(event)
        else:
            event.Skip()

    def _assert_can_image(self):
        is_connected = self.core.is_serial_port_connected
        has_path = len(self.core.project.pose_sets)
        is_homed = self.core.is_machine_homed
        can_image = is_connected and has_path and is_homed

        if not can_image:
            msg = 'The machine needs to be homed before imaging.'
            if not is_connected:
                msg = 'The machine needs to be connected for imaging.'
            elif not has_path:
                msg = 'The machine needs a path for imaging.'

            show_msg_dialog(msg, 'Imaging')

        return can_image

    def init_gui(self) -> None:
        """Initialize gui elements."""
        timeline_sizer = wx.BoxSizer(wx.VERTICAL)
        self.timeline = wx.TreeCtrl(self)
        btn_panel = scrolled.ScrolledPanel(self)
        btn_panel.SetupScrolling(scroll_x=False, scrollIntoView=False)
        btn_size = (85, -1)

        # Bind events
        self.timeline.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_selection_changed)
        self.timeline.Bind(wx.EVT_KEY_UP, self._on_key_up)

        timeline_sizer.Add(self.timeline, 1, wx.EXPAND)
        self.Sizer.Add(timeline_sizer, 2, wx.EXPAND)
        btn_sizer = wx.BoxSizer(wx.VERTICAL)

        set_top_btn = wx.Button(btn_panel, label='Set to Top', size=btn_size)
        set_top_btn.direction = 'top'
        set_top_btn.Bind(wx.EVT_BUTTON, self.on_move_command)
        self._buttons['set_top_btn'] = set_top_btn

        set_up_btn = wx.Button(btn_panel, label='Set Up', size=btn_size)
        set_up_btn.direction = 'up'
        set_up_btn.Bind(wx.EVT_BUTTON, self.on_move_command)
        self._buttons['set_up_btn'] = set_up_btn

        set_down_btn = wx.Button(btn_panel, label='Set Down', size=btn_size)
        set_down_btn.direction = 'down'
        set_down_btn.Bind(wx.EVT_BUTTON, self.on_move_command)
        self._buttons['set_down_btn'] = set_down_btn

        set_bottom_btn = wx.Button(btn_panel, label='Set to Bottom', size=btn_size)
        set_bottom_btn.direction = 'bottom'
        set_bottom_btn.Bind(wx.EVT_BUTTON, self.on_move_command)
        self._buttons['set_bottom_btn'] = set_bottom_btn

        copy_pose_btn = wx.Button(btn_panel, label='Copy Pose', size=btn_size)
        copy_pose_btn.Bind(wx.EVT_BUTTON, self.on_copy_command)
        self._buttons['copy_pose_btn'] = copy_pose_btn

        cut_pose_btn = wx.Button(btn_panel, label='Cut Pose', size=btn_size)
        cut_pose_btn.Bind(wx.EVT_BUTTON, self.on_cut_command)
        self._buttons['cut_pose_btn'] = cut_pose_btn

        paste_pose_btn = wx.Button(
            btn_panel, label='Paste Pose', size=btn_size)
        paste_pose_btn.Bind(wx.EVT_BUTTON, self.on_paste_command)
        self._buttons['paste_pose_btn'] = paste_pose_btn

        insert_pose_btn = wx.Button(
            btn_panel, label='Insert Pose', size=btn_size)
        insert_pose_btn.Bind(wx.EVT_BUTTON, self.on_insert_pose_command)
        self._buttons['insert_pose_btn'] = insert_pose_btn

        insert_pose_set_btn = wx.Button(
            btn_panel, label='Insert Pose Set', size=btn_size)
        insert_pose_set_btn.Bind(wx.EVT_BUTTON, self.on_insert_pose_set_command)
        self._buttons['insert_pose_set_btn'] = insert_pose_set_btn

        add_btn = wx.Button(btn_panel, label='Add', size=btn_size)
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_command)
        self._buttons['add_btn'] = add_btn

        reverse_btn = wx.Button(btn_panel, label='Reverse', size=btn_size)
        reverse_btn.Bind(wx.EVT_BUTTON, self.on_reverse_command)
        self._buttons['reverse_btn'] = reverse_btn

        delete_btn = wx.Button(btn_panel, label='Delete', size=btn_size)
        delete_btn.Bind(wx.EVT_BUTTON, self.on_delete_command)
        self._buttons['delete_btn'] = delete_btn

        play_btn = wx.Button(btn_panel, label='Play', size=btn_size)
        play_btn.Bind(wx.EVT_BUTTON, self.on_play_command)
        self._buttons['play_btn'] = play_btn

        image_btn = wx.Button(btn_panel, label='Play All', size=btn_size)
        image_btn.Bind(wx.EVT_BUTTON, self.on_image_command)
        self._buttons['image_btn'] = image_btn

        # ----

        btn_sizer.AddMany([
            (set_top_btn, 0, 0, 0),
            (set_up_btn, 0, 0, 0),
            (set_down_btn, 0, 0, 0),
            (set_bottom_btn, 0, 0, 0),
            (copy_pose_btn, 0, 0, 0),
            (cut_pose_btn, 0, 0, 0),
            (paste_pose_btn, 0, 0, 0),
            (insert_pose_btn, 0, 0, 0),
            (insert_pose_set_btn, 0, 0, 0),
            (add_btn, 0, 0, 0),
            (reverse_btn, 0, 0, 0),
            (delete_btn, 0, 0, 0),
            (play_btn, 0, 0, 0),
            (image_btn, 0, 0, 0)
        ])

        self._toggle_buttons()

        btn_panel.SetSizer(btn_sizer)
        btn_panel.Layout()

        self.Sizer.Add(btn_panel, 0, wx.EXPAND, 0)

    def on_add_command(self, _):
        """Adds a pose or pose set."""
        def on_add_pose_set(event: wx.CommandEvent):
            event.EventObject.Parent.Close()

            set_index = self.core.project.add_pose_set()
            self.core.select_pose_set(set_index)

        def on_add_pose(event: wx.CommandEvent):
            event.EventObject.Parent.Close()

            task = event.EventObject.Name
            dvcs = self.core.project.devices if task == 'insert_pose' else devices

            with PathgenPoint(self, dvcs) as dlg:
                if dlg.ShowModal() == wx.ID_OK:

                    device_id = int(dlg.device_choice.GetString(dlg.device_choice.Selection)
                        .split(' ')[0])
                    device = self.core.project.devices[device_id]
                    point = vec3(dlg.x_ctrl.num_value,
                        dlg.y_ctrl.num_value,
                        dlg.z_ctrl.num_value)
                    lookat = vec3(dlg.lookat_x_ctrl.num_value,
                        dlg.lookat_y_ctrl.num_value,
                        dlg.lookat_z_ctrl.num_value)

                    if device and device.range_3d.vec3_intersect(point, 0.0):
                        pan, tilt = get_heading(point, lookat)
                        s_point = sanitize_point(point)
                        s_pan = sanitize_number(pan)
                        s_tilt = sanitize_number(tilt)

                        g_args = create_action_args(
                            [s_point.x, s_point.y, s_point.z, s_pan, s_tilt])
                        c_args = create_action_args([1.5], 'S')
                        payload = [Action(ActionType.C0, device_id, len(c_args), c_args)]

                        pose = Pose(Action(ActionType.G1, device_id, len(g_args), g_args), payload)

                        if task == 'insert_pose':
                            pose_index = self.core.project.insert_pose(set_index, pose)
                        else:
                            pose_index = self.core.project.add_pose(set_index, pose)

                        idx_in_poses = self._get_index_poses(set_index, pose_index) \
                            if pose_index >= 0 else pose_index

                        self.core.select_pose(idx_in_poses)

                        if pose_index >= 0:
                            print_debug_msg(self.core.console,
                                f'Pose added to set {set_index}', self.core.is_dev_env)
                            self.core.imaging_target = lookat
                        else:
                            print_debug_msg(self.core.console,
                                f'Could not add pose to set {set_index}', self.core.is_dev_env)

        data = None
        if self.timeline.Selection.IsOk():
            data = self.timeline.GetItemData(self.timeline.Selection)

        if data:
            if data['item'] == 'set':
                set_index = data['index']
            elif data['item'] == 'pose':
                set_index = data['set index']

            devices = self.core.project.get_allowed_devices(set_index)
            dialog_size = (100, -1)
            btn_size = (85, -1)

            dialog = wx.Dialog(self, wx.ID_ADD, 'Add Path Item', size=dialog_size)
            dialog.Sizer = wx.BoxSizer(wx.VERTICAL)

            choice_grid = wx.GridSizer(3, (12, -1))

            dialog.add_set_btn = wx.Button(dialog, label='Add Pose Set', size=btn_size,
                name='add_set')
            dialog.add_set_btn.Bind(wx.EVT_BUTTON, on_add_pose_set)

            dialog.add_pose_btn = wx.Button(dialog, label='Add Pose', size=btn_size,
                name='add_pose')
            dialog.add_pose_btn.Bind(wx.EVT_BUTTON, on_add_pose)

            dialog.insert_pose_btn = wx.Button(dialog, label='Insert Pose', size=btn_size,
                name='insert_pose')
            dialog.insert_pose_btn.Bind(wx.EVT_BUTTON, on_add_pose)

            if not devices:
                dialog.add_pose_btn.Disable()

            choice_grid.AddMany([
                (dialog.add_set_btn, 0, 0, 0),
                (dialog.add_pose_btn, 0, 0, 0),
                (dialog.insert_pose_btn, 0, 0, 0)
            ])

            dialog.Sizer.Add(choice_grid, 1, wx.ALL, 4)

            dialog.Layout()
            dialog.SetMinSize(dialog_size)
            dialog.Fit()
            dialog.ShowModal()
        else:
            set_index = self.core.project.add_pose_set()
            self.core.select_pose_set(set_index)

    def on_reverse_command(self, event: wx.CommandEvent):
        """"Reverses the play order of poses or pose sets."""
        def on_reverse_pose_set(_):
            event.EventObject.Parent.Close()

            self.core.project.reverse_pose_sets()

        def on_reverse_poses(dlg, event: wx.CommandEvent):
            event.EventObject.Parent.Close()

            cl_box: wx.CheckListBox = dlg.device_checklist
            if 0 in cl_box.CheckedItems:
                self.core.project.reverse_poses()
            else:
                selections = [int(s.split()[0]) for s in cl_box.GetCheckedStrings()]
                self.core.project.reverse_poses(selections)

        def on_device_chosen(event: wx.CommandEvent):
            clicked_item = event.String
            cl_box: wx.CheckListBox = event.EventObject

            if clicked_item == cl_box.Items[0]:
                for i in range(1, cl_box.Count):
                    cl_box.Check(i, cl_box.IsChecked(0))
            elif all(cl_box.IsChecked(i) for i in range(1, cl_box.Count)):
                cl_box.Check(0, True)
            else:
                cl_box.Check(0, False)

        device_ids = list(set(p.position.device for p in self.core.project.poses))
        device_ids.sort()
        devices = [self._get_device(did) for did in device_ids]
        device_choices = list(map(lambda d: f'{d.device_id} ({d.name})', devices))
        device_choices.insert(0, 'All')

        dialog_size = (120, -1)
        btn_size = (100, -1)

        dialog = wx.Dialog(self, wx.ID_ADD, 'Reverse Items', size=dialog_size)
        dialog.Sizer = wx.BoxSizer(wx.VERTICAL)

        choice_grid = wx.FlexGridSizer(2, 2, 6, 12)

        dialog.reverse_sets_btn = wx.Button(dialog, label='Reverse Pose Sets', size=btn_size,
            name='reverse_set')
        dialog.reverse_sets_btn.Bind(wx.EVT_BUTTON, on_reverse_pose_set)

        dialog.reverse_poses_btn = wx.Button(dialog, label='Reverse Poses', size=btn_size,
            name='reverse_pose')
        dialog.reverse_poses_btn.Bind(wx.EVT_BUTTON, partial(on_reverse_poses, dialog))

        dialog.device_checklist = wx.CheckListBox(dialog, choices=device_choices,
            size=btn_size)
        dialog.device_checklist.Bind(wx.EVT_CHECKLISTBOX, on_device_chosen)

        choice_grid.AddMany([
            (0, 0),
            (dialog.device_checklist, 0, 0, 0),
            (dialog.reverse_sets_btn, 0, 0, 0),
            (dialog.reverse_poses_btn, 0, 0, 0)
        ])

        dialog.Sizer.Add(choice_grid, 0, wx.ALL, 4)

        dialog.Layout()
        dialog.SetMinSize(dialog_size)
        dialog.Fit()
        dialog.ShowModal()

    def on_play_command(self, event: wx.CommandEvent):
        """Plays the selected pose or pose set."""
        can_image = self._assert_can_image()

        if can_image:
            data = self.timeline.GetItemData(self.timeline.Selection)

            if data:
                if data['item'] == 'set':
                    poses = self.core.project.pose_sets[data['index']]
                elif data['item'] == 'pose':
                    set_index = data['set index']
                    pose_index = data['index']
                    poses = [self.core.project.pose_sets[set_index][pose_index]]

                if self._parent.properties_panel.use_last_save_session_choice:
                    proceed = True
                    path = self.core.imaging_session_path
                    keep_last = self._parent._keep_last_session_imaging_path
                else:
                    proceed, path, keep_last = prompt_for_imaging_session_path(
                        self.core.imaging_session_path)
                    self._parent._keep_last_session_imaging_path = keep_last

                if not proceed:
                    return

                pos = event.GetEventObject().GetScreenPosition()

                def play_handler():
                    self.core.play_poses(poses, path, keep_last)
                    self._parent.hide_imaging_toolbar()

                actions = [(ToolIds.PLAY, True, play_handler)]
                self._parent.show_imaging_toolbar(pos, actions)

    def on_image_command(self, event: wx.CommandEvent):
        """Start the imaging run (plays all poses)."""
        can_image = self._assert_can_image()

        if can_image:
            if self._parent.properties_panel.use_last_save_session_choice:
                proceed = True
                path = self.core.imaging_session_path
                keep_last = self._parent._keep_last_session_imaging_path
            else:
                proceed, path, keep_last = prompt_for_imaging_session_path(
                    self.core.imaging_session_path)
                self._parent._keep_last_session_imaging_path = keep_last

            if not proceed:
                return

        pos = event.GetEventObject().GetScreenPosition()
        pane: aui.AuiPaneInfo = self._parent.imaging_toolbar.GetAuiManager().GetPane(
            self._parent.imaging_toolbar)

        def play_all_handler():
            self.core.start_imaging(path, keep_last)
            pane.window.enable_tool(ToolIds.PAUSE)
            pane.window.enable_tool(ToolIds.STOP)

        def pause_handler():
            self.core.pause_work()

        def stop_handler():
            self.core.stop_work()

        actions = [(ToolIds.PLAY_ALL, True, play_all_handler),
            (ToolIds.PAUSE, False, pause_handler),
            (ToolIds.STOP, False, stop_handler)]
        self._parent.show_imaging_toolbar(pos, actions)
        dispatcher.connect(self._parent.hide_imaging_toolbar, signal='ntf_machine_idle')

    def on_copy_command(self, _):
        """Copies the selected pose."""
        data = self.timeline.GetItemData(self.timeline.Selection)

        if data and data['item'] == 'pose':
            set_index = data['set index']
            index = data['index']
            self._copied_pose = copy.deepcopy(self.core.project.pose_sets[set_index][index])
            self._toggle_buttons(data)

    def on_cut_command(self, event: wx.CommandEvent):
        """Cuts the selected pose."""
        data = self.timeline.GetItemData(self.timeline.Selection)

        if data and data['item'] == 'pose':
            set_index = data['set index']
            index = data['index']
            self._copied_pose = copy.deepcopy(self.core.project.pose_sets[set_index][index])
            self.on_delete_command(event)

    def on_paste_command(self, _):
        """Pastes the copied pose into the selected set if possible."""
        data = self.timeline.GetItemData(self.timeline.Selection)

        if data and self._copied_pose:
            set_index = data['index'] if data['item'] == 'set' else data['set index']

            if self.core.project.can_add_pose(set_index, self._copied_pose.position.device):
                pose_index = self.core.project.add_pose(
                    set_index, copy.deepcopy(self._copied_pose))

                idx_in_poses = self._get_index_poses(set_index, pose_index) \
                    if pose_index >= 0 else pose_index

                self.core.select_pose(idx_in_poses)

    def on_insert_pose_command(self, _):
        """Inserts the copied pose into the selected set. Shifts poses from the same
            camera down if necessary."""
        data = self.timeline.GetItemData(self.timeline.Selection)

        if data and self._copied_pose:
            set_index = data['index'] if data['item'] == 'set' else data['set index']

            pose_index = self.core.project.insert_pose(
                set_index, copy.deepcopy(self._copied_pose))

            idx_in_poses = self._get_index_poses(set_index, pose_index) \
                if pose_index >= 0 else pose_index

            self.core.select_pose(idx_in_poses)

    def on_insert_pose_set_command(self, _):
        """Inserts a pose set at the given index."""
        data = self.timeline.GetItemData(self.timeline.Selection)

        if data and data['item'] == 'set':
            set_index = data['index']
            set_index = self.core.project.insert_pose_set(set_index)

            self.core.select_pose_set(set_index)

    def on_move_command(self, event: wx.CommandEvent) -> None:
        """Moves a set up or down"""
        data = self.timeline.GetItemData(self.timeline.Selection)

        if data and data['item'] == 'set':
            index = data['index']
            direction = event.EventObject.direction
            set_count = len(self.core.project.pose_sets)
            new_index = None

            is_at_top = index <= 0
            is_at_bottom = index >= set_count - 1

            if direction == 'up' and not is_at_top:
                new_index = self.core.project.move_set(index, -1)
            elif direction == 'down' and not is_at_bottom:
                new_index = self.core.project.move_set(index, 1)
            elif direction == 'top' and not is_at_top:
                new_index = self.core.project.move_set(index, -1 * index)
            elif direction == 'bottom' and not is_at_bottom:
                new_index = self.core.project.move_set(index, set_count - 1 - index)

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

        self._toggle_buttons()
