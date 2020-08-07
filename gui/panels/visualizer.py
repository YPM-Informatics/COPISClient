#!/usr/bin/env python3
"""Visualizer panel. Creates a Canvas3D OpenGL canvas."""

import random

import wx
from gl.canvas3d import Canvas3D
from gl.camera3d import Camera3D


class VisualizerPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, style=wx.BORDER_DEFAULT | wx.NO_FULL_REPAINT_ON_RESIZE)

        self.parent = parent
        self._selected_cam = None
        # self._build_dimensions = [400, 400, 400, 200, 200, 200]
        self._build_dimensions = [400, 400, 400, 200, 200, 200]

        self._glcanvas = Canvas3D(
            self,
            build_dimensions=self._build_dimensions,
            axes=True,
            bounding_box=True,
            every=100,
            subdivisions=10)

        self.zoom_slider = None

        self.init_panel()

    def init_panel(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # add bottom navigation bar
        navbar = wx.Panel(self, wx.ID_ANY, size=(-1, 35), style=wx.BORDER_RAISED)
        navbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # add zoom slider and text
        navbar_sizer.Add(wx.StaticText(navbar, wx.ID_ANY, 'Zoom', wx.DefaultPosition, wx.DefaultSize, 0), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        self.zoom_slider = wx.Slider(navbar, wx.ID_ANY, 10, self._glcanvas.zoom_min*10, self._glcanvas.zoom_max*10, size=(150, -1), style=wx.SL_HORIZONTAL)
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

        # add Canvas3D
        sizer.Add(self._glcanvas, 1, wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def on_zoom_slider(self, event):
        self._glcanvas.zoom = event.GetInt() / 10

    def set_zoom_slider(self, value):
        self.zoom_slider.SetValue(value * 10)

    def on_axes_check(self, event):
        if self._glcanvas is None:
            return

        self._glcanvas.bed.show_axes = event.IsChecked()

    def on_bbox_check(self, event):
        if self._glcanvas is None:
            return

        self._glcanvas.bed.show_bounding_box = event.IsChecked()

    @property
    def dirty(self):
        return self._glcanvas.dirty

    @dirty.setter
    def dirty(self, value):
        self._glcanvas.dirty = value

    @property
    def glcanvas(self):
        return self._glcanvas

    # ------------------
    # Camera3D functions
    # ------------------

    def on_clear_cameras(self):
        """Clear Camera3D list."""
        self._glcanvas.camera3d_list = []
        self._glcanvas.dirty = True

    def get_camera_objects(self):
        """Return Camera3D list."""
        return self.camera3d_list

    def add_camera(self, cam_id=-1):
        """Add new Camera3D."""
        x = random.random() * self._build_dimensions[0] - self._build_dimensions[3]
        y = random.random() * self._build_dimensions[1] - self._build_dimensions[4]
        z = random.random() * self._build_dimensions[2] - self._build_dimensions[5]
        b = random.randrange(0, 360, 5)
        c = random.randrange(0, 360, 5)

        if cam_id == -1:
            cam_id = self._generate_camera_id()

        cam_3d = Camera3D(cam_id, x, y, z, b, c)
        self._glcanvas.camera3d_list.append(cam_3d)
        self._glcanvas.dirty = True

        return str(cam_3d.cam_id)

    def get_camera_by_id(self, cam_id):
        """Return Camera3D by id."""
        if self._glcanvas.camera3d_list:
            for cam in self._glcanvas.camera3d_list:
                if cam.cam_id == cam_id:
                    return cam
        return None

    def _generate_camera_id(self):
        if self._glcanvas.camera3d_list:
            self._glcanvas.camera3d_list.sort(key=lambda x: x.cam_id)
            return self._glcanvas.camera3d_list[-1].cam_id + 1
        return 0

    def get_selected_camera(self):
        if self._selected_cam:
            return self._selected_cam
        return None

    def set_selected_camera(self, id):
        # reset previously selected camera
        last_selected = self.get_selected_camera()
        if last_selected:
            last_selected.is_selected = False

        # update new selected camera
        self._selected_cam = self.get_camera_by_id(id)
        self._selected_cam.is_selected = True

        # refresh glcanvas
        self._glcanvas.dirty = True
