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

"""wxPython util functions."""

import re
from typing import Any, Tuple

import wx
import wx.lib.newevent
import wx.svg as svg

from helpers import find_path

FancyTextUpdatedEvent, EVT_FANCY_TEXT_UPDATED_EVENT = wx.lib.newevent.NewEvent()


def set_dialog(msg: str) -> None:
    """Show a wx.MessageDialog with msg as the message."""
    dialog = wx.MessageDialog(None, msg, 'Confirm Exit', wx.OK)
    dialog.ShowModal()
    dialog.Destroy()


def create_scaled_bitmap(bmp_name: str,
                         px_cnt: int = 16) -> wx.Bitmap:
    """Return scaled wx.Bitmap from svg file name.

    Args:
        bmp_name: A string representing the svg image to convert.
        px_cnt: Optional; Size to scale to, with aspect ratio 1. Defaults to 16.
    """
    filename = 'img/' + bmp_name + '.svg'

    image = svg.SVGimage.CreateFromFile(find_path(filename)).ConvertToScaledBitmap((px_cnt, px_cnt))
    return image


def simple_statictext(parent: Any, label: str = '', width: int = -1) -> wx.StaticText:
    return wx.StaticText(
        parent,
        label=label,
        size=(width, -1),
        style=wx.ALIGN_RIGHT
    )


class FancyTextCtrl(wx.TextCtrl):
    """TextCtrl but a bit smarter.

    Args:
        num_value:
        max_precision:
        default_unit:
        unit_conversions:

    Attributes:
        num_value:
        current_unit:
    """

    def __init__(self, *args, num_value=1, max_precision=3, default_unit,
                 unit_conversions, **kwargs):
        """Inits FancyTextCtrl with constructors."""
        super().__init__(*args, **kwargs)
        self._num_value = num_value
        self._max_precision = max_precision
        self._units = dict(unit_conversions)
        self._default_unit = default_unit
        self._current_unit = default_unit

        if self._default_unit not in self._units:
            raise KeyError(f'Default unit {self._default_unit} not in unit_conversions')
        self.Value = f'{self._num_value} {self._default_unit}'

        self._selected_dirty = False
        self._text_dirty = False

        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)
        self.Bind(wx.EVT_TEXT, self.on_text_change)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter)

    def on_left_up(self, event: wx.CommandEvent) -> None:
        """On EVT_LEFT_UP, if not already focused, select digits."""
        if not self._selected_dirty:
            self._selected_dirty = True
            self.SetSelection(0, self.Value.find(' '))
        event.Skip()

    def on_set_focus(self, event: wx.CommandEvent) -> None:
        """On EVT_SET_FOCUS, select digits."""
        self.SetSelection(0, self.Value.find(' '))
        event.Skip()

    def on_kill_focus(self, event: wx.CommandEvent) -> None:
        """On EVT_KILL_FOCUS, process the updated value."""
        if self._text_dirty:
            self.Undo()
            self._text_dirty = False
        self._selected_dirty = False
        event.Skip()

    def on_text_change(self, event: wx.CommandEvent) -> None:
        """On EVT_TEXT, set dirty flag true."""
        self._text_dirty = True
        event.Skip()

    def on_text_enter(self, event: wx.CommandEvent) -> None:
        """On EVT_TEXT_ENTER, process the updated value."""
        if not self._text_dirty:
            return

        regex = re.findall(rf'(-?\d*\.?\d+)\s*({"|".join(self._units.keys())})?', self.Value)
        if len(regex) == 0:
            self.Undo()
            return
        value, unit = regex[0]

        if unit not in self._units:
            unit = self._default_unit
        self._num_value = float(value) * self._units[unit]
        self._text_dirty = False
        self._update_value()

        evt = FancyTextUpdatedEvent()
        # wxPython is dumb. WHY DOESN'T evt.EventObject = self WORK??????
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)

    def _update_value(self) -> None:
        """Update control text."""
        self.Value = f'{self._num_value:.{self._max_precision}f} {self._current_unit}'
        self._text_dirty = False

    @property
    def num_value(self) -> float:
        return self._num_value

    @num_value.setter
    def num_value(self, value) -> None:
        self._num_value = value
        self._update_value()

    @property
    def current_unit(self) -> Tuple[str, float]:
        return self._current_unit, self._units[self._current_unit]
