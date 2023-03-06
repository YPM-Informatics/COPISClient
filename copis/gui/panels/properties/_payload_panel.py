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

"""COPIS pose payload properties panel."""

from functools import partial

import wx

from copis.classes import Action, Pose
from copis.globals import ActionType
from copis.gui.wxutils import simple_statictext
from copis.helpers import (
    create_action_args, get_atype_kind, is_number,
print_error_msg, print_info_msg)


class PayloadPanel(wx.Panel):
    """Show pose payload properties panel."""

    _CTRL_SIZE = (45, -1)
    _DEFAULT_SNAP_COUNT = 5

    def __init__(self, parent) -> None:
        super().__init__(parent, style=wx.BORDER_NONE)
        self._parent = parent
        self._core = parent.core
        self._pose = None

        self._box_sizer = None
        self._add_btn = None
        self._toggles = None
        self._payload_dlg = None
        self._payload_dlg_item_count = 0

    def _get_snap_count_value(self, snap_count_ctrl):
        snap_count_val = snap_count_ctrl.Value
        if is_number(snap_count_val):
            value = float(snap_count_val)
            if value < 0:
                value = abs(value)
                snap_count_ctrl.Value = str(value)

            return value

        snap_count_ctrl.Value = str(self._DEFAULT_SNAP_COUNT)
        return self._DEFAULT_SNAP_COUNT

    def _init_layout(self):
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self._box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Payload'), wx.VERTICAL)

        grid = wx.FlexGridSizer(1, 2, 0, 0)
        grid.AddGrowableCol(0)

        self._add_btn = wx.Button(self, label='Add', size=self._CTRL_SIZE, name='add')
        self._add_btn.Bind(wx.EVT_BUTTON, self._on_add_payload)

        grid.AddMany([
            (0, 0),
            (self._add_btn, 0, wx.EXPAND, 0)
        ])

        self._box_sizer.Add(grid, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)

        self.Sizer.Add(self._box_sizer, 0, wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, 5)
        self.Layout()

    def _build_serial_shot_ctrl(self):
        def on_add(spin_ctrl, event: wx.CommandEvent):
            event.EventObject.Parent.Close()

            shutter_release_time = max(0, float(spin_ctrl.Value))
            c_args = create_action_args([shutter_release_time], 'S')
            payload_item = Action(ActionType.C0, self._pose.position.device,
                len(c_args), c_args)

            if self._core.add_to_selected_pose_payload(payload_item):
                pose = self._core.project.poses[self._core.selected_pose]
                self.set_pose(pose)

        sizer = wx.FlexGridSizer(2, 1, 2, 0)
        sizer.AddGrowableCol(0, 0)
        ctrl_sizer = wx.FlexGridSizer(1, 2, 0, 0)

        shutter_release_times = wx.SpinCtrlDouble(self._payload_dlg, wx.ID_ANY,
            min=0, max=5, initial=1.5, inc=.1, size=self._CTRL_SIZE)
        add_btn = wx.Button(self._payload_dlg, wx.ID_ANY,
            label='Add')
        add_btn.Bind(wx.EVT_BUTTON, partial(on_add, shutter_release_times))

        ctrl_sizer.AddMany([
            (simple_statictext(self._payload_dlg, 'Release shutter in (seconds): ', -1),
                0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (shutter_release_times, 0, wx.EXPAND, 0)
        ])

        sizer.AddMany([
            (ctrl_sizer, 0, wx.ALIGN_CENTER, 0),
            (add_btn, 0, wx.ALIGN_RIGHT|wx.EXPAND, 0)
        ])

        return sizer

    def _build_serial_focus_ctrl(self):
        def on_add(spin_ctrl, event: wx.CommandEvent):
            event.EventObject.Parent.Close()

            shutter_release_time = max(0, float(spin_ctrl.Value))
            c_args = create_action_args([shutter_release_time], 'S')
            payload_item = Action(ActionType.C1, self._pose.position.device,
                len(c_args), c_args)

            if self._core.add_to_selected_pose_payload(payload_item):
                pose = self._core.project.poses[self._core.selected_pose]
                self.set_pose(pose)

        sizer = wx.FlexGridSizer(2, 1, 2, 0)
        sizer.AddGrowableCol(0, 0)
        ctrl_sizer = wx.FlexGridSizer(1, 2, 0, 0)

        shutter_release_times = wx.SpinCtrlDouble(self._payload_dlg, wx.ID_ANY,
            min=0, max=5, initial=1.0, inc=.1, size=self._CTRL_SIZE)
        add_btn = wx.Button(self._payload_dlg, wx.ID_ANY,
            label='Add')
        add_btn.Bind(wx.EVT_BUTTON, partial(on_add, shutter_release_times))

        ctrl_sizer.AddMany([
            (simple_statictext(self._payload_dlg, 'Release shutter in (seconds): ', -1),
                0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (shutter_release_times, 0, wx.EXPAND, 0)
        ])

        sizer.AddMany([
            (ctrl_sizer, 0, wx.ALIGN_CENTER, 0),
            (add_btn, 0, wx.ALIGN_RIGHT|wx.EXPAND, 0)
        ])

        return sizer

    def _build_serial_stack_ctrl(self):
        def on_add(directions_ctrl, steps_ctrl, count_ctrl, event: wx.CommandEvent):
            event.EventObject.Parent.Close()

            dir_sel = directions_ctrl.Selection
            dir_text = directions_ctrl.GetString(dir_sel).lower()
            direction = -1 if dir_text == 'near' else 1

            step = direction * max(0, float(steps_ctrl.Value))
            snap_count = self._get_snap_count_value(count_ctrl)
            c_args = create_action_args([step, snap_count], 'ZV')
            payload_item = Action(ActionType.HST_F_STACK, self._pose.position.device,
                len(c_args), c_args)

            if self._core.add_to_selected_pose_payload(payload_item):
                pose = self._core.project.poses[self._core.selected_pose]
                self.set_pose(pose)

        sizer = wx.FlexGridSizer(2, 1, 0, 0)
        sizer.AddGrowableCol(0, 0)
        ctrl_sizer = wx.FlexGridSizer(1, 2, 0, 0)
        cell_sizer = wx.FlexGridSizer(1, 2, 0, 0)
        cell_sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        col_sizer = wx.BoxSizer(wx.VERTICAL)

        focus_dir = wx.RadioBox(self._payload_dlg, wx.ID_ANY, 'Direction',
            choices=['Near', 'Far'], style=wx.RA_VERTICAL)
        focus_step = wx.SpinCtrlDouble(self._payload_dlg, wx.ID_ANY,
            min=0.1, max=5, initial=1.0, inc=.1, size=self._CTRL_SIZE)
        num_shots = wx.TextCtrl(self._payload_dlg, wx.ID_ANY, size=self._CTRL_SIZE,
            value=str(self._DEFAULT_SNAP_COUNT))
        add_btn = wx.Button(self._payload_dlg, wx.ID_ANY,
            label='Add')
        add_btn.Bind(wx.EVT_BUTTON, partial(on_add, focus_dir, focus_step, num_shots))

        cell_sizer.AddMany([
            (simple_statictext(self._payload_dlg, 'Increment (mm): ', -1),
                0, wx.ALIGN_CENTER_VERTICAL, 0),
            (focus_step, 0, 0, 0)
        ])

        cell_sizer_1.AddMany([
            (simple_statictext(self._payload_dlg, 'Snap count: ', -1),
                0, wx.ALIGN_CENTER_VERTICAL, 0),
            (num_shots, 0, 0, 0)
        ])

        col_sizer.AddMany([
            (cell_sizer, 0, wx.ALIGN_RIGHT|wx.BOTTOM, 5),
            (cell_sizer_1, 0, wx.ALIGN_RIGHT, 0)
        ])

        ctrl_sizer.AddMany([
            (focus_dir, 0, wx.EXPAND, 0),
            (col_sizer, 0, wx.EXPAND|wx.LEFT, 5)
        ])

        sizer.AddMany([
            (ctrl_sizer, 0, wx.ALIGN_CENTER, 0),
            (add_btn, 0, wx.ALIGN_RIGHT|wx.EXPAND, 0)
        ])

        return sizer

    def _build_edsdk_shot_ctrl(self):
        def on_add(cb_ctrl, event: wx.CommandEvent):
            event.EventObject.Parent.Close()

            do_auto_focus = 1 if cb_ctrl.Value else 0
            c_args = create_action_args([do_auto_focus], 'V')
            payload_item = Action(ActionType.EDS_SNAP, self._pose.position.device,
                len(c_args), c_args)

            if self._core.add_to_selected_pose_payload(payload_item):
                pose = self._core.project.poses[self._core.selected_pose]
                self.set_pose(pose)

        sizer = wx.FlexGridSizer(2, 1, 0, 0)
        sizer.AddGrowableCol(0, 0)

        af_option = wx.CheckBox(self._payload_dlg, wx.ID_ANY,
            label='With autofocus')
        af_option.SetValue(True)
        add_btn = wx.Button(self._payload_dlg, wx.ID_ANY,
            label='Add')
        add_btn.Bind(wx.EVT_BUTTON, partial(on_add, af_option))

        sizer.AddMany([
            (af_option, 0, wx.ALIGN_CENTER, 0),
            (add_btn, 0, wx.ALIGN_RIGHT|wx.EXPAND, 0)
        ])

        return sizer

    def _build_edsdk_focus_ctrl(self):
        def on_add(spin_ctrl, event: wx.CommandEvent):
            event.EventObject.Parent.Close()

            shutter_release_time = max(0, float(spin_ctrl.Value))
            c_args = create_action_args([shutter_release_time], 'S')
            payload_item = Action(ActionType.EDS_FOCUS, self._pose.position.device,
                len(c_args), c_args)

            if self._core.add_to_selected_pose_payload(payload_item):
                pose = self._core.project.poses[self._core.selected_pose]
                self.set_pose(pose)

        sizer = wx.FlexGridSizer(2, 1, 2, 0)
        sizer.AddGrowableCol(0, 0)
        ctrl_sizer = wx.FlexGridSizer(1, 2, 0, 0)

        shutter_release_times = wx.SpinCtrlDouble(self._payload_dlg, wx.ID_ANY,
            min=0, max=5, initial=1.0, inc=.1, size=self._CTRL_SIZE)
        add_btn = wx.Button(self._payload_dlg, wx.ID_ANY,
            label='Add')
        add_btn.Bind(wx.EVT_BUTTON, partial(on_add, shutter_release_times))

        ctrl_sizer.AddMany([
            (simple_statictext(self._payload_dlg, 'Release shutter in (seconds): ', -1),
                0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (shutter_release_times, 0, wx.EXPAND, 0)
        ])

        sizer.AddMany([
            (ctrl_sizer, 0, wx.ALIGN_CENTER, 0),
            (add_btn, 0, wx.ALIGN_RIGHT|wx.EXPAND, 0)
        ])

        return sizer

    def _build_edsdk_stack_ctrl(self):
        def on_add(directions_ctrl, steps_ctrl, count_ctrl, event: wx.CommandEvent):
            event.EventObject.Parent.Close()

            dir_sel = directions_ctrl.Selection
            dir_text = directions_ctrl.GetString(dir_sel).lower()
            direction = -1 if dir_text == 'near' else 1

            step_sel = steps_ctrl.Selection
            step_text = steps_ctrl.GetString(step_sel).lower()

            if step_text == 'small':
                step = 1
            elif step_text == 'medium':
                step = 2
            else:
                step = 3

            step = direction * step
            snap_count = self._get_snap_count_value(count_ctrl)
            c_args = create_action_args([step, snap_count], 'ZV')
            payload_item = Action(ActionType.EDS_F_STACK, self._pose.position.device,
                len(c_args), c_args)

            if self._core.add_to_selected_pose_payload(payload_item):
                pose = self._core.project.poses[self._core.selected_pose]
                self.set_pose(pose)

        sizer = wx.FlexGridSizer(2, 1, 0, 0)
        sizer.AddGrowableCol(0, 0)
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cell_sizer = wx.FlexGridSizer(1, 2, 0, 0)

        focus_dir = wx.RadioBox(self._payload_dlg, wx.ID_ANY, 'Direction',
            choices=['Near', 'Far'], style=wx.RA_VERTICAL)
        focus_step = wx.RadioBox(self._payload_dlg, wx.ID_ANY, 'Increment',
            choices=['Small', 'Medium', 'Large'], style=wx.RA_VERTICAL)
        num_shots = wx.TextCtrl(self._payload_dlg, wx.ID_ANY, size=(40, -1),
            value=str(self._DEFAULT_SNAP_COUNT))
        add_btn = wx.Button(self._payload_dlg, wx.ID_ANY,
            label='Add')
        add_btn.Bind(wx.EVT_BUTTON, partial(on_add, focus_dir, focus_step, num_shots))

        cell_sizer.AddMany([
            (simple_statictext(self._payload_dlg, 'Snap count: ', -1),
                0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
            (num_shots, 0, 0, 0)
        ])

        ctrl_sizer.AddMany([
            (focus_dir, 0, wx.EXPAND, 0),
            (focus_step, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5),
            (cell_sizer, 0, wx.EXPAND, 0)
        ])

        sizer.AddMany([
            (ctrl_sizer, 0, wx.ALIGN_CENTER, 0),
            (add_btn, 0, wx.ALIGN_RIGHT|wx.EXPAND, 0)
        ])

        return sizer

    def _on_add_payload(self, _):
        dlg_size = (100, -1)
        pos = self.GetScreenPosition()
        self._payload_dlg = wx.Dialog(self, wx.ID_ANY, 'Add Payload Item', size=dlg_size, pos=pos)
        self._payload_dlg.Sizer = wx.BoxSizer(wx.VERTICAL)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        pi_protocol = wx.RadioBox(self._payload_dlg, wx.ID_ANY, 'Protocol',
            # choices=['Remote Shutter', 'EDSDK'], style=wx.RA_VERTICAL)
            choices=['Remote Shutter'], style=wx.RA_VERTICAL)
        pi_protocol.Bind(wx.EVT_RADIOBOX, self._on_toggled)

        pi_action = wx.RadioBox(self._payload_dlg, wx.ID_ANY, 'Action',
            # choices=['Snap', 'Autofocus', 'Focus Stack'], style=wx.RA_VERTICAL)
            choices=['Snap', 'Autofocus'], style=wx.RA_VERTICAL)
        pi_action.Bind(wx.EVT_RADIOBOX, self._on_toggled)

        self._toggles = [pi_protocol, pi_action]

        header_sizer.AddMany([
            (pi_protocol, 0, wx.EXPAND, 0),
            (pi_action, 0, wx.EXPAND|wx.LEFT, 5)
        ])

        self._payload_dlg.Sizer.Add(header_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
        self._payload_dlg_item_count = len(self._payload_dlg.Children)

        toggled_ui = self._build_serial_shot_ctrl()
        self._payload_dlg.Sizer.Add(toggled_ui, 0, wx.ALL|wx.EXPAND, 5)

        self._payload_dlg.Layout()
        self._payload_dlg.SetMinSize(dlg_size)
        self._payload_dlg.Fit()
        self._payload_dlg.ShowModal()

    def _on_toggled(self, _):
        for toggle in self._toggles:
            label = toggle.GetLabelText().lower()
            selection = toggle.Selection

            if label == 'protocol':
                protocol = toggle.GetString(selection).lower()
            else:
                action = toggle.GetString(selection).lower()

        builder = None

        if protocol == 'remote shutter' and action == 'snap':
            builder = self._build_serial_shot_ctrl
        elif protocol == 'remote shutter' and action == 'autofocus':
            builder = self._build_serial_focus_ctrl
        elif protocol == 'remote shutter' and action == 'focus stack':
            builder = self._build_serial_stack_ctrl
        elif protocol == 'edsdk' and action == 'snap':
            builder = self._build_edsdk_shot_ctrl
        elif protocol == 'edsdk' and action == 'autofocus':
            builder = self._build_edsdk_focus_ctrl
        elif protocol == 'edsdk' and action == 'focus stack':
            builder = self._build_edsdk_stack_ctrl
        else:
            print_error_msg(self._core.console,
                f"Toggle '{protocol} {action}' not yet implemented.")

        if builder:
            if self._payload_dlg.Sizer.ItemCount > 1:
                self._payload_dlg.Sizer.Remove(1)

                while len(self._payload_dlg.Children) > self._payload_dlg_item_count:
                    child = self._payload_dlg.GetChildren()[self._payload_dlg_item_count]
                    self._payload_dlg.RemoveChild(child)
                    child.Destroy()

            toggled_ui = builder()
            self._payload_dlg.Sizer.Add(toggled_ui, 0, wx.ALL|wx.EXPAND, 5)

            self._payload_dlg.Sizer.RepositionChildren(self._payload_dlg.Sizer.MinSize)
            self._payload_dlg.SetMinSize(self._payload_dlg.Sizer.MinSize)
            self._payload_dlg.Fit()

    def _on_delete_payload_item(self, event: wx.CommandEvent):
        payload_index = event.EventObject.payload_index

        if self._core.delete_from_selected_pose_payload(payload_index):
            pose = self._core.project.poses[self._core.selected_pose]
            self.set_pose(pose)

    def _on_edit_payload_item(self, event: wx.CommandEvent):
        payload_index = event.EventObject.payload_index

        print_info_msg(self._core.console, f'edit payload item @ index: {payload_index}')

    def _get_payload_item_caption(self, action):
        time_args = {
            'P': 'ms',
            'S': 's',
            'X': 's'
        }

        caption = '<not implemented>'
        com_mode = get_atype_kind(action.atype)

        if com_mode in ('SER', 'HST'):
            com_mode = 'REM'

        if action.atype in self._core.LENS_COMMANDS:
            key, value = action.args[0]
            arg = ' - release shutter in'

            if action.atype == ActionType.EDS_SNAP:
                arg = ' - with autofocus' if float(value) else ''

            caption = f'{"snap" if action.atype in self._core.SNAP_COMMANDS else "autofocus"}'
            caption = f'{com_mode} {caption}{arg}'

            if key in time_args:
                caption = f'{caption} {value}{time_args[key]}'
            elif action.atype != ActionType.EDS_SNAP:
                caption = f'{caption} {value} <invalid time unit>'

        elif action.atype in self._core.F_STACK_COMMANDS:
            def get_arg_value(arg_col, arg_key):
                arg = next(filter(lambda a, k=arg_key: a[0] == k, arg_col), None)
                return float(arg[1]) if arg and arg[1] else arg

            step = get_arg_value(action.args, 'Z') or 0.0
            count = int(get_arg_value(action.args, 'V') or 0.0)
            direction = 'near' if step < 0 else 'far'
            step = abs(step)
            increment = f'{step}mm'

            if get_atype_kind(action.atype) == 'EDS':
                if step == 1:
                    increment = 'small'
                elif step == 2:
                    increment = 'medium'
                else:
                    increment = 'large'

            post_sd = get_arg_value(action.args, 'Y') or 0
            pre_sd = get_arg_value(action.args, 'X') or 0
            shutter_delays = f'shutter delays: [{pre_sd}, {post_sd}]ms' if pre_sd or post_sd else None
            shutter_hold = get_arg_value(action.args, 'P')
            return_to_start = any(arg[0] == 'T' for arg in action.args)
            feed_rate = get_arg_value(action.args, 'F')

            caption = ' '.join([f'{com_mode} stack - {count} shot{"s" if count != 1 else ""},',
                f'{direction} focus, {increment} step'])

            if shutter_delays:
                caption += f', {shutter_delays}'
            if shutter_hold:
                caption += f', shutter hold time: {shutter_hold}ms'
            if feed_rate:
                caption += f', feed rate: {feed_rate}mm_or_dd/min'
            if return_to_start:
                caption += ', return to start'

        return caption

    def set_pose(self, pose: Pose):
        """Parses the selected pose into the panel."""
        self._pose = pose

        self.DestroyChildren()
        self._init_layout()

        grid = wx.FlexGridSizer(len(pose.payload) * 2, 1, 0, 0)
        grid.AddGrowableCol(0, 0)

        for i, action in enumerate(pose.payload):
            delete_btn = wx.Button(self, label='Delete', size=self._CTRL_SIZE, name='delete')
            delete_btn.payload_index = i
            delete_btn.Bind(wx.EVT_BUTTON, self._on_delete_payload_item)

            edit_btn = wx.Button(self, label='Edit', size=self._CTRL_SIZE, name='edit')
            edit_btn.payload_index = i
            edit_btn.Bind(wx.EVT_BUTTON, self._on_edit_payload_item)

            caption_text = self._get_payload_item_caption(action)
            caption = simple_statictext(self, caption_text, width=220, style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
            caption.SetToolTip(wx.ToolTip(caption_text))

            crud_sizer = wx.BoxSizer(wx.HORIZONTAL)
            crud_sizer.AddMany([
                (edit_btn, 0, wx.EXPAND, 0),
                (delete_btn, 0, wx.EXPAND, 0)
            ])

            item_grid = wx.FlexGridSizer(1, 2, 0, 0)
            item_grid.AddGrowableCol(0, 0)
            item_grid.AddMany([
                (caption, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0),
                (crud_sizer, 0, wx.EXPAND, 0)
            ])

            grid.AddMany([
                (wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.TOP, 1),
                (item_grid, 0, wx.EXPAND, 0)
            ])

        self._box_sizer.Add(grid, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

        self.Sizer.RepositionChildren(self.Sizer.MinSize)
        self._parent.SetVirtualSize(self._parent.Sizer.MinSize)
