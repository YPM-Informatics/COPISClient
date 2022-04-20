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
from copis.helpers import print_info_msg


class ImagingToolbar(aui.AuiToolBar):
    """Manage imaging toolbar."""

    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_DEFAULT, agwStyle=
            aui.AUI_TB_PLAIN_BACKGROUND)

        self._parent = parent
        self._core = self._parent.core

        self._init_toolbar()

        self.Bind(wx.EVT_TOOL, self._on_tool_selected)

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
        print_info_msg(self._core.console, f'selected tool is: {ToolIds(event.Id)}')
