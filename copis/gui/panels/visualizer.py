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

"""VisualizerPanel class."""

from gl.glcanvas import GLCanvas3D
from typing import List, Optional

import wx


class VisualizerPanel(wx.Panel):
    """Visualizer panel. Creates a GLCanvas3D OpenGL canvas.

    Args:
        parent: Pointer to a parent wx.Frame.

    Attributes:
        dirty: A boolean indicating if the OpenGL canvas needs updating or not.
        glcanvas: Read only; A GLCanvas3D object.
        bbox_shown: A boolean indicating if the canvas chamber bounding box is
            shown or not.
        axes_shown: A boolean indicating if the canvas axes is shown or not.
    """

    def __init__(self, parent, chamberdims, *args, **kwargs) -> None:
        """Inits VisualizerPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.parent = parent
        self.core = self.parent.core

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self._selected_cam = None
        self._build_dimensions = chamberdims
        self.zoom_slider = None

        self._glcanvas = GLCanvas3D(
            self,
            build_dimensions=self._build_dimensions,
            every=100,
            subdivisions=10)
        self.init_gui()

        self.Layout()

    def init_gui(self) -> None:
        """Initialize gui elements."""
        navbar = wx.Panel(self, wx.ID_ANY, size=(-1, 23), style=wx.BORDER_DEFAULT)
        navbar.Sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add zoom slider and text
        navbar.Sizer.Add(wx.StaticText(navbar, wx.ID_ANY, 'Zoom'), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        self.zoom_slider = wx.Slider(navbar, wx.ID_ANY, 10, self._glcanvas.zoom_min * 10,
            self._glcanvas.zoom_max * 10, size=(150, -1), style=wx.SL_HORIZONTAL)
        self.zoom_slider.Bind(wx.EVT_SCROLL, self.on_zoom_slider)
        navbar.Sizer.Add(self.zoom_slider, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)

        # add GLCanvas3D
        self.Sizer.Add(self._glcanvas, 1, wx.EXPAND|wx.ALL, 0)

        # add navbar
        self.Sizer.Add(navbar, 0, wx.EXPAND)

    def on_zoom_slider(self, event: wx.ScrollEvent) -> None:
        """Update GLCanvas3D zoom when slider is updated."""
        self._glcanvas.zoom = event.Int / 10

    def set_zoom_slider(self, value: float) -> None:
        """Update slider value."""
        self.zoom_slider.Value = value * 10

    # --------------------------------------------------------------------------
    # Accessor methods
    # --------------------------------------------------------------------------

    @property
    def grid_shown(self) -> bool:
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
        return self._glcanvas.dirty

    @dirty.setter
    def dirty(self, value: bool) -> None:
        self._glcanvas.dirty = value

    @property
    def glcanvas(self) -> GLCanvas3D:
        return self._glcanvas
