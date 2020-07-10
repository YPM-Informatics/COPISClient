#!/usr/bin/env python3
"""Canvas3D class."""

import math
import random
import numpy as np
from threading import Lock

import wx
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *

from components.glhelper import arcball, vector_to_quat, quat_to_matrix4, mul_quat, draw_circle, draw_helix
from components.path3d import Path3D
from components.camera3d import Camera3D

class Canvas3D(glcanvas.GLCanvas):

    class Size():
        def __init__(self, width, height, scale_factor):
            self.__width = width
            self.__height = height
            self.__scale_factor = scale_factor

        @property
        def width(self):
            return self.__width

        @property
        def height(self):
            return self.__height

        @property
        def scale_factor(self):
            return self.__scale_factor

        @width.setter
        def width(self, width):
            self.__width = width

        @height.setter
        def height(self, height):
            self.__height = height

        @scale_factor.setter
        def scale_factor(self, scale_factor):
            self.__scale_factor = scale_factor

    zoom_min = 0.5
    zoom_max = 5.0
    clip_near = 3.0
    clip_far = 7.0

    # True: use arcball controls, False: use orbit controls
    arcball_control = True
    color_background = (0.941, 0.941, 0.941, 1)

    def __init__(self, parent):
        display_attrs = glcanvas.GLAttributes()
        display_attrs.MinRGBA(8, 8, 8, 8).DoubleBuffer().Depth(24).EndList()
        super().__init__(parent, display_attrs, -1)

        self._gl_initialized = False
        self._dirty = False # dirty flag to track when we need to re-render the canvas
        self._zoom = 1
        self._width = None
        self._height = None
        self._rot_quat = [1, 0, 0, 0]
        self._rot_lock = Lock()
        self._angle_z = 0
        self._angle_x = 0
        self._mouse_pos = None

        self._camera3d_list = []
        self._path3d_list = []

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

        self.quadratic = gluNewQuadric()

        glClearColor(*self.color_background)
        glClearDepth(1.0)

        glDepthFunc(GL_LEQUAL)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)

        # set antialiasing
        glEnable(GL_LINE_SMOOTH)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_MULTISAMPLE)

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

        size = self.GetClientSize()
        canvas_size = self.get_canvas_size()
        glViewport(0, 0, canvas_size.width, canvas_size.height)
        self._width = max(10, canvas_size.width)
        self._height = max(10, canvas_size.height)

        self.apply_view_matrix()
        self.apply_projection()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self._render_background()
        self._render_grid()
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

        for camera in self._camera3d_list:
            self._dirty = self._dirty or camera._dirty

        if not self._dirty:
            return

        self._refresh_if_shown_on_screen()
        self._dirty = False
        for camera in self._camera3d_list:
            camera._dirty = False

    def on_key(self, event):
        """Handle EVT_KEY_DOWN and EVT_KEY_UP."""
        pass

    def on_mouse_wheel(self, event):
        """Handle mouse wheel event and adjust zoom."""
        if not self._gl_initialized or event.MiddleIsDown():
            return

        self._update_camera_zoom(event.GetWheelRotation() / event.GetWheelDelta())

    def on_mouse(self, event):
        """Handle mouse events.
            LMB drag:   move viewport
            RMB drag:   unused
            LMB/RMB up: reset position
        """
        if not self._gl_initialized or not self._set_current():
            return

        if event.Dragging():
            if event.LeftIsDown():
                self.rotate_camera(event, use_arcball=self.arcball_control)
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
        mouse_pos = event.GetPosition()
        point = self._mouse_to_3d(*mouse_pos)
        print(point)
        pass

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
        factor = 2.0
        # insert retina/high dpi scaling adjustment here
        w = int(w * factor)
        h = int(h * factor)
        return self.Size(w, h, factor)

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

    def _render_grid(self):
        glColor3ub(200, 200, 200)
        glBegin(GL_LINES)
        for i in np.arange(-10, 11, 1):
            i *= 0.1
            glVertex3f(i, 1, 0)
            glVertex3f(i, -1, 0)
            glVertex3f(1, i, 0)
            glVertex3f(-1, i, 0)

        glColor3ub(255, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(math.sqrt(2), 0, 0)
        glColor3ub(0, 255, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, math.sqrt(2), 0)
        glColor3ub(0, 0, 255)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, math.sqrt(2))
        glEnd()

    def _render_objects(self):
        # draw hemispheres
        glColor3ub(225, 225, 225)
        draw_circle([0, 0, 0], [1, 1, 0], math.sqrt(2), 128)
        draw_circle([0, 0, 0], [1, -1, 0], math.sqrt(2), 128)
        for i in np.arange(0, 180, 45):
            draw_circle([0, 0, math.sqrt(2) * math.cos(np.deg2rad(i))], [0, 0, 1], math.sqrt(2) * math.sin(np.deg2rad(i)), 128)

        # draw axes circles
        glColor3ub(160, 160, 160)
        draw_circle([0, 0, 0], [0, 0, 1], math.sqrt(2), 128)
        draw_circle([0, 0, 0], [0, 1, 0], math.sqrt(2), 128)
        draw_circle([0, 0, 0], [1, 0, 0], math.sqrt(2), 128)

        # draw sphere
        glColor3ub(0, 0, 128)
        gluSphere(self.quadratic, 0.25, 32, 32)

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

    def on_clear_cameras(self):
        """Clear Camera3D list."""
        self._camera3d_list = []
        self._dirty = True

    def get_camera_objects(self):
        """Return Camera3D list."""
        return self._camera3d_list

    def add_camera(self, id=-1):
        """Add new Camera3D."""
        x = float(random.randrange(-100, 100)) / 100
        y = float(random.randrange(-100, 100)) / 100
        z = float(random.randrange(-100, 100)) / 100
        b = random.randrange(0, 360, 5)
        c = random.randrange(0, 360, 5)

        if id == -1:
            id = self._generate_camera_id()

        cam_3d = Camera3D(id, x, y, z, b, c)
        self._camera3d_list.append(cam_3d)
        self._dirty = True

        return str(cam_3d._id)

    def get_camera_by_id(self, id):
        """Return Camera3D by id."""
        if self._camera3d_list:
            for cam in self._camera3d_list:
                if cam._id == id:
                    return cam
        return None

    def _generate_camera_id(self):
        if self._camera3d_list:
            self._camera3d_list.sort(key=lambda x: x._id)
            return self._camera3d_list[-1]._id + 1
        return 0

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
        gluLookAt(0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        glMultMatrixd(quat_to_matrix4(self._rot_quat))

    def apply_projection(self):
        """Set camera projection. Also updates zoom."""
        # TODO: add toggle between perspective and orthographic view modes
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(np.arctan(np.tan(np.deg2rad(50.0)) / self._zoom) * 180 / np.pi, float(self._width) / self._height, self.clip_near, self.clip_far)
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

    def rotate_camera(self, event, use_arcball=True):
        """Update _rot_quat based on mouse position.
            use_arcball = True:     Use arcball_rotation to rotate canvas.
            use_arcball = False:    Use orbit_rotation to rotate canvas.
        """
        if self._mouse_pos is None:
            self._mouse_pos = event.GetPosition()
            return
        last = self._mouse_pos
        cur = event.GetPosition()

        p1x = float(last.x) * 2.0 / self._width - 1.0
        p1y = 1 - float(last.y) * 2.0 / self._height
        p2x = float(cur.x) * 2.0 / self._width - 1.0
        p2y = 1 - float(cur.y) * 2.0 / self._height

        if p1x == p2x and p1y == p2y:
            return [1.0, 0.0, 0.0, 0.0]

        with self._rot_lock:
            if use_arcball:
                quat = arcball(p1x, p1y, p2x, p2y, math.sqrt(2)/2)
                self._rot_quat = mul_quat(self._rot_quat, quat)
            else:
                delta_z = p2x - p1x
                self._angle_z -= delta_z
                rot_z = vector_to_quat([0.0, 0.0, 1.0], self._angle_z)

                delta_x = p2y - p1y
                self._angle_x += delta_x
                rot_x = vector_to_quat([1.0, 0.0, 0.0], self._angle_x)
                self._rot_quat = mul_quat(rot_z, rot_x)
        self._mouse_pos = cur

    def translate_camera(self, event):
        if self._mouse_pos is None:
            self._mouse_pos = event.GetPosition()
            return
        last = self._mouse_pos
        cur = event.GetPosition()
        # Do stuff
        self._mouse_pos = cur

    def _mouse_to_3d(self, x, y, z=1.0, local_transform=False):
        x = float(x)
        y = self._height - float(y)
        pmat = self.get_projection_matrix()
        mvmat = self.get_modelview_matrix()
        viewport = self.get_viewport()
        point = gluUnProject(x, y, z, mvmat, pmat, viewport)
        return point

    def _mouse_to_ray(self, x, y, local_transform=False):
        x = float(x)
        y = self._height - float(y)
        pmat = self.get_projection_matrix()
        mvmat = self.get_modelview_matrix()
        viewport = self.get_viewport()
        px = (GLdouble)()
        py = (GLdouble)()
        pz = (GLdouble)()
        ray_far = gluUnProject(x, y, 1, mvmat, pmat, viewport)
        ray_near = gluUnProject(x, y, 0., mvmat, pmat, viewport)
        return ray_near, ray_far

    def _mouse_to_plane(self, x, y, plane_normal, plane_offset, local_transform=False):
        ray_near, ray_far = self.mouse_to_ray(x, y, local_transform)
        ray_near = np.array(ray_near)
        ray_far = np.array(ray_far)
        ray_dir = ray_far - ray_near
        ray_dir = ray_dir / np.linalg.norm(ray_dir)
        plane_normal = np.array(plane_normal)
        q = ray_dir.dot(plane_normal)
        if q == 0:
            return None
        t = - (ray_near.dot(plane_normal) + plane_offset) / q
        if t < 0:
            return None
        return ray_near + t * ray_dir
