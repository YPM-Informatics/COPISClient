#!/usr/bin/env python3
"""Canvas3D and associated classes."""

import math
import random
import numpy as np
import platform as pf
import ctypes

from typing import NamedTuple
from threading import Lock

import glm
import wx
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GLU import *

from gl.glhelper import arcball
from gl.path3d import Path3D
from gl.camera3d import Camera3D
from gl.proxy3d import Proxy3D
from gl.viewcube import GLViewCube
from gl.bed import GLBed

from enums import ViewCubePos, ViewCubeSize
from utils import timing


class _Size(NamedTuple):
    width: int
    height: int
    scale_factor: float

    def aspect_ratio(self):
        return self.width / self.height


class Canvas3D(glcanvas.GLCanvas):
    """Canvas3D class."""
    # True: use arcball controls, False: use orbit controls
    orbit_controls = True
    color_background = (0.941, 0.941, 0.941, 1)
    zoom_min = 0.1
    zoom_max = 7.0

    def __init__(self, parent, build_dimensions=None, axes=True, bounding_box=True, every=100, subdivisions=10):
        self.parent = parent
        display_attrs = glcanvas.GLAttributes()
        display_attrs.MinRGBA(8, 8, 8, 8).DoubleBuffer().Depth(24).EndList()
        super().__init__(self.parent, display_attrs, id=wx.ID_ANY, pos=wx.DefaultPosition,
                         size=wx.DefaultSize, style=0, name='GLCanvas', palette=wx.NullPalette)
        self._canvas = self
        self._context = glcanvas.GLContext(self._canvas)
        self._shader_program = None

        if build_dimensions:
            self._build_dimensions = build_dimensions
        else:
            self._build_dimensions = [400, 400, 400, 200, 200, 200]
        self._dist = 0.5 * (self._build_dimensions[1] + max(self._build_dimensions[0], self._build_dimensions[2]))

        self._bed = GLBed(self, self._build_dimensions, axes, bounding_box, every, subdivisions)
        self._viewcube = GLViewCube(self)
        self._proxy3d = None # Proxy3D('Sphere', [1], (0, 53, 107))
        # self._path3d = Path3D()
        # self._path3d_list = []
        self._camera3d_list = []
        self._camera3d_scale = 10

        # screen is only refreshed from the OnIdle handler if it is dirty
        self._dirty = False
        self._gl_initialized = False
        self._scale_factor = None
        self._mouse_pos = None

        self._zoom = 1
        self._rot_quat = glm.quat()
        self._rot_lock = Lock()
        self._angle_z = 0
        self._angle_x = 0
        self._inside = False
        self._hover_id = -1

        # bind events
        self._canvas.Bind(wx.EVT_SIZE, self.on_size)
        self._canvas.Bind(wx.EVT_IDLE, self.on_idle)
        self._canvas.Bind(wx.EVT_KEY_DOWN, self.on_key)
        self._canvas.Bind(wx.EVT_KEY_UP, self.on_key)
        self._canvas.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self._canvas.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)
        self._canvas.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick)
        self._canvas.Bind(wx.EVT_ENTER_WINDOW, self.on_enter_window)
        self._canvas.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window)
        self._canvas.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)
        self._canvas.Bind(wx.EVT_PAINT, self.on_paint)
        self._canvas.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)

    def init_opengl(self):
        """Initialize OpenGL."""
        if self._gl_initialized:
            return True

        if self._context is None:
            return False

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
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        self.init_shaders()

        self._gl_initialized = True
        return True

    def init_shaders(self):
        vertex = """
        #version 450 core

        layout (location = 0) in vec3 positions;
        layout (location = 1) in vec3 colors;

        layout (location = 0) uniform mat4 projection;
        layout (location = 1) uniform mat4 modelview;

        out vec3 newColor;

        void main() {
            gl_Position = projection * modelview * vec4(positions, 1.0);
            newColor = colors;
        }
        """

        fragment = """
        #version 450 core

        in vec3 newColor;
        out vec4 outColor;

        void main() {
            outColor = vec4(newColor, 1.0);
        }
        """

        vertex_shader = shaders.compileShader(vertex, GL_VERTEX_SHADER)
        fragment_shader = shaders.compileShader(fragment, GL_FRAGMENT_SHADER)
        self._shader_program = shaders.compileProgram(vertex_shader, fragment_shader)

    @timing
    def render(self):
        """Render frame."""
        # ensure that canvas is current and initialized
        if not self._is_shown_on_screen() or not self._set_current():
            return

        # ensure that opengl is initialized
        if not self.init_opengl():
            return

        canvas_size = self._canvas.get_canvas_size()
        glViewport(0, 0, canvas_size.width, canvas_size.height)

        self.apply_view_matrix()
        self.apply_projection()

        self._picking_pass()
        # self._hover_id = self._picking_pass()
        # print(self._hover_id)
        glViewport(0, 0, canvas_size.width, canvas_size.height)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self._render_background()
        self._render_bed()
        # self._render_objects()
        self._render_viewcube()

        self._canvas.SwapBuffers()

    # ---------------------
    # Canvas event handlers
    # ---------------------

    def on_size(self, event):
        """Handle EVT_SIZE."""
        self._dirty = True

    def on_idle(self, event):
        """Handle EVT_IDLE."""
        if not self._gl_initialized or self._canvas.IsFrozen():
            return

        self._dirty = self._dirty or any((i.dirty for i in self._camera3d_list))

        self._refresh_if_shown_on_screen()

        for camera in self._camera3d_list:
            camera.dirty = False
        self._dirty = False

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
            pass
            # if self._mouse_pos is not None:
            #     self._mouse_pos = None
        elif event.Moving():
            self._mouse_pos = event.GetPosition()
        else:
            event.Skip()
        self._dirty = True

    def on_left_dclick(self, event):
        """Handle EVT_LEFT_DCLICK."""

        # get current hovered id
        cam_id = self._hover_id

        # check if id is out of bounds
        if cam_id == -1 or cam_id >= len(self._camera3d_list):
            return

        wx.GetApp().mainframe.set_selected_camera(cam_id)

    def on_enter_window(self, event):
        self._inside = True

    def on_leave_window(self, event):
        self._inside = False

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
        w, h = self._canvas.GetSize()
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

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    def _is_shown_on_screen(self):
        return self._canvas.IsShownOnScreen()

    def _set_current(self):
        return False if self._context is None else self._canvas.SetCurrent(self._context)

    def _update_camera_zoom(self, delta_zoom):
        zoom = self._zoom / (1.0 - max(min(delta_zoom, 4.0), -4.0) * 0.1)
        self._zoom = max(min(zoom, self.zoom_max), self.zoom_min)
        self._dirty = True
        self._update_parent_zoom_slider()

    def _refresh_if_shown_on_screen(self):
        if self._is_shown_on_screen():
            self._set_current()
            self.render()

    def _picking_pass(self):
        glDisable(GL_MULTISAMPLE)

        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self._render_objects_for_picking()

        glEnable(GL_MULTISAMPLE)

        id_ = -1

        canvas_size = self._canvas.get_canvas_size()
        mouse = self._mouse_pos
        if self._inside:
            # rgb to id
            color = glReadPixels(mouse[0], canvas_size.height - mouse[1] -1, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)
            id_ = color[0] + (color[1] << 8) + (color[2] << 16)

        if id_ == 15790320: # 15790320 is from the background color
            id_ = -1



        self._viewcube.picked_side = id_

    def _render_background(self):
        glClearColor(*self.color_background)

    def _render_bed(self):
        if self._bed is not None:
            self._bed.render()

    def _render_objects(self):
        if self._proxy3d is not None:
            self._proxy3d.render()

        if not self._camera3d_list:
            return
        for cam in self._camera3d_list:
            cam.render()

    def _render_viewcube(self):
        if self._viewcube is not None:
            self._viewcube.render()

    def _render_objects_for_picking(self):
        self._viewcube.render_for_picking()
        return

        glDisable(GL_CULL_FACE)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)

        self._viewcube.render_for_picking()
        view_matrix = self.get_modelview_matrix()

        # encode id in color value
        for cam in self._camera3d_list:
            id_ = cam.cam_id
            r = (id_ & (0x0000000FF << 0)) >> 0
            g = (id_ & (0x0000000FF << 8)) >> 8
            b = (id_ & (0x0000000FF << 16)) >> 16
            a = 1.0
            # glColor4f(r / 255.0, g / 255.0, b / 255.0, a)
            # cam.render_for_picking()

        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glEnable(GL_CULL_FACE)

    # ------------------
    # Accessor functions
    # ------------------

    def _update_parent_zoom_slider(self):
        self.parent.set_zoom_slider(self._zoom)

    @property
    def default_shader_program(self):
        return self._shader_program

    @property
    def rot_quat(self):
        return self._rot_quat

    @property
    def bed(self):
        return self._bed

    @property
    def proxy3d(self):
        return self._proxy3d

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        self._zoom = value
        self._dirty = True

    @property
    def build_dimensions(self):
        return self._build_dimensions

    @build_dimensions.setter
    def build_dimensions(self, value):
        self._build_dimensions = value
        self._bed.build_dimensions = value
        self._dirty = True

    @property
    def camera3d_scale(self):
        return self._camera3d_scale

    @camera3d_scale.setter
    def camera3d_scale(self, value):
        for camera in self._camera3d_list:
            camera.scale = value
            camera.dirty = True

    @property
    def camera3d_list(self):
        return self._camera3d_list

    @camera3d_list.setter
    def camera3d_list(self, value):
        self._camera3d_list = value
        self._dirty = True

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

        glMultMatrixd(np.array(glm.mat4_cast(self._rot_quat)))

    def apply_projection(self):
        """Set camera projection. Also updates zoom."""
        # TODO: add toggle between perspective and orthographic view modes
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(
            math.atan(math.tan(math.radians(45.0)) / self._zoom) * 180 / math.pi,
            self._canvas.get_canvas_size().aspect_ratio(),
            0.1,
            2000.0)
        glMatrixMode(GL_MODELVIEW)

    def get_projection_matrix(self):
        """Return GL_PROJECTION_MATRIX."""
        mat = (GLdouble * 16)()
        glGetDoublev(GL_PROJECTION_MATRIX, mat)
        return mat

    def get_modelview_matrix(self):
        """Return GL_MODELVIEW_MATRIX."""
        mat = (GLdouble * 16)()
        glGetDoublev(GL_MODELVIEW_MATRIX, mat)
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

        canvas_size = self._canvas.get_canvas_size()
        p1x = last.x * 2.0 / canvas_size.width - 1.0
        p1y = 1 - last.y * 2.0 / canvas_size.height
        p2x = cur.x * 2.0 / canvas_size.width - 1.0
        p2y = 1 - cur.y * 2.0 / canvas_size.height

        if p1x == p2x and p1y == p2y:
            self._rot_quat = glm.quat()

        with self._rot_lock:
            if orbit:
                delta_x = p2y - p1y
                self._angle_x -= delta_x
                rot_x = glm.angleAxis(self._angle_x, glm.vec3(1.0, 0.0, 0.0))

                delta_z = p2x - p1x
                self._angle_z += delta_z
                rot_z = glm.angleAxis(self._angle_z, glm.vec3(0.0, 1.0, 0.0))

                self._rot_quat = rot_x * rot_z
            else:
                quat = arcball(p1x, p1y, p2x, p2y, self._dist / 250.0)
                self._rot_quat = quat * self._rot_quat
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
