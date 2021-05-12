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

"""TimelinePanel class.

TODO: Get timeline buttons to actually modify the action list
TODO: Overhaul timeline panel visually
"""

import wx
from pydispatch import dispatcher

from copis.gui.wxutils import set_dialog


class TimelinePanel(wx.Panel):
    """Timeline panel.

    Args:
        parent: Pointer to a parent wx.Frame.
    """

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits TimelinePanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent
        self.core = self.parent.core

        self.Sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.timeline = None
        self.timeline_writer = None

        self.init_gui()
        self.update_timeline()

        # bind copiscore listeners
        dispatcher.connect(self.update_timeline, signal='core_a_list_changed')

        self.Layout()

    def init_gui(self) -> None:
        """Initialize gui elements."""
        timeline_sizer = wx.BoxSizer(wx.VERTICAL)

        self.timeline = wx.ListBox(self, style=wx.LB_SINGLE)
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
        # self.core.append_point(0, tuple(map(float, cmd.split(', '))))
        self.parent.visualizer_panel.dirty = True
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
                set_dialog('Please type command to replace.')
        else:
            set_dialog('Please select the command to replace.')

    def on_delete_command(self, event: wx.CommandEvent) -> None:
        """TODO"""
        size = event.EventObject.size
        if size == 'single':
            index = self.timeline.Selection
            if index != -1:
                self.core.remove_action(index)
                self.timeline.Delete(index)
            else:
                set_dialog('Please select the command to delete.')
        else:
            self.core.clear_action()
            self.timeline.Clear()

    def update_timeline(self) -> None:
        """When points are modified, redisplay timeline commands.

        Handles core_p_list_changed signal sent by self.core.
        """
        self.timeline.Clear()
        for action in self.core.actions:
            self.add_command(f'{str(action.device)} {str(action.atype)[11:]} {str(action.args)}')
