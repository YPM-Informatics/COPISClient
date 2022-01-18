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

"""Custom AUI tab art class."""

import wx
import wx.lib.agw.aui as aui

from wx.lib.agw.aui.aui_constants import (AUI_NB_BOTTOM,
    AUI_BUTTON_STATE_HIDDEN, AUI_NB_CLOSE_ON_TAB_LEFT, AUI_BUTTON_STATE_HOVER,
    AUI_BUTTON_STATE_PRESSED)
from wx.lib.agw.aui.aui_utilities import (ChopText, GetBaseColour,
    IndentPressedBitmap, StepColour, TakeScreenShot)


class CustomAuiTabArt(aui.AuiDefaultTabArt):
    """Custom tab art for SetAutoNotebookTabArt.

    Derived from
    https://github.com/wxWidgets/Phoenix/blob/master/wx/lib/agw/aui/tabart.py.
    """

    def __init__(self):
        """ Default class constructor. """
        aui.AuiDefaultTabArt.__init__(self)

        self._normal_font.PointSize -= 1
        self._selected_font.PointSize -= 1
        self._measuring_font.PointSize -= 1

    def SetDefaultColours(self, base_colour=None):
        """
        Sets the default colours, which are calculated from the given base colour.
        :param `base_colour`: an instance of :class:`wx.Colour`. If defaulted to ``None``, a colour
         is generated accordingly to the platform and theme.
        """
        if base_colour is None:
            base_colour = GetBaseColour()

        self.SetBaseColour(base_colour)
        self._border_colour = StepColour(base_colour, 80)
        self._border_pen = wx.Pen(StepColour(self._border_colour, 130))

        self._background_top_colour = StepColour(base_colour, 170)
        self._background_bottom_colour = StepColour(base_colour, 170)

        self._tab_top_colour =  wx.WHITE
        self._tab_bottom_colour = wx.WHITE
        self._tab_gradient_highlight_colour = wx.WHITE

        self._tab_inactive_top_colour = self._background_top_colour
        self._tab_inactive_bottom_colour = self._background_bottom_colour

        self._tab_text_colour = lambda page: page.text_colour
        self._tab_disabled_text_colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)

    def DrawBackground(self, dc, wnd, rect):
        """
        Draws the tab area background.
        :param `dc`: a :class:`wx.DC` device context;
        :param `wnd`: a :class:`wx.Window` instance object;
        :param wx.Rect `rect`: the tab control rectangle.
        """

        self._buttonRect = wx.Rect()

        # draw background
        agwFlags = self.GetAGWFlags()
        if agwFlags & AUI_NB_BOTTOM:
            r = wx.Rect(rect.x-1, rect.y-1, rect.width+2, rect.height+2)
        else: #for AUI_NB_TOP
            r = wx.Rect(rect.x-1, rect.y-1, rect.width+2, rect.height+2)

        dc.SetBrush(wx.Brush(self._background_top_colour))
        dc.DrawRectangle(r)

        dc.SetPen(self._border_pen)
        dc.DrawLine(0, rect.GetHeight()-1, rect.GetWidth(), rect.GetHeight()-1)

    def GetTabSize(self, dc, wnd, caption, bitmap, active, close_button_state, control=None):
        tab_size, x_extent = aui.AuiDefaultTabArt.GetTabSize(self, dc, wnd, caption, bitmap,
                                                             active, close_button_state, control)

        tab_width, tab_height = tab_size

        # modify tab height
        tab_height -= 6
        tab_width += 4
        x_extent += 4

        return (tab_width, tab_height), x_extent

    def DrawTab(self, dc, wnd, page, in_rect, close_button_state, paint_control=False):
        """
        Draws a single tab.
        :param `dc`: a :class:`wx.DC` device context;
        :param `wnd`: a :class:`wx.Window` instance object;
        :param `page`: the tab control page associated with the tab;
        :param wx.Rect `in_rect`: rectangle the tab should be confined to;
        :param integer `close_button_state`: the state of the close button on the tab;
        :param bool `paint_control`: whether to draw the control inside a tab (if any) on a :class:`MemoryDC`.
        """

        # a flat, minimal style

        # if the caption is empty, measure some temporary text
        caption = page.caption
        if not caption:
            caption = "Xj"

        dc.SetFont(self._normal_font)
        normal_textx, normal_texty, dummy = dc.GetFullMultiLineTextExtent(caption)

        control = page.control

        # figure out the size of the tab
        tab_size, x_extent = self.GetTabSize(dc, wnd, page.caption, page.bitmap,
                                             page.active, close_button_state, control)

        tab_height = tab_size[1] + 6
        tab_width = tab_size[0]
        tab_x = in_rect.x - 6
        tab_y = in_rect.y + in_rect.height - tab_height + 3

        caption = page.caption

        # select pen, brush and font for the tab to be drawn
        dc.SetFont(self._normal_font)
        textx, texty = normal_textx, normal_texty

        if not page.enabled:
            dc.SetTextForeground(self._tab_disabled_text_colour)
            pagebitmap = page.dis_bitmap
        else:
            dc.SetTextForeground(self._tab_text_colour(page))
            pagebitmap = page.bitmap

        # create points that will make the tab outline

        clip_width = tab_width
        if tab_x + clip_width > in_rect.x + in_rect.width:
            clip_width = in_rect.x + in_rect.width - tab_x

        # since the above code above doesn't play well with WXDFB or WXCOCOA,
        # we'll just use a rectangle for the clipping region for now --
        dc.SetClippingRegion(tab_x, tab_y, clip_width+1, tab_height-3)

        agwFlags = self.GetAGWFlags()

        wxPoint = wx.Point  # local opt
        if agwFlags & AUI_NB_BOTTOM:
            border_points = [wxPoint(tab_x,             tab_y),
                             wxPoint(tab_x,             tab_y+tab_height-4),
                             wxPoint(tab_x+tab_width,   tab_y+tab_height-4),
                             wxPoint(tab_x+tab_width,   tab_y)]

        else: #if (agwFlags & AUI_NB_TOP)
            border_points = [wxPoint(tab_x,             tab_y+tab_height-4),
                             wxPoint(tab_x,             tab_y),
                             wxPoint(tab_x+tab_width,   tab_y),
                             wxPoint(tab_x+tab_width,   tab_y+tab_height-4)]

        drawn_tab_yoff = border_points[1].y
        drawn_tab_height = border_points[0].y - border_points[1].y

        if page.active:
            # draw active tab
            r = wx.Rect(tab_x, tab_y, tab_width, tab_height)

            dc.SetPen(wx.Pen(self._tab_top_colour))
            dc.SetBrush(wx.Brush(self._tab_top_colour))
            dc.DrawRectangle(r)

        else:
            # draw inactive tab
            r = wx.Rect(tab_x, tab_y, tab_width, tab_height)

            dc.SetPen(wx.Pen(self._tab_inactive_top_colour))
            dc.SetBrush(wx.Brush(self._tab_inactive_top_colour))
            dc.DrawRectangle(r)

        # draw tab outline
        dc.SetPen(self._border_pen)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawPolygon(border_points)

        # remove bottom border of active tab
        if page.active:
            dc.SetPen(wx.Pen(self._tab_bottom_colour))
            dc.DrawLine(border_points[0].x+1, border_points[0].y,
                        border_points[3].x, border_points[3].y)

        text_offset = tab_x + 4
        close_button_width = 0

        if close_button_state != AUI_BUTTON_STATE_HIDDEN:
            close_button_width = self._active_close_bmp.GetWidth()

            if agwFlags & AUI_NB_CLOSE_ON_TAB_LEFT:
                text_offset += close_button_width - 5

        bitmap_offset = 0

        if pagebitmap.IsOk():

            bitmap_offset = tab_x + 8
            if agwFlags & AUI_NB_CLOSE_ON_TAB_LEFT and close_button_width:
                bitmap_offset += close_button_width - 5

            # draw bitmap
            dc.DrawBitmap(pagebitmap,
                          bitmap_offset,
                          drawn_tab_yoff + (drawn_tab_height/2) - (pagebitmap.GetHeight()/2),
                          True)

            text_offset = bitmap_offset + pagebitmap.GetWidth()
            text_offset += 3 # bitmap padding

        else:

            if agwFlags & AUI_NB_CLOSE_ON_TAB_LEFT == 0 or not close_button_width:
                text_offset = tab_x + 8

        draw_text = ChopText(dc, caption, tab_width - (text_offset-tab_x) - close_button_width)

        ypos = drawn_tab_yoff + (drawn_tab_height)/2 - (texty/2) + 1

        if control:
            if control.GetPosition() != wxPoint(text_offset+1, ypos):
                control.SetPosition(wxPoint(text_offset+1, ypos))

            if not control.IsShown():
                control.Show()

            if paint_control:
                bmp = TakeScreenShot(control.GetScreenRect())
                dc.DrawBitmap(bmp, text_offset+1, ypos, True)

            controlW, controlH = control.GetSize()
            text_offset += controlW + 4
            textx += controlW + 4

        # draw tab text
        rectx, recty, dummy = dc.GetFullMultiLineTextExtent(draw_text)
        dc.DrawLabel(draw_text, wx.Rect(text_offset, ypos, rectx, recty))

        out_button_rect = wx.Rect()

        # draw close button if necessary
        if close_button_state != AUI_BUTTON_STATE_HIDDEN:

            bmp = self._disabled_close_bmp

            if close_button_state == AUI_BUTTON_STATE_HOVER:
                bmp = self._hover_close_bmp
            elif close_button_state == AUI_BUTTON_STATE_PRESSED:
                bmp = self._pressed_close_bmp

            shift = (agwFlags & AUI_NB_BOTTOM and [1] or [0])[0]

            if agwFlags & AUI_NB_CLOSE_ON_TAB_LEFT:
                rect = wx.Rect(tab_x + 4, tab_y + (tab_height - bmp.GetHeight())/2 - shift,
                               close_button_width, tab_height)
            else:
                rect = wx.Rect(tab_x + tab_width - close_button_width - 1,
                               tab_y + (tab_height - bmp.GetHeight())/2 - shift,
                               close_button_width, tab_height)

            rect = IndentPressedBitmap(rect, close_button_state)
            dc.DrawBitmap(bmp, rect.x, rect.y-1, True)

            out_button_rect = rect

        out_tab_rect = wx.Rect(tab_x, tab_y, tab_width, tab_height)

        dc.DestroyClippingRegion()

        return out_tab_rect, out_button_rect, x_extent
