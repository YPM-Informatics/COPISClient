#!/usr/bin/env python3
"""Canvas3D class and associated classes."""

import math
import random
import numpy as np
import platform as pf

from threading import Lock

import wx
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *

from components.glhelper import arcball, axis_to_quat, quat_to_matrix4, mul_quat, draw_circle, draw_helix
from components.path3d import Path3D
from components.camera3d import Camera3D
from components.bed3d import Bed3D


class _Size():
    def __init__(self, width, height, scale_factor):
        self.__width = width
        self.__height = height
        self.__scale_factor = scale_factor

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, width):
        self.__width = width

    @property
    def height(self):
        return self.__height

    @height.setter
    def height(self, height):
        self.__height = height

    @property
    def scale_factor(self):
        return self.__scale_factor

    @scale_factor.setter
    def scale_factor(self, scale_factor):
        self.__scale_factor = scale_factor


class Canvas3D(glcanvas.GLCanvas):
    """Canvas3D class."""
    # True: use arcball controls, False: use orbit controls
    orbit_controls = True
    color_background = (0.941, 0.941, 0.941, 1)
    zoom_min = 0.1
    zoom_max = 7.0

    def __init__(self, parent, build_dimensions=None, axes=True, every=100, subdivisions=10):
        display_attrs = glcanvas.GLAttributes()
        display_attrs.MinRGBA(8, 8, 8, 8).DoubleBuffer().Depth(24).EndList()
        super().__init__(parent, display_attrs, -1)

        self._gl_initialized = False
        self._dirty = False # dirty flag to track when we need to re-render the canvas
        self._scale_factor = None
        self._mouse_pos = None
        self._width = None
        self._height = None
        if build_dimensions:
            self._build_dimensions = build_dimensions
        else:
            self._build_dimensions = [400, 400, 400, 200, 200, 200]
        self._dist = 0.5 * (self._build_dimensions[1] + max(self._build_dimensions[0], self._build_dimensions[2]))
        self._bed3d = Bed3D(self._build_dimensions, axes=axes, every=every, subdivisions=subdivisions)
        self._path3d = Path3D()

        self._camera3d_list = []
        self._path3d_list = []
        self._quadric = None
        self._zoom = 1
        self._rot_quat = [0.0, 0.0, 0.0, 1.0]
        self._rot_lock = Lock()
        self._angle_z = 0
        self._angle_x = 0

        self._main_frame = parent.parent

        # initialize opengl context
        self._context = glcanvas.GLContext(self)

        # bind events
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_IDLE, self.on_idle)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key)
        self.Bind(wx.EVT_KEY_UP, self.on_key)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)

    def init_opengl(self):
        """Initialize OpenGL."""
        if self._gl_initialized:
            return True

        if self._context is None:
            return False

        self._quadric = gluNewQuadric()

        glClearColor(*self.color_background)
        glClearDepth(1.0)

        glDepthFunc(GL_LESS)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # set antialiasing
        glEnable(GL_LINE_SMOOTH)

        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_MULTISAMPLE)

        if not self._bed3d.init():
            return

        self._gl_initialized = True
        return True

    def render(self):
        """Render frame."""
        # ensure that canvas is current and initialized
        if not self._is_shown_on_screen() or not self._set_current():
            return

        # ensure that opengl is initialized
        if not self.init_opengl():
            return

        canvas_size = self.get_canvas_size()
        glViewport(0, 0, canvas_size.width, canvas_size.height)
        self._width = max(10, canvas_size.width)
        self._height = max(10, canvas_size.height)

        self.apply_view_matrix()
        self.apply_projection()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self._render_background()

        self._render_platform()
        self._render_objects()
        self._render_cameras()
        self._render_paths()

        self.SwapBuffers()

    # ---------------------
    # Canvas event handlers
    # ---------------------

    def on_size(self, event):
        """Handle EVT_SIZE."""
        self._dirty = True

    def on_idle(self, event):
        """Handle EVT_IDLE."""
        if not self._gl_initialized or self.IsFrozen():
            return

        self._dirty = self._dirty or any((i.dirty for i in self._camera3d_list))

        self._refresh_if_shown_on_screen()
        self._dirty = False
        for camera in self._camera3d_list:
            camera.dirty = False

    def on_key(self, event):
        """Handle EVT_KEY_DOWN and EVT_KEY_UP."""
        pass

    def on_mouse_wheel(self, event):
        """Handle mouse wheel event and adjust zoom."""
        if not self._gl_initialized or event.MiddleIsDown():
            return

        scale = self.get_scale_factor()
        event.SetX(int(event.GetX() * scale))
        event.SetY(int(event.GetY() * scale))

        self._update_camera_zoom(event.GetWheelRotation() / event.GetWheelDelta())

    def on_mouse(self, event):
        """Handle mouse events.
            LMB drag:   move viewport
            RMB drag:   unused
            LMB/RMB up: reset position
        """
        if not self._gl_initialized or not self._set_current():
            return

        scale = self.get_scale_factor()
        event.SetX(int(event.GetX() * scale))
        event.SetY(int(event.GetY() * scale))

        if event.Dragging():
            if event.LeftIsDown():
                self.rotate_camera(event, orbit=self.orbit_controls)
            elif event.RightIsDown() or event.MiddleIsDown():
                self.translate_camera(event)
        elif event.LeftUp() or event.MiddleUp() or event.RightUp() or event.Leaving():
            if self._mouse_pos is not None:
                self._mouse_pos = None
        elif event.Moving():
            pass
        else:
            event.Skip()
        self._dirty = True

    def on_left_dclick(self, event):
        """Handle EVT_LEFT_DCLICK."""
        # Detect click location
        scale = self.get_scale_factor()
        event.SetX(int(event.GetX() * scale))
        event.SetY(int(event.GetY() * scale))
        glFlush()

        # Read pixel color
        pixel = glReadPixels(event.GetX(), self._height - event.GetY(), 1, 1, GL_RGB, GL_UNSIGNED_BYTE)
        camid = 125 - pixel[0]

        # If user double clicks something other than camera
        if camid > len(self._camera3d_list) or camid < 0:
            return 0

        self._main_frame.set_selected_camera(camid)

    def on_erase_background(self, event):
        """Handle the erase background event."""
        pass  # Do nothing, to avoid flashing on MSW.

    def on_paint(self, event):
        """Handle EVT_PAINT."""
        if self._gl_initialized:
            self._dirty = True
        else:
            self.render()

    def on_set_focus(self, event):
        """Handle EVT_SET_FOCUS."""
        self._refresh_if_shown_on_screen()

    def get_canvas_size(self):
        """Get canvas size based on scaling factor."""
        w, h = self.GetSize()
        factor = self.get_scale_factor()
        w = int(w * factor)
        h = int(h * factor)
        return _Size(w, h, factor)

    # ---------------------
    # Canvas util functions
    # ---------------------

    def destroy(self):
        """Clean up the OpenGL context."""
        self._context.destroy()
        glcanvas.GLCanvas.Destroy()

    def set_dirty(self):
        """Set dirty flag true."""
        self._dirty = True

    def _is_shown_on_screen(self):
        return self.IsShownOnScreen()

    def _set_current(self):
        return False if self._context is None else self.SetCurrent(self._context)

    def _update_camera_zoom(self, delta_zoom):
        zoom = self._zoom / (1.0 - max(min(delta_zoom, 4.0), -4.0) * 0.1)
        self._zoom = max(min(zoom, self.zoom_max), self.zoom_min)
        self._dirty = True

    def _refresh_if_shown_on_screen(self):
        if self._is_shown_on_screen():
            self._set_current()
            self.render()

    def _render_background(self):
        glClearColor(*self.color_background)

    def _render_platform(self):
        if self._bed3d is None:
            return

        self._bed3d.render()

    def _render_objects(self):
        return

    def _render_cameras(self):
        if not self._camera3d_list:
            return
        for cam in self._camera3d_list:
            cam.render()

    def _render_paths(self):
        if not self._path3d_list:
            return

    # ------------------
    # Camera3D functions
    # ------------------

    # TODO: move camera logic (and all methods that aren't graphics based)
    # out of Canvas3D

    def on_clear_cameras(self):
        """Clear Camera3D list."""
        self._camera3d_list = []
        self._dirty = True

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
        self._camera3d_list.append(cam_3d)
        self._dirty = True

        return str(cam_3d.camid)

    def get_camera_by_id(self, camid):
        """Return Camera3D by id."""
        if self._camera3d_list:
            for cam in self._camera3d_list:
                if cam.camid == camid:
                    return cam
        return None

    def _generate_camera_id(self):
        if self._camera3d_list:
            self._camera3d_list.sort(key=lambda x: x.camid)
            return self._camera3d_list[-1].camid + 1
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

        # refresh canvas
        self.set_dirty

    # ----------------
    # Path3D functions
    # ----------------


    # -----------------------
    # Canvas camera functions
    # -----------------------

    def apply_view_matrix(self):
        """Apply modelview matrix according to rotation quat."""
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            0.0, 0.0, self._dist * 1.5, # eyeX, eyeY, eyeZ
            0.0, 0.0, 0.0,              # centerX, centerY, centerZ
            0.0, 1.0, 0.0)              # upX, upY, upZ
        glMultMatrixd(quat_to_matrix4(self._rot_quat))

    def apply_projection(self):
        """Set camera projection. Also updates zoom."""
        # TODO: add toggle between perspective and orthographic view modes
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(
            np.arctan(np.tan(np.deg2rad(45.0)) / self._zoom) * 180 / math.pi,
            float(self._width) / self._height,
            0.1,
            2000.0)
        glMatrixMode(GL_MODELVIEW)

    def get_modelview_matrix(self):
        """Return GL_MODELVIEW_MATRIX."""
        mat = (GLdouble * 16)()
        glGetDoublev(GL_MODELVIEW_MATRIX, mat)
        return mat

    def get_projection_matrix(self):
        """Return GL_PROJECTION_MATRIX."""
        mat = (GLdouble * 16)()
        glGetDoublev(GL_PROJECTION_MATRIX, mat)
        return mat

    def get_viewport(self):
        """Return GL_VIEWPORT."""
        vec = (GLint * 4)()
        glGetIntegerv(GL_VIEWPORT, vec)
        return vec

    def rotate_camera(self, event, orbit=True):
        """Update _rot_quat based on mouse position.
            orbit = True:   Use orbit method to rotate.
            orbit = False:  Use arcball method to rotate.
        """
        if self._mouse_pos is None:
            self._mouse_pos = event.GetPosition()
            return
        last = self._mouse_pos
        cur = event.GetPosition()

        p1x = last.x * 2.0 / self._width - 1.0
        p1y = 1 - last.y * 2.0 / self._height
        p2x = cur.x * 2.0 / self._width - 1.0
        p2y = 1 - cur.y * 2.0 / self._height

        if p1x == p2x and p1y == p2y:
            self._rot_quat = [0.0, 0.0, 0.0, 1.0]

        with self._rot_lock:
            if orbit:
                delta_x = p2y - p1y
                self._angle_x += delta_x
                rot_x = axis_to_quat([1.0, 0.0, 0.0], self._angle_x)

                delta_z = p2x - p1x
                self._angle_z -= delta_z
                rot_z = axis_to_quat([0.0, 1.0, 0.0], self._angle_z)

                self._rot_quat = mul_quat(rot_z, rot_x)
            else:
                quat = arcball(p1x, p1y, p2x, p2y, self._dist / 250.0)
                self._rot_quat = mul_quat(self._rot_quat, quat)
        self._mouse_pos = cur

    def translate_camera(self, event):
        if self._mouse_pos is None:
            self._mouse_pos = event.GetPosition()
            return
        last = self._mouse_pos
        cur = event.GetPosition()
        # Do stuff
        self._mouse_pos = cur

    # -------------------
    # Misc util functions
    # -------------------

    def get_scale_factor(self):
        if self._scale_factor is None:
            if pf.system() == 'Darwin': # MacOS
                self._scale_factor = 2.0
            else:
                self._scale_factor = 1.0
        return self._scale_factor
