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

"""ImagingToolbar class."""


import wx
import wx.lib.agw.aui as aui

from copis.globals import ToolIds
from copis.gui.wxutils import create_scaled_bitmap


class ImagingToolbar(aui.AuiToolBar):
    """Manage imaging toolbar."""

    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_DEFAULT, agwStyle=
            aui.AUI_TB_PLAIN_BACKGROUND)

        self._parent = parent
        self._core = self._parent.core

        self._init_toolbar()

        # Using the aui.AUI_TB_OVERFLOW style flag means that the overflow button always shows
        # when the toolbar is floating, even if all the items fit.
        # This allows the overflow button to be visible only when they don't;
        # no matter if the toolbar is floating or docked.
        self.Bind(wx.EVT_MOTION,
            lambda _: self.SetOverflowVisible(not self.GetToolBarFits()))

    def _init_toolbar(self):
        """Initialize and populate toolbar.

        Icons taken from https://material.io/resources/icons/?style=baseline.
        """
        _bmp = create_scaled_bitmap('playlist_play', 24)
        self.AddTool(ToolIds.PLAY_ALL.value, 'Play', _bmp, _bmp, aui.ITEM_NORMAL,
            short_help_string='Play all/resume imaging')

        _bmp = create_scaled_bitmap('play_arrow', 24)
        self.AddTool(ToolIds.PLAY.value, 'Play', _bmp, _bmp, aui.ITEM_NORMAL,
                     short_help_string='Play pose/pose set')

        _bmp = create_scaled_bitmap('pause', 24)
        self.AddTool(ToolIds.PAUSE.value, 'Pause', _bmp, _bmp, aui.ITEM_NORMAL,
            short_help_string='Pause imaging')

        _bmp = create_scaled_bitmap('stop', 24)
        self.AddTool(ToolIds.STOP.value, 'Stop', _bmp, _bmp, aui.ITEM_NORMAL,
            short_help_string='Abort imaging')

    def _on_tool_selected(self, event: wx.CommandEvent):
        tool_id = ToolIds(event.Id)
        if tool_id == ToolIds.PLAY_ALL:
            pass
        elif tool_id == ToolIds.PLAY:
            pass
        elif tool_id == ToolIds.PAUSE:
            pass
        elif tool_id == ToolIds.STOP:
            pass
        else:
            raise NotImplementedError(f'Tool {ToolIds(event.Id)} not implemented.')
