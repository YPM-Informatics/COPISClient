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
        glcanvas.GLCanvas.__init__(self, parent, -1)
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

        self.Bind(wx.EVT_LEFT_DOWN, self.onMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.onMouseUp)
        self.Bind(wx.EVT_MOTION, self.onMouseMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel)

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
                # TODO: display error in console window
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

        self.Refresh()

