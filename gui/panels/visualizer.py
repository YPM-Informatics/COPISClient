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
        self._build_dimensions = [4, 4, 4, 2, 2, 2]

        self.glcanvas = Canvas3D(
            self,
            build_dimensions=self._build_dimensions,
            axes=True,
            every=100,
            subdivisions=10)
        self.init_panel()

    def init_panel(self):
        sizer = wx.BoxSizer(orient=wx.VERTICAL)

        # add Canvas3D
        sizer.Add(self.glcanvas, 1, wx.EXPAND)

        # add bottom navigation bar
        navbar = wx.Panel(self, wx.ID_ANY, size=(-1, 32), style=wx.BORDER_RAISED)
        navbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        zoom = wx.StaticText(navbar, wx.ID_ANY, 'Zoom level', wx.DefaultPosition, wx.DefaultSize, 0)
        navbar_sizer.Add(zoom, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        zoom_slider = wx.Slider(navbar, wx.ID_ANY, 50, 0, 100, style=wx.SL_HORIZONTAL)
        navbar_sizer.Add(zoom_slider, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        wx.StaticLine(navbar, wx.ID_ANY, style=wx.LI_VERTICAL)
        navbar_sizer.Add(wx.StaticLine(navbar, wx.ID_ANY, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        axes_check = wx.CheckBox(navbar, wx.ID_ANY, 'Show &axes')
        axes_check.SetValue(True)
        axes_check.Bind(wx.EVT_CHECKBOX, self.on_axes_check)
        navbar_sizer.Add(axes_check, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)

        bbox_check = wx.CheckBox(navbar, wx.ID_ANY, 'Show &bounding boxes')
        bbox_check.SetValue(True)
        bbox_check.Bind(wx.EVT_CHECKBOX, self.on_bbox_check)
        navbar_sizer.Add(bbox_check, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)

        navbar.SetSizerAndFit(navbar_sizer)
        sizer.Add(navbar, 0, wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def on_axes_check(self, event):
        if self.glcanvas is None:
            return

        self.glcanvas.bed3d.show_axes = event.IsChecked()

    def on_bbox_check(self, event):
        if self.glcanvas is None:
            return

        self.glcanvas.bed3d.show_bounding_box = event.IsChecked()

    def set_dirty(self):
        self.glcanvas.set_dirty()

    # ------------------
    # Camera3D functions
    # ------------------

    def on_clear_cameras(self):
        """Clear Camera3D list."""
        self.glcanvas._camera3d_list = []
        self.glcanvas.set_dirty()

    def get_camera_objects(self):
        """Return Camera3D list."""
        return self._camera3d_list

    def add_camera(self, camid=-1):
        """Add new Camera3D."""
        x = random.random() * self._build_dimensions[0] - self._build_dimensions[3]
        y = random.random() * self._build_dimensions[1] - self._build_dimensions[4]
        z = random.random() * self._build_dimensions[2] - self._build_dimensions[5]
        b = random.randrange(0, 360, 5)
        c = random.randrange(0, 360, 5)

        if camid == -1:
            camid = self._generate_camera_id()

        cam_3d = Camera3D(camid, x, y, z, b, c)
        self.glcanvas._camera3d_list.append(cam_3d)
        self.glcanvas.set_dirty()

        return str(cam_3d.camid)

    def get_camera_by_id(self, camid):
        """Return Camera3D by id."""
        if self.glcanvas._camera3d_list:
            for cam in self.glcanvas._camera3d_list:
                if cam.camid == camid:
                    return cam
        return None

    def _generate_camera_id(self):
        if self.glcanvas._camera3d_list:
            self.glcanvas._camera3d_list.sort(key=lambda x: x.camid)
            return self.glcanvas._camera3d_list[-1].camid + 1
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
        self.glcanvas.set_dirty()
