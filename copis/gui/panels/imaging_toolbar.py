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

"""ImagingToolbar class."""


from logging.handlers import SYSLOG_UDP_PORT
import wx
import wx.lib.agw.aui as aui

from typing import List

from copis.globals import ToolIds
from copis.gui.wxutils import create_scaled_bitmap


class ImagingToolbar(aui.AuiToolBar):
    """Manage imaging toolbar."""

    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_DEFAULT, agwStyle=
            aui.AUI_TB_PLAIN_BACKGROUND)
        
        self._parent = parent
        self._core = self._parent.core
        self._tools = []
        self._actions = {}

        self._init_toolbar()

        # Using the aui.AUI_TB_OVERFLOW style flag means that the overflow button always shows
        # when the toolbar is floating, even if all the items fit.
        # This allows the overflow button to be visible only when they don't;
        # no matter if the toolbar is floating or docked.
        self.Bind(wx.EVT_MOTION,
            lambda _: self.SetOverflowVisible(not self.GetToolBarFits()))

        self.Bind(wx.EVT_TOOL, self._on_tool_selected)
        
    def _init_toolbar(self):
        """Initialize and populate toolbar.

        Icons taken from https://material.io/resources/icons/?style=baseline.
        """
        _bmp = create_scaled_bitmap('playlist_play', 24)
        _bmp_d = create_scaled_bitmap('playlist_play_disabled', 24)
        self.AddTool(ToolIds.PLAY_ALL.value, 'Play All', _bmp, _bmp_d, aui.ITEM_NORMAL,
            short_help_string='Play all/resume imaging')

        _bmp = create_scaled_bitmap('play_arrow', 24)
        _bmp_d = create_scaled_bitmap('play_arrow_disabled', 24)
        self.AddTool(ToolIds.PLAY.value, 'Play', _bmp, _bmp_d, aui.ITEM_NORMAL,
            short_help_string='Play pose/pose set')

        _bmp = create_scaled_bitmap('pause', 24)
        _bmp_d = create_scaled_bitmap('pause_disabled', 24)
        self.AddTool(ToolIds.PAUSE.value, 'Pause', _bmp, _bmp_d, aui.ITEM_NORMAL,
            short_help_string='Pause imaging')

        _bmp = create_scaled_bitmap('stop', 24)
        _bmp_d = create_scaled_bitmap('stop_disabled', 24)
        self.AddTool(ToolIds.STOP.value, 'Stop', _bmp, _bmp_d, aui.ITEM_NORMAL,
            short_help_string='Abort imaging')

        self.AddSeparator()

        _bmp = create_scaled_bitmap('photo', 24)
        _bmp_d = create_scaled_bitmap('photo_disabled', 24)
        self.AddTool(ToolIds.SNAP_SHOT.value, 'Snap a Shot', _bmp, _bmp_d, aui.ITEM_NORMAL,
            short_help_string='Take a picture')

        _bmp = create_scaled_bitmap('photos', 24)
        _bmp_d = create_scaled_bitmap('photos_disabled', 24)
        self.AddTool(ToolIds.SNAP_SHOTS.value, 'Stack Shots', _bmp, _bmp_d, aui.ITEM_NORMAL,
            short_help_string='Take focus-stacked pictures')

        self._tools.extend([ToolIds.PLAY_ALL, ToolIds.PLAY, ToolIds.PAUSE, ToolIds.STOP,
            ToolIds.SNAP_SHOT, ToolIds.SNAP_SHOTS])
        


    def _on_tool_selected(self, event: wx.CommandEvent):
        tool_id = ToolIds(event.Id)

        if tool_id in self._tools:
            if tool_id in self._actions:
                self._actions[tool_id]()
        else:
            raise NotImplementedError(f'Tool {ToolIds(event.Id)} not implemented.')

    def set_actions(self, tools_actions: List[tuple]) -> None:
        """Sets handlers and initial states for the gives tools."""
        for tool in self._tools:
            self.EnableTool(tool.value, False)

        self._actions.clear()

        if tools_actions:
            for action in tools_actions:
                tool_id, is_enabled, handler = action
                self.EnableTool(tool_id.value, is_enabled)
                if handler:
                    self._actions[tool_id] = handler

    def enable_tool(self, tool_id: ToolIds, is_enabled: bool=True) -> None:
        """Enables or disables the tool."""
        self.EnableTool(tool_id.value, is_enabled)
