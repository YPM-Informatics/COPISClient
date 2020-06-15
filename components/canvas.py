#!/usr/bin/env python3
"""TODO: Fill in docstring"""

import wx
from wx import glcanvas

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *


class CanvasBase(glcanvas.GLCanvas):
    MIN_ZOOM = 0.5
    MAX_ZOOM = 5.0
    NEAR_CLIP = 3.0
    FAR_CLIP = 7.0
    ASPECT_CONSTRAINT = 1.9

    def __init__(self, parent, *args, **kwargs):
        super(CanvasBase, self).__init__(parent, -1)
        self.GLinitialized = False
        self.context = glcanvas.GLContext(self)

        self.viewPoint = (0.0, 0.0, 0.0)
        self.zoom = 1

        self.width = None
        self.height = None

        # initial mouse position
        self.lastx = self.x = 30
        self.lastz = self.z = 30
        self.size = None

        self.gl_broken = False

        # bind events
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.processEraseBackgroundEvent)
        self.Bind(wx.EVT_SIZE, self.processSizeEvent)
        self.Bind(wx.EVT_PAINT, self.processPaintEvent)

    def processEraseBackgroundEvent(self, event):
        pass  # Do nothing, to avoid flashing on MSW.

    def processSizeEvent(self, event):
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
        self.SetCurrent(self.context)

        if not self.gl_broken:
            try:
                self.OnInitGL()
                self.OnDraw()
            except Exception as e: # TODO: add specific glcanvas exception
                self.gl_broken = True
                print('OpenGL Failed:')
                print(e)
                # TODO: display this error in console window
        event.Skip()

    def Destroy(self):
        self.context.destroy()
        glcanvas.GLCanvas.Destroy()

    def OnInitGL(self):
        if self.GLinitialized:
            return
        self.GLinitialized = True

    def OnReshape(self):
        size = self.GetClientSize()
        width, height = size.width, size.height

        self.width = max(float(width), 1.0)
        self.height = max(float(height), 1.0)

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(np.arctan(np.tan(50.0 * 3.14159 / 360.0) / self.zoom) * 360.0 / 3.14159, float(width) / height, self.NEAR_CLIP, self.FAR_CLIP)
        glMatrixMode(GL_MODELVIEW)

    def OnDraw(self):
        self.SetCurrent(self.context)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.draw_objects()
        self.SwapBuffers()

    # To be implemented by a sub-class

    def create_objects(self):
        pass

    def draw_objects(self):
        pass

    # Temporary

    def onMouseDown(self, evt):
        self.CaptureMouse()
        self.x, self.z = self.lastx, self.lastz = evt.GetPosition()

    def onMouseUp(self, evt):
        # clear residual movement
        self.lastx, self.lastz = self.x, self.z
        self.ReleaseMouse()

    def onMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            self.lastx, self.lastz = self.x, self.z
            self.x, self.z = evt.GetPosition()
            self.Refresh(False)

    def onMouseWheel(self, event):
        wheelRotation = event.GetWheelRotation()

        if wheelRotation != 0:
            if wheelRotation > 0:
                self.zoom += 0.1
            elif wheelRotation < 0:
                self.zoom -= 0.1

            if self.zoom < self.MIN_ZOOM:
                self.zoom = self.MIN_ZOOM
            elif self.zoom > self.MAX_ZOOM:
                self.zoom = self.MAX_ZOOM

        self.OnReshape()
        self.Refresh()

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

    def handle_rotation(self, event):
        if self.initpos is None:
            self.initpos = event.GetPosition()
        # else:
        #     p1 = self.initpos
        #     p2 = event.GetPosition()
        #     sz = self.GetClientSize()
        #     p1x = float(p1[0]) / (sz[0] / 2) - 1
        #     p1y = 1 - float(p1[1]) / (sz[1] / 2)
        #     p2x = float(p2[0]) / (sz[0] / 2) - 1
        #     p2y = 1 - float(p2[1]) / (sz[1] / 2)
        #     quat = trackball(p1x, p1y, p2x, p2y, self.dist / 250.0)
        #     with self.rot_lock:
        #         if self.orbit_control:
        #             self.basequat = self.orbit(p1x, p1y, p2x, p2y)
        #         else:
        #             self.basequat = mulquat(self.basequat, quat)
        #     self.initpos = p2


    def handle_translation(self, event):
        if self.initpos is None:
            self.initpos = event.GetPosition()
        else:
            p1 = self.initpos
            p2 = event.GetPosition()
            # Do stuff
            self.initpos = p2
