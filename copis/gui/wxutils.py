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

"""wxPython util functions."""

from typing import Any, Tuple

import re
import wx
import wx.lib.newevent
import wx.svg as svg

from copis.store import Store

FancyTextUpdatedEvent, EVT_FANCY_TEXT_UPDATED_EVENT = wx.lib.newevent.NewEvent()

def prompt_for_imaging_session_path(path: str=None) -> Tuple:
    """Takes the user throughthe imaging saving path prompt tree.
        Returns a tuple that says whether to proceed and, if so where to save."""
    new_path = None
    proceed = True
    keep_last_path = False
    caption = 'Save Images to Folder'
    prompt = 'Would you like to save this imaging session?'

    if path:
        prompt = 'Would you like to save this imaging session to a new folder?\n' + \
            f'Last folder is: {path}'
        choice = show_prompt_dialog(prompt, caption, True, True, 'Save to Last Folder')
    else:
        choice = show_prompt_dialog(prompt, caption, True)

    if choice == wx.ID_NO:
        keep_last_path = True
    if choice == wx.ID_YES:
        new_path = show_folder_dialog('Save Images to Folder')
        if not new_path:
            proceed = False
    elif choice == wx.ID_HELP:
        new_path = path
    elif choice == wx.ID_CANCEL:
        proceed = False

    return (proceed, new_path, keep_last_path)

def show_folder_dialog(caption: str, path: str='') -> str:
    """Shows a wx.DirDialog to prompt for a folder."""
    dialog = wx.DirDialog(None, caption, path)
    choice = dialog.ShowModal()

    return None if choice == wx.ID_CANCEL else dialog.Path

def show_msg_dialog(msg: str, caption=' ') -> None:
    """Shows a wx.MessageDialog informational message."""
    dialog = wx.MessageDialog(None, msg, caption, wx.OK)
    dialog.ShowModal()

def show_prompt_dialog(msg: str, caption:str=' ', show_cancel_btn:bool=False,
    show_help_btn:bool=False, help_btn_label:str=None) -> Any:
    """Show a wx.MessageDialog confirmation prompt."""
    style = wx.YES_NO

    if show_cancel_btn:
        style = style|wx.CANCEL
    if show_help_btn:
        style = style|wx.HELP

    modal = wx.MessageDialog(None, msg, caption, style)

    if show_help_btn and help_btn_label:
        modal.HelpLabel = help_btn_label

    choice = modal.ShowModal()

    return choice

def create_scaled_bitmap(bmp_name: str,
                         px_cnt: int = 16) -> wx.Bitmap:
    """Return scaled wx.Bitmap from svg file name.

    Args:
        bmp_name: A string representing the svg image to convert.
        px_cnt: Optional; Size to scale to, with aspect ratio 1. Defaults to 16.
    """
    filename = 'img/' + bmp_name + '.svg'
    store = Store()

    image = svg.SVGimage.CreateFromFile(
        store.find_path(filename)
    ).ConvertToScaledBitmap((px_cnt, px_cnt))

    return image


def simple_statictext(
    parent: Any,
    label: str='',
    width: int=-1,
    style: Any=wx.ALIGN_LEFT,
    font: wx.Font=None) -> wx.StaticText:
    """Helper function for a simple static text control."""
    text_ctrl = wx.StaticText(
        parent,
        label=label,
        size=(width, -1),
        style=style
    )

    if font:
        text_ctrl.Font = font

    return text_ctrl


class FancyTextCtrl(wx.TextCtrl):
    """TextCtrl but a bit smarter.

    Args:
        num_value: Optional; A float representing initial value. Defaults to 1.
        max_precision: Optional; An integer representing the max precision to
            display. Defaults to 3.
        default_unit: A string representing the default unit.
        unit_conversions: A dictionary with pairs of (unit: str, conversion: float).

    Attributes:
        num_value: A float representing current value in the current units.
        current_unit: A tuple of current unit string and conversion from default.
    """

    def __init__(self, *args, num_value: float = 1, max_precision: int = 3,
                 default_unit: str, unit_conversions, **kwargs):
        """Initialize FancyTextCtrl with constructors."""
        super().__init__(*args, **kwargs)
        self.WindowStyle = wx.TE_PROCESS_ENTER

        self._num_value = num_value
        self._max_precision = max_precision
        self._units = dict(unit_conversions)
        self._default_unit = default_unit
        self._current_unit = default_unit

        if self._default_unit not in self._units:
            raise KeyError(f'Default unit {self._default_unit} not in unit_conversions')
        self._update_value()

        self._selected_dirty = False
        self._text_dirty = False

        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)
        self.Bind(wx.EVT_TEXT, self.on_text_change)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

    def on_left_up(self, event: wx.CommandEvent) -> None:
        """On EVT_LEFT_UP, if not already focused, select digits."""
        if not self._selected_dirty:
            self._selected_dirty = True
            self.SelectAll()
        event.Skip()

    def on_set_focus(self, event: wx.CommandEvent) -> None:
        """On EVT_SET_FOCUS, select digits."""
        self.SelectAll()
        event.Skip()

    def on_kill_focus(self, event: wx.CommandEvent) -> None:
        """On EVT_KILL_FOCUS, process the updated value."""
        if self._text_dirty:
            self._process_text()

        self._selected_dirty = False
        event.Skip()

    def on_text_change(self, event: wx.CommandEvent) -> None:
        """On EVT_TEXT, set dirty flag true."""
        self._text_dirty = True
        event.Skip()

    def on_key_down(self, event: wx.KeyEvent) -> None:
        """On EVT_KEY_DOWN, process the text if enter or tab is pressed."""
        keycode = event.KeyCode
        if not event.HasAnyModifiers() and \
            keycode in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_TAB) and \
                self._process_text():
                # Handle if "Shift" key is held.
            event.EventObject.Navigate(flags=wx.NavigationKeyEvent.IsBackward \
                if event.shiftDown else wx.NavigationKeyEvent.IsForward)

        else:
            event.Skip()

    def _process_text(self) -> bool:
        """Process updated text. Uses a regex to automatically convert between units."""
        if not self._text_dirty:
            return True

        regex = re.findall(rf'(-?\d*\.?\d+)\s*({"|".join(self._units.keys())})?', self.Value)
        if len(regex) == 0:
            self.Undo()
            return False
        value, unit = regex[0]

        if unit not in self._units:
            unit = self._default_unit
        self._num_value = float(value) * self._units[unit]
        self._text_dirty = False
        self._update_value()

        evt = FancyTextUpdatedEvent()
        evt.SetEventObject(self)

        self.SelectNone()
        wx.PostEvent(self, evt)
        return True

    def _update_value(self) -> None:
        """Update control text."""
        self.Value = f'{self._num_value:.{self._max_precision}f}'
        self._text_dirty = False

    @property
    def num_value(self) -> float:
        """Current value in the current units."""
        return self._num_value

    @num_value.setter
    def num_value(self, value) -> None:
        self._num_value = value
        self._update_value()

    @property
    def current_unit(self) -> Tuple[str, float]:
        """Tuple of current unit string and conversion from default."""
        return self._current_unit, self._units[self._current_unit]
