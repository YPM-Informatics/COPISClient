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
    """

    def __init__(self, parent, *args, **kwargs) -> None:
        """Initialize VisualizerPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT | wx.NO_FULL_REPAINT_ON_RESIZE)

        self.parent = parent
        self._selected_cam = None
        self._build_dimensions = [400, 400, 400, 200, 200, 200]

        self._glcanvas = GLCanvas3D(
            self,
            build_dimensions=self._build_dimensions,
            axes=True,
            bounding_box=True,
            every=100,
            subdivisions=10)

        self.zoom_slider = None

        self.init_panel()

    def init_panel(self) -> None:
        """Initialize panel."""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # add bottom navigation bar
        navbar = wx.Panel(self, wx.ID_ANY, size=(-1, 35), style=wx.BORDER_RAISED)
        navbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add zoom slider and text
        navbar_sizer.Add(wx.StaticText(navbar, wx.ID_ANY, 'Zoom'), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        self.zoom_slider = wx.Slider(navbar, wx.ID_ANY, 10, self._glcanvas.zoom_min * 10,
            self._glcanvas.zoom_max * 10, size=(150, -1), style=wx.SL_HORIZONTAL)
        self.zoom_slider.Bind(wx.EVT_SCROLL, self.on_zoom_slider)
        navbar_sizer.Add(self.zoom_slider, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        wx.StaticLine(navbar, wx.ID_ANY, style=wx.LI_VERTICAL)
        navbar_sizer.Add(wx.StaticLine(navbar, wx.ID_ANY, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        # add axes checkbox
        axes_check = wx.CheckBox(navbar, wx.ID_ANY, '&Axes')
        axes_check.SetValue(True)
        axes_check.Bind(wx.EVT_CHECKBOX, self.on_axes_check)
        navbar_sizer.Add(axes_check, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)

        # add bounding box checkbox
        bbox_check = wx.CheckBox(navbar, wx.ID_ANY, '&Bounding boxes')
        bbox_check.SetValue(True)
        bbox_check.Bind(wx.EVT_CHECKBOX, self.on_bbox_check)
        navbar_sizer.Add(bbox_check, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)

        navbar.SetSizerAndFit(navbar_sizer)
        sizer.Add(navbar, 0, wx.EXPAND)

        # add GLCanvas3D
        sizer.Add(self._glcanvas, 1, wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def on_zoom_slider(self, event: wx.ScrollEvent) -> None:
        """Update GLCanvas3D zoom when slider is updated."""
        self._glcanvas.zoom = event.GetInt() / 10

    def set_zoom_slider(self, value: float) -> None:
        """Update slider value."""
        self.zoom_slider.SetValue(value * 10)

    def on_axes_check(self, event: wx.CommandEvent) -> None:
        "Show or hide GLBed axes when checkbox is updated."
        if self._glcanvas is None:
            return

        self._glcanvas.bed.show_axes = event.IsChecked()

    def on_bbox_check(self, event: wx.CommandEvent) -> None:
        "Show or hide GLBed bounding box when checkbox is updated."
        if self._glcanvas is None:
            return

        self._glcanvas.bed.show_bounding_box = event.IsChecked()

    @property
    def dirty(self) -> bool:
        return self._glcanvas.dirty

    @dirty.setter
    def dirty(self, value: bool) -> None:
        self._glcanvas.dirty = value

    @property
    def glcanvas(self) -> GLCanvas3D:
        return self._glcanvas
