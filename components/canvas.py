#!/usr/bin/env python3
"""TODO: Fill in docstring"""

from threading import Lock
import numpy as np

import wx
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *

from .arcball import arcball, axis_to_quat, mul_quat


class CanvasBase(glcanvas.GLCanvas):
    MIN_ZOOM = 0.5
    MAX_ZOOM = 5.0
    NEAR_CLIP = 3.0
    FAR_CLIP = 7.0
    color_background = (0.941, 0.941, 0.941, 1)

    def __init__(self, parent, *args, **kwargs):
        super(CanvasBase, self).__init__(parent, -1)
        self.gl_init = False
        self.gl_broken = False
        self.context = glcanvas.GLContext(self)
        self.context_attrs = glcanvas.GLContextAttrs()
        self.display_attrs = glcanvas.GLAttributes()

        self.width = None
        self.height = None

        self.viewpoint = (0.0, 0.0, 0.0)
        self.rot_lock = Lock()
        self.basequat = [0, 0, 0, 1]
        self.zoom_factor = 1.0
        self.angle_z = 0
        self.angle_x = 0
        self.zoom = 1
        self.initpos = None

        # bind events
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.processEraseBackgroundEvent)
        self.Bind(wx.EVT_SIZE, self.processSizeEvent)
        self.Bind(wx.EVT_PAINT, self.processPaintEvent)

    def processEraseBackgroundEvent(self, event):
        """Process the erase background event."""
        pass  # Do nothing, to avoid flashing on MSW.

    def processSizeEvent(self, event):
        """Process the resize event. Calls OnReshape() if window
        is not frozen and visible on screen.
        """
        if self.IsFrozen():
            event.Skip()
            return
        if self.IsShownOnScreen():
            self.SetCurrent(self.context)
            self.OnReshape()
            self.Refresh(False)
            timer = wx.CallLater(100, self.Refresh)
            timer.Start()
        event.Skip()

    def processPaintEvent(self, event):
        """Process the drawing event."""
        dc = wx.PaintDC(self)
        self.SetCurrent(self.context)

        if not self.gl_broken:
            try:
                # make sure OpenGL works properly
                self.OnInitGL()
                self.OnDraw()
            except Exception as e: # TODO: add specific glcanvas exception
                self.gl_broken = True
                print('OpenGL Failed:')
                print(e)
                # TODO: display this error in the console window
        event.Skip()

    def Destroy(self):
        """Clean up the OpenGL context."""
        self.context.destroy()
        glcanvas.GLCanvas.Destroy()

    def OnInitGL(self):
        """Initialize OpenGL."""
        if self.gl_init:
            return
        self.gl_init = True
        self.SetCurrent(self.context)
        glClearColor(*self.color_background)
        glClearDepth(1.0)

    def OnReshape(self):
        """Reshape the OpenGL viewport based on the size of the window.
        Called from processSizeEvent().
        """
        size = self.GetClientSize()
        width, height = size.width, size.height

        self.width = max(float(width), 1.0)
        self.height = max(float(height), 1.0)

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(np.arctan(np.tan(50.0 * 3.14159 / 360.0) / self.zoom) * 360.0 / 3.14159, float(self.width) / self.height, self.NEAR_CLIP, self.FAR_CLIP)
        glMatrixMode(GL_MODELVIEW)

    def OnDraw(self):
        """Draw the window. Called from processPaintEvents()."""
        # self.SetCurrent(self.context)
        glClearColor(*self.color_background)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.draw_objects()
        self.SwapBuffers()

    # -------------------------------
    # To be implemented by a subclass
    # -------------------------------

    def draw_objects(self):
        """Called in OnDraw after the buffer has been cleared."""
        return

    def create_objects(self):
        """Create OpenGL objects when window is initialized."""
        return

    def onMouseWheel(self, event):
        """Process mouse wheel event. Adjusts zoom accordingly
        and takes into consideration the zoom boundaries.
        """
        delta = event.GetWheelRotation()

        if delta != 0:
            if delta > 0:
                self.zoom += 0.1
            elif delta < 0:
                self.zoom -= 0.1

            if self.zoom < self.MIN_ZOOM:
                self.zoom = self.MIN_ZOOM
            elif self.zoom > self.MAX_ZOOM:
                self.zoom = self.MAX_ZOOM

        self.OnReshape()
        self.Refresh()

    # --------------
    # Util functions
    # --------------

    def get_modelview_mat(self, local_transform):
        mvmat = (GLdouble * 16)()
        glGetDoublev(GL_MODELVIEW_MATRIX, mvmat)
        return mvmat

    def mouse_to_3d(self, x, y, z=1.0, local_transform=False):
        x = float(x)
        y = self.height - float(y)
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
        y = self.height - float(y)
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

    def zoom_test(self, factor, to=None):
        glMatrixMode(GL_MODELVIEW)
        if to:
            delta_x = to[0]
            delta_y = to[1]
            glTranslatef(delta_x, delta_y, 0)
        glScalef(factor, factor, 1)
        self.zoom_factor *= factor
        if to:
            glTranslatef(-delta_x, -delta_y, 0)
        wx.CallAfter(self.Refresh)

    def orbit_rotation(self, p1x, p1y, p2x, p2y):
        """Rotate canvas using two orbits."""
        if p1x == p2x and p1y == p2y:
            return [0.0, 0.0, 0.0, 1.0]
        delta_z = p2x - p1x
        self.angle_z -= delta_z
        rot_z = axis_to_quat([0.0, 0.0, 1.0], self.angle_z)

        delta_x = p2y - p1y
        self.angle_x += delta_x
        rot_x = axis_to_quat([1.0, 0.0, 0.0], self.angle_x)
        return mul_quat(rot_z, rot_x)

    def arcball_rotation(self, p1x, p1y, p2x, p2y):
        """Rotate canvas using an arcball."""
        if p1x == p2x and p1y == p2y:
            return [0.0, 0.0, 0.0, 1.0]
        quat = arcball(p1x, p1y, p2x, p2y, 1)
        return mul_quat(self.basequat, quat)

    def handle_rotation(self, event, use_arcball=True):
        """Update basequat based on mouse position.
        use_arcball = True:     Use arcball_rotation to rotate canvas.
        use_arcball = False:    Use orbit_rotation to rotate canvas.
        """
        if self.initpos is None:
            self.initpos = event.GetPosition()
            return
        last = self.initpos
        cur = event.GetPosition()

        last_x = float(last.x) * 2.0 / self.width - 1.0
        last_y = 1 - float(last.y) * 2.0 / self.height
        cur_x = float(cur.x) * 2.0 / self.width - 1.0
        cur_y = 1 - float(cur.y) * 2.0 / self.height

        with self.rot_lock:
            if use_arcball:
                self.basequat = self.arcball_rotation(last_x, last_y, cur_x, cur_y)
            else:
                self.basequat = self.orbit_rotation(last_x, last_y, cur_x, cur_y)
        self.initpos = cur

    def handle_translation(self, event):
        if self.initpos is None:
            self.initpos = event.GetPosition()
            return
        last = self.initpos
        cur = event.GetPosition()
        # Do stuff
        self.initpos = cur
