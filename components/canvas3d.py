#!/usr/bin/env python3
"""TODO: Fill in docstring"""

import math
import numpy as np
from threading import Lock

import wx
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *

from components.glhelper import arcball, vector_to_quat, quat_to_matrix4, mul_quat, draw_circle, draw_helix


class Canvas3D(glcanvas.GLCanvas):
    zoom_min = 0.5
    zoom_max = 5.0
    clip_near = 3.0
    clip_far = 7.0
    # True: use arcball controls, False: use orbit controls
    arcball_control = True
    color_background = (0.941, 0.941, 0.941, 1)

    def __init__(self, parent, *args, **kwargs):
        super(Canvas3D, self).__init__(parent, -1)
        self._initialized = False
        self._dirty = False
        self._zoom = 1
        self._width = None
        self._height = None
        self._rot_quat = [1, 0, 0, 0]
        self._rot_lock = Lock()
        self._angle_z = 0
        self._angle_x = 0
        self._mouse_pos = None
        self.camera_objects = []

        # these attributes cannot be set for the time being
        display_attrs = glcanvas.GLAttributes()
        display_attrs.PlatformDefaults().MinRGBA(8, 8, 8, 8).DoubleBuffer().Depth(32).EndList()
        context_attrs = glcanvas.GLContextAttrs()
        context_attrs.CoreProfile().OGLVersion(4, 5).Robust().ResetIsolation().EndList()

        # initialize canvas and context
        self.canvas = glcanvas.GLCanvas(self)
        self.context = glcanvas.GLContext(self.canvas)

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
        if self._initialized:
            return True

        if self.canvas is None or self.context is None:
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

        self._initialized = True
        return True

    def render(self):
        """Render frame."""
        # ensure that canvas exists
        if self.canvas is None:
            return

        # ensure that canvas is current and initialized
        if not self._is_shown_on_screen() or not self._set_current():
            return

        # ensure that opengl is initialized
        if not self.init_opengl():
            return

        size = self.GetClientSize()
        self._width = max(size.width, 1)
        self._height = max(size.height, 1)

        # multiply modelview matrix according to rotation quat
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        glMultMatrixd(quat_to_matrix4(self._rot_quat))

        # TODO: add toggle between perspective and orthographic view modes
        glViewport(0, 0, self._width, self._height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(np.arctan(np.tan(np.deg2rad(50.0)) / self._zoom) * 180 / np.pi, float(self._width) / self._height, self.clip_near, self.clip_far)
        glMatrixMode(GL_MODELVIEW)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self._render_background()
        self._render_objects()

        self.SwapBuffers()

    def on_size(self, event):
        """Handle EVT_SIZE."""
        self._dirty = True

    def on_idle(self, event):
        """Handle EVT_IDLE."""
        if not self._initialized or not self._dirty:
            return

        if self.IsFrozen():
            return

        self._refresh_if_shown_on_screen()
        self._dirty = False

    def on_key(self, event):
        """Handle EVT_KEY_DOWN and EVT_KEY_UP."""
        pass

    def on_mouse_wheel(self, event):
        """Handle mouse wheel event and adjust zoom."""
        if not self._initialized:
            return

        # ignore if middle mouse button is pressed
        if event.MiddleIsDown():
            return

        self._update_camera_zoom(event.GetWheelRotation() / event.GetWheelDelta())

    def on_mouse(self, event):
        """Handle mouse events.
            LMB drag:   move viewport
            RMB drag:   unused
            LMB/RMB up: reset position
        """
        if not self._initialized or not self._set_current():
            return

        if event.Dragging():
            # self._mouse_pos = event.GetPosition()
            if event.LeftIsDown():
                self.rotate_camera(event, use_arcball=self.arcball_control)
            elif event.RightIsDown() or event.MiddleIsDown():
                self.translate_camera(event)
        elif event.LeftUp() or event.MiddleUp() or event.RightUp() or event.Leaving():
            if self._mouse_pos is not None:
                self._mouse_pos = None
        # elif event.Moving():
        else:
            event.Skip()
        self._dirty = True

    def on_left_dclick(self, event):
        """Handle EVT_LEFT_DCLICK."""
        print('double click')

    def on_erase_background(self, event):
        """Handle the erase background event."""
        pass  # Do nothing, to avoid flashing on MSW.

    def on_paint(self, event):
        """Handle EVT_PAINT."""
        if self._initialized:
            self._dirty = True
        else:
            self.render()

    def on_set_focus(self, event):
        """Handle EVT_SET_FOCUS."""
        self._refresh_if_shown_on_screen()

    def destroy(self):
        """Clean up the OpenGL context."""
        self.context.destroy()
        glcanvas.GLCanvas.Destroy()

    # --------------
    # Util functions
    # --------------

    def _is_shown_on_screen(self):
        """Return whether or not the canvas is physically visible on the screen."""
        return False if self.canvas is None else self.canvas.IsShownOnScreen()

    def _set_current(self):
        """Set current OpenGL context as current."""
        return False if self.context is None else self.SetCurrent(self.context)

    def _update_camera_zoom(self, delta_zoom):
        zoom = self._zoom / (1.0 - max(min(delta_zoom, 4.0), -4.0) * 0.1)
        self._zoom = max(min(zoom, self._zoom_max), self._zoom_min)
        self._dirty = True

    def _refresh_if_shown_on_screen(self):
        if self._is_shown_on_screen():
            self.render()

    def _render_background(self):
        glClearColor(*self.color_background)

    def _render_objects(self):
        self._render_grid()

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

        # draw cameras
        for cam in self.camera_objects:
            cam.onDraw()

    def _render_grid(self):
        glColor3ub(200, 200, 200)

        # TODO: remove glBegin/glEnd in favor of modern OpenGL methods
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

    def get_modelview_mat(self, local_transform):
        mvmat = (GLdouble * 16)()
        glGetDoublev(GL_MODELVIEW_MATRIX, mvmat)
        return mvmat

    def mouse_to_3d(self, x, y, z=1.0, local_transform=False):
        x = float(x)
        y = self._height - float(y)
        pmat = (GLdouble * 16)()
        mvmat = self.get_modelview_mat(local_transform)
        viewport = (GLint * 4)()
        px = (GLdouble)()
        py = (GLdouble)()
        pz = (GLdouble)()
        glGetIntegerv(GL_VIEWPORT, viewport)
        glGetDoublev(GL_PROJECTION_MATRIX, pmat)
        glGetDoublev(GL_MODELVIEW_MATRIX, mvmat)
        gluUnProject(x, y, z, mvmat, pmat, viewport, px, py, pz)
        return (px.value, py.value, pz.value)

    def mouse_to_ray(self, x, y, local_transform=False):
        x = float(x)
        y = self._height - float(y)
        pmat = (GLdouble * 16)()
        mvmat = (GLdouble * 16)()
        viewport = (GLint * 4)()
        px = (GLdouble)()
        py = (GLdouble)()
        pz = (GLdouble)()
        glGetIntegerv(GL_VIEWPORT, viewport)
        glGetDoublev(GL_PROJECTION_MATRIX, pmat)
        mvmat = self.get_modelview_mat(local_transform)
        gluUnProject(x, y, 1, mvmat, pmat, viewport, px, py, pz)
        ray_far = (px.value, py.value, pz.value)
        gluUnProject(x, y, 0., mvmat, pmat, viewport, px, py, pz)
        ray_near = (px.value, py.value, pz.value)
        return ray_near, ray_far

    def mouse_to_plane(self, x, y, plane_normal, plane_offset, local_transform=False):
        # Ray/plane intersection
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
