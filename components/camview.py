#!/usr/bin/env python3
"""TODO: Fill in docstring"""

import numpy as np
from enums import Axis
import math

import wx
from OpenGL.GL import *
from OpenGL.GLU import *

from .canvas import CanvasBase
from .arcball import axis_to_quat, quat_to_mat


class Canvas(CanvasBase):
    # True: use arcball controls, False: use orbit controls
    arcball_control = True

    def __init__(self, parent, *args, **kwargs):
        super(Canvas, self).__init__(parent)
        self.parent = parent

        self.mousepos = (0, 0)
        self.dist = 1
        self.basequat = [0, 0, 0, 1]
        self.scale = 1.0
        self.camera_objects = []
        self.initpos = None

        self.Bind(wx.EVT_MOUSE_EVENTS, self.move)
        self.Bind(wx.EVT_MOUSEWHEEL, self.wheel)
        self.Bind(wx.EVT_LEFT_DCLICK, self.double_click)

    def OnReshape(self):
        super(Canvas, self).OnReshape()

    def OnInitGL(self):
        """Initialize OpenGL."""
        if self.gl_init:
            return
        self.gl_init = True

        self.SetCurrent(self.context)
        self.quadratic = gluNewQuadric()

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
        return

    def draw_objects(self):
        """Called in OnDraw after the buffer has been cleared."""
        self.create_objects()

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        # multiply modelview matrix according to rotation quat
        glMultMatrixf(quat_to_mat(self.basequat))

        for cam in self.camera_objects:
            cam.onDraw()

    def create_objects(self):
        """Create OpenGL objects when OpenGL is initialized."""
        self.draw_grid()
        glColor3ub(180, 180, 180)
        self.draw_circle([0, 0, 0], [0, 0, 1], 1.41421356237)
        self.draw_circle([0, 0, 0], [0, 1, 0], 1.41421356237)
        self.draw_circle([0, 0, 0], [1, 0, 0], 1.41421356237)

        # draw sphere
        glColor3ub(0, 0, 128)
        gluSphere(self.quadratic, 0.25, 32, 32)

    def draw_grid(self):
        """Draw coordinate grid."""
        glColor3ub(180, 180, 180)

        glBegin(GL_LINES)
        for i in np.arange(-10, 11, 1):
            i *= 0.1
            glVertex3f(i, 1, 0)
            glVertex3f(i, -1, 0)
            glVertex3f(1, i, 0)
            glVertex3f(-1, i, 0)

        glColor3ub(255, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(1.5, 0, 0)
        glColor3ub(0, 255, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 1.5, 0)
        glColor3ub(0, 0, 255)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 1.5)
        glEnd()

    def draw_circle(self, p, n, r, sides=36):
        """Draw circle given point, plane normal vector, radius, and # sides."""
        n = np.array(n)
        if not n.any():
            raise ValueError('zero magnitude normal vector')
        n = n / np.linalg.norm(n)
        ex = np.array([1, 0, 0]) # x axis normal basis vector
        ey = np.array([0, 1, 0]) # y axis normal basis vector

        # rotates x, y, z basis vectors so that the basis vector for the z axis
        # aligns with the normalized normal vector n
        if (n != np.array([0, 0, 1])).any():
            phi = math.acos(np.dot(n, np.array([0, 0, 1])))
            axis = np.cross(n, np.array([0, 0, 1]))
            l = list(quat_to_mat(axis_to_quat(axis.tolist(), phi)))
            rot = np.array([[l[0], l[1], l[2]], [l[4], l[5], l[6]], [l[8], l[9], l[10]]])
            ex = rot.dot(np.array([1, 0, 0])) # apply rotation matrices to x and y basis vectors
            ey = rot.dot(np.array([0, 1, 0]))

        # calculate coordinates of vertices given the sides resolution
        verts = sides + 1
        tau = 6.28318530717958647692
        circle_verts = (GLfloat * (verts*3))()
        for i in range(verts):
            circle_verts[i*3] = GLfloat(
                p[0] + r * (ex[0] * math.cos(i*tau/sides) + ey[0] * math.sin(i*tau/sides)))
            circle_verts[i*3 + 1] = GLfloat(
                p[1] + r * (ex[1] * math.cos(i*tau/sides) + ey[1] * math.sin(i*tau/sides)))
            circle_verts[i*3 + 2] = GLfloat(
                p[2] + r * (ex[2] * math.cos(i*tau/sides) + ey[2] * math.sin(i*tau/sides)))

        # draw circle using GL_LINE_STRIP
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, circle_verts)
        glDrawArrays(GL_LINE_STRIP, 0, verts)
        glDisableClientState(GL_VERTEX_ARRAY)


class Camera3D():
    def __init__(self, id, x, y, z, b, c):
        self.id = id
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.b = float(b)
        self.c = float(c)

        self.start = (self.x, self.y, self.z, self.b, self.c)
        self.mode = "normal"

        self.angle = 0
        self.rotationVector = []

    def onDraw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        if self.mode == 'normal':
            if self.b != 0.0:
                glRotatef(self.b, 0, 0, 1)
            if self.c != 0.0:
                glRotatef(self.c, 0, 1, 0)
        elif self.mode == 'rotate':
            glRotatef(self.angle, self.rotationVector[0], self.rotationVector[1], self.rotationVector[2])

        glBegin(GL_QUADS)
        ## bottom
        glColor3ub(255, 255, 255)
        glVertex3f(-0.025, -0.05, -0.05)
        glVertex3f( 0.025, -0.05, -0.05)
        glVertex3f( 0.025, -0.05,  0.05)
        glVertex3f(-0.025, -0.05,  0.05)

        ## right
        glColor3ub(255, 255, 255)
        glVertex3f(-0.025,  0.05, -0.05)
        glVertex3f( 0.025,  0.05, -0.05)
        glVertex3f( 0.025, -0.05, -0.05)
        glVertex3f(-0.025, -0.05, -0.05)

        ## top
        glColor3ub(255, 255, 255)
        glVertex3f(-0.025,  0.05, -0.05)
        glVertex3f( 0.025,  0.05, -0.05)
        glVertex3f( 0.025,  0.05,  0.05)
        glVertex3f(-0.025,  0.05,  0.05)

        ## left
        glColor3ub(255, 255, 255)
        glVertex3f(-0.025, -0.05,  0.05)
        glVertex3f( 0.025, -0.05,  0.05)
        glVertex3f( 0.025,  0.05,  0.05)
        glVertex3f(-0.025,  0.05,  0.05)

        ## back
        glColor3ub(255, 255, 255)
        glVertex3f( 0.025, -0.05, -0.05)
        glVertex3f( 0.025, -0.05,  0.05)
        glVertex3f( 0.025,  0.05,  0.05)
        glVertex3f( 0.025,  0.05, -0.05)

        ## front
        glColor3ub(255, 255, 255)
        glVertex3f(-0.025, -0.05, -0.05)
        glVertex3f(-0.025, -0.05,  0.05)
        glVertex3f(-0.025,  0.05,  0.05)
        glVertex3f(-0.025,  0.05, -0.05)
        glEnd()

        glPushMatrix()
        glColor3ub(255, 255, 255)
        glTranslated(-0.05, 0.0, 0.0)
        quadric = gluNewQuadric()
        glRotatef(90.0, 0.0, 1.0, 0.0)
        gluCylinder(quadric, 0.025, 0.025, 0.03, 16, 16)
        gluDeleteQuadric(quadric)
        glPopMatrix()
        glPopMatrix()

    def getRotationAngle(self, v1, v2):
        v1_u = self.getUnitVector(v1)
        v2_u = self.getUnitVector(v2)
        return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1, 1)))

    def getUnitVector(self, vector):
        return vector / np.linalg.norm(vector)

    def onFocusCenter(self):
        self.mode = 'rotate'
        cameraCenterPoint = (self.x, self.y, self.z)
        currentFacingPoint = (self.x - 0.5, self.y, self.z)
        desirableFacingPoint = (0.0, 0.0, 0.0)

        v1 = np.subtract(currentFacingPoint, cameraCenterPoint)
        v2 = np.subtract(desirableFacingPoint, cameraCenterPoint)

        self.angle = self.getRotationAngle(v1, v2)
        self.rotationVector = np.cross(self.getUnitVector(v1), self.getUnitVector(v2))
        self.onDraw()

    def getZbyAngle(self, angle):
        return np.sqrt(np.square(0.5 / angle) - 0.25)

    def onMove(self, axis, amount):
        if axis in Axis and amount != 0:
            if axis == Axis.X:
                self.x += amount
            elif axis == Axis.Y:
                self.y += amount
            elif axis == Axis.Z:
                self.z += amount
            elif axis == Axis.B:
                self.b += amount
            elif axis == Axis.C:
                self.c += amount
