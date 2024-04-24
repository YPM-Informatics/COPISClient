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

"""ViewportPanel class."""

import wx

from copis.gl.glcanvas import GLCanvas3D


class ViewportPanel(wx.Panel):
    """Viewport panel. Creates a GLCanvas3D OpenGL canvas.

    Args:
        parent: Pointer to a parent wx.Frame.

    Attributes:
        dirty: A boolean indicating if the OpenGL canvas needs updating or not.
        glcanvas: Read only; A GLCanvas3D object.
        bbox_shown: A boolean indicating if the canvas chamber bounding box is
            shown or not.
        axes_shown: A boolean indicating if the canvas axes is shown or not.
    """

    def __init__(self, parent) -> None:
        """Initialize ViewportPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.core = parent.core

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self._build_dimensions = parent.chamber_dimensions
        self._zoom_slider = None

        self._glcanvas = GLCanvas3D(self, build_dimensions=self._build_dimensions, every=100,subdivisions=10)
        self.init_gui()

        self.Layout()

    def init_gui(self) -> None:
        """Initialize gui elements."""

        # add GLCanvas3D
        self.Sizer.Add(self._glcanvas, 1, wx.EXPAND|wx.ALL, 0)

        navbar = wx.Panel(self, wx.ID_ANY, size=(-1, 23), style=wx.BORDER_DEFAULT)
        navbar.Sizer = wx.BoxSizer(wx.HORIZONTAL)

        navbar_left_sizer = wx.BoxSizer(wx.HORIZONTAL)
        navbar_right_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add zoom slider and text
        navbar_left_sizer.Add(wx.StaticText(navbar, wx.ID_ANY, 'Zoom'),0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)

        #self._zoom_slider = wx.Slider(navbar, wx.ID_ANY, 10, self._glcanvas.zoom_min * 10,self._glcanvas.zoom_max * 10, size=(150, -1), style=wx.SL_HORIZONTAL)
        self._zoom_slider = wx.Slider(navbar, id=wx.ID_ANY, value=10, minValue=int(self._glcanvas.zoom_min * 10), maxValue=int(self._glcanvas.zoom_max * 10), size=(150, -1), style=wx.SL_HORIZONTAL)
        self._zoom_slider.Bind(wx.EVT_SCROLL, self.on_zoom_slider)
        navbar_left_sizer.Add(self._zoom_slider, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)

        grid_check = wx.CheckBox(navbar, label='Show &plane', name='grid')
        grid_check.Value = True
        axes_check = wx.CheckBox(navbar, label='Show &axes', name='axes')
        axes_check.Value = True
        bbox_check = wx.CheckBox(navbar, label='Show &boundaries', name='bbox')
        bbox_check.Value = True

        navbar_right_sizer.AddMany([
            (grid_check, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5),
            (axes_check, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5),
            (bbox_check, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 0)
        ])

        navbar.Bind(wx.EVT_CHECKBOX, self.on_checkbox)

        # add navbars
        navbar.Sizer.AddMany([
            (navbar_left_sizer, 2, wx.EXPAND),
            (navbar_right_sizer, 0, wx.EXPAND)
        ])
        self.Sizer.Add(navbar, 0, wx.EXPAND)

    def on_checkbox(self, event: wx.CommandEvent) -> None:
        """Toggles the appropriate chamber element."""
        name = event.EventObject.Name

        if name == 'grid':
            self.grid_shown = event.Int
        elif name == 'axes':
            self.axes_shown = event.Int
        else:
            self.bbox_shown = event.Int

    def set_perspective_projection(self, _: wx.CommandEvent) -> None:
        """Set to perspective projection."""
        self._glcanvas.orthographic = False
        self.dirty = True

    def set_orthographic_projection(self, _: wx.CommandEvent) -> None:
        """Set to orthographic projection."""
        self._glcanvas.orthographic = True
        self.dirty = True

    def on_zoom_slider(self, event: wx.ScrollEvent) -> None:
        """Update GLCanvas3D zoom when slider is updated."""
        self._glcanvas.zoom = event.Int / 10

    def set_zoom_slider(self, value: int) -> None:
        """Update slider value."""
        self._zoom_slider.Value = int(value * 10)

    # --------------------------------------------------------------------------
    # Accessor methods
    # --------------------------------------------------------------------------

    @property
    def grid_shown(self) -> bool:
        """Returns a flag indicating whether the chamber plane (floor/ceiling) is shown."""
        if self._glcanvas is None:
            return False

        return self._glcanvas.chamber.grid_shown

    @grid_shown.setter
    def grid_shown(self, value: bool) -> None:
        if self._glcanvas is None:
            return

        self._glcanvas.chamber.grid_shown = value

    @property
    def axes_shown(self) -> bool:
        """Returns a flag indicating whether the chamber axes are shown."""
        if self._glcanvas is None:
            return False

        return self._glcanvas.chamber.axes_shown

    @axes_shown.setter
    def axes_shown(self, value: bool) -> None:
        if self._glcanvas is None:
            return

        self._glcanvas.chamber.axes_shown = value

    @property
    def bbox_shown(self) -> bool:
        """Returns a flag indicating whether the chamber bounding box is shown."""
        if self._glcanvas is None:
            return False

        return self._glcanvas.chamber.bbox_shown

    @bbox_shown.setter
    def bbox_shown(self, value: bool) -> None:
        if self._glcanvas is None:
            return

        self._glcanvas.chamber.bbox_shown = value

    @property
    def dirty(self) -> bool:
        """Returns a flag indicating whether the GL canvas is dirty."""
        return self._glcanvas.dirty

    @dirty.setter
    def dirty(self, value: bool) -> None:
        self._glcanvas.dirty = value

    @property
    def glcanvas(self) -> GLCanvas3D:
        """Returns the GL canvas."""
        return self._glcanvas
