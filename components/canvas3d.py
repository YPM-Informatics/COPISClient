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
    MIN_ZOOM = 0.5  # TODO: make these default
    MAX_ZOOM = 5.0
    NEAR_CLIP = 3.0
    FAR_CLIP = 7.0
    # True: use arcball controls, False: use orbit controls
    arcball_control = True
    color_background = (0.941, 0.941, 0.941, 1)

    def __init__(self, parent, *args, **kwargs):
        super(Canvas3D, self).__init__(parent, -1)
        self.gl_init = False
        self.gl_broken = False

        # these attributes cannot be set for the time being
        display_attrs = glcanvas.GLAttributes()
        display_attrs.PlatformDefaults().MinRGBA(8, 8, 8, 8).DoubleBuffer().Depth(32).EndList()
        context_attrs = glcanvas.GLContextAttrs()
        context_attrs.CoreProfile().OGLVersion(4, 5).Robust().ResetIsolation().EndList()

        # initialize canvas and context
        self.canvas = glcanvas.GLCanvas(self)
        self.context = glcanvas.GLContext(self.canvas)

        self.width = None
        self.height = None

        self.rot_quat = [1, 0, 0, 0]
        self.rot_lock = Lock()
        self.zoom_factor = 1.0
        self.angle_z = 0
        self.angle_x = 0
        self.zoom = 1
        self.initpos = None
        self.camera_objects = []

        # bind events
        self.Bind(wx.EVT_MOUSE_EVENTS, self.move)
        self.Bind(wx.EVT_MOUSEWHEEL, self.wheel)
        self.Bind(wx.EVT_LEFT_DCLICK, self.double_click)
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
        if self.canvas.IsShownOnScreen():
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
        self.quadratic = gluNewQuadric()

        glClearColor(*self.color_background)
        glClearDepth(1.0)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)

        # draw antialiased lines and specify blend function
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

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
        gluPerspective(np.arctan(np.tan(np.deg2rad(50.0)) / self.zoom) * 180 / np.pi, float(self.width) / self.height, self.NEAR_CLIP, self.FAR_CLIP)
        glMatrixMode(GL_MODELVIEW)

    def OnDraw(self):
        """Draw the window. Called from processPaintEvents()."""
        self.SetCurrent(self.context)
        glClearColor(*self.color_background)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.draw_objects()
        self.SwapBuffers()

    def move(self, event):
        """React to mouse events.
        LMB drag:   move viewport
        RMB drag:   unused
        LMB/RMB up: reset position
        """
        self.mousepos = event.GetPosition()
        if event.Dragging() and event.LeftIsDown():
            self.handle_rotation(event, use_arcball=self.arcball_control)
        elif event.Dragging() and event.RightIsDown():
            self.handle_translation(event)
        elif event.ButtonUp() or event.Leaving():
            if self.initpos is not None:
                self.initpos = None
        else:
            event.Skip()
            return
        event.Skip()
        wx.CallAfter(self.Refresh)

    def handle_wheel(self, event):
        """(Currently unused) Reacts to mouse wheel changes."""
        delta = event.GetWheelRotation()

        factor = 1.05
        x, y = event.GetPosition()
        x, y, _ = self.mouse_to_3d(x, y, local_transform=True)

        if delta > 0:
            self.zoom_test(factor, (x, y))
        else:
            self.zoom_test(1 / factor, (x, y))

    def wheel(self, event):
        """React to the scroll wheel event."""
        # self.handle_wheel(event)
        self.onMouseWheel(event)
        wx.CallAfter(self.Refresh)

    def double_click(self, event):
        """React to the double click event."""
        print('double click')

    def draw_objects(self):
        """Called in OnDraw after the buffer has been cleared."""
        self.create_objects()

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        # multiply modelview matrix according to rotation quat
        glMultMatrixf(quat_to_matrix4(self.rot_quat))

        for cam in self.camera_objects:
            cam.onDraw()

    def create_objects(self):
        """Create OpenGL objects when OpenGL is initialized."""
        self.draw_grid()

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

    def draw_grid(self):
        """Draw coordinate grid."""
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
            return [1.0, 0.0, 0.0, 0.0]
        delta_z = p2x - p1x
        self.angle_z -= delta_z
        rot_z = vector_to_quat([0.0, 0.0, 1.0], self.angle_z)

        delta_x = p2y - p1y
        self.angle_x += delta_x
        rot_x = vector_to_quat([1.0, 0.0, 0.0], self.angle_x)
        return mul_quat(rot_z, rot_x)

    def arcball_rotation(self, p1x, p1y, p2x, p2y):
        """Rotate canvas using an arcball."""
        if p1x == p2x and p1y == p2y:
            return [1.0, 0.0, 0.0, 0.0]
        quat = arcball(p1x, p1y, p2x, p2y, math.sqrt(2)/2)
        return mul_quat(self.rot_quat, quat)

    def handle_rotation(self, event, use_arcball=True):
        """Update rot_quat based on mouse position.
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
                self.rot_quat = self.arcball_rotation(last_x, last_y, cur_x, cur_y)
            else:
                self.rot_quat = self.orbit_rotation(last_x, last_y, cur_x, cur_y)
        self.initpos = cur

    def handle_translation(self, event):
        if self.initpos is None:
            self.initpos = event.GetPosition()
            return
        last = self.initpos
        cur = event.GetPosition()
        # Do stuff
        self.initpos = cur
