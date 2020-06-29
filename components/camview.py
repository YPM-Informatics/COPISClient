#!/usr/bin/env python3
"""TODO: Fill in docstring"""

import numpy as np
from enums import Axis
import math

import wx
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from .canvas import CanvasBase
from .glhelper import vector_to_quat, quat_to_matrix4, draw_circle, draw_helix

class Canvas(CanvasBase):
    # True: use arcball controls, False: use orbit controls
    arcball_control = True

    def __init__(self, parent, *args, **kwargs):
        super(Canvas, self).__init__(parent)
        self.parent = parent

        self.scale = 1.0
        self.camera_objects = []
        self.mousepos = (0, 0)
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

        glClearColor(*self.color_background)
        glClearDepth(1.0)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)

        # draw antialiased lines and specify blend function
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


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
        pass

    def draw_objects(self):
        """Called in OnDraw after the buffer has been cleared."""
        self.create_objects()

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        # multiply modelview matrix according to rotation quat
        glMultMatrixf(quat_to_matrix4(self.basequat))

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

        self.trans = False
        self.nIncre = 0
        self.increx = 0
        self.increy = 0
        self.increz = 0

        self.isSelected = False

    def onDraw(self):

        ## Set color based on selection
        if self.isSelected:
            color = [75, 230, 150]
        else:
            color = [125, 125, 125]

        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        if self.mode == 'normal':
            if self.b != 0.0:
                glRotatef(self.b, 0, 0, 1)
            if self.c != 0.0:
                glRotatef(self.c, 0, 1, 0)
        elif self.mode == 'rotate':
            glRotatef(self.angle, self.rotationVector[0], self.rotationVector[1], self.rotationVector[2])

        if self.trans:
            self.translate()

        glBegin(GL_QUADS)

        ## bottom
        glColor3ub(*color)
        glVertex3f(-0.025, -0.05, -0.05)
        glVertex3f( 0.025, -0.05, -0.05)
        glVertex3f( 0.025, -0.05,  0.05)
        glVertex3f(-0.025, -0.05,  0.05)

        ## right
        glVertex3f(-0.025,  0.05, -0.05)
        glVertex3f( 0.025,  0.05, -0.05)
        glVertex3f( 0.025, -0.05, -0.05)
        glVertex3f(-0.025, -0.05, -0.05)

        ## top
        glVertex3f(-0.025,  0.05,  0.05)
        glVertex3f( 0.025,  0.05,  0.05)
        glVertex3f( 0.025,  0.05, -0.05)
        glVertex3f(-0.025,  0.05, -0.05)
        
        ## left
        glVertex3f(-0.025, -0.05,  0.05)
        glVertex3f( 0.025, -0.05,  0.05)
        glVertex3f( 0.025,  0.05,  0.05)
        glVertex3f(-0.025,  0.05,  0.05)

        ## back
        glVertex3f( 0.025,  0.05, -0.05)
        glVertex3f( 0.025,  0.05,  0.05)
        glVertex3f( 0.025, -0.05,  0.05)
        glVertex3f( 0.025, -0.05, -0.05)
        
        ## front
        glVertex3f(-0.025, -0.05, -0.05)
        glVertex3f(-0.025, -0.05,  0.05)
        glVertex3f(-0.025,  0.05,  0.05)
        glVertex3f(-0.025,  0.05, -0.05)
        glEnd()

        glPushMatrix()

        ## lens
        glColor3ub(*[x - 15 for x in color])
        glTranslated(-0.05, 0.0, 0.0)
        quadric = gluNewQuadric()
        glRotatef(90.0, 0.0, 1.0, 0.0)
        gluCylinder(quadric, 0.025, 0.025, 0.03, 16, 16)
        gluDeleteQuadric(quadric)

        ## cap
        glColor3ub(*[x - 25 for x in color])
        circleQuad = gluNewQuadric()
        gluQuadricOrientation(circleQuad, GLU_INSIDE)
        gluDisk(circleQuad, 0.0, 0.025, 16, 1)
        gluDeleteQuadric(circleQuad)

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

    def translate(self, newx=0, newy=0, newz=0):
        #Initialize nIncre and increxyz, skip if already initialized
        if not self.trans:
            dx = round(newx - self.x, 2)
            dy = round(newy - self.y, 2)
            dz = round(newz - self.z, 2)
            
            maxd = max(dx, dy, dz)
            scale = maxd/0.01

            self.nIncre = scale
            self.increx = dx/scale
            self.increy = dy/scale
            self.increz = dz/scale
            
            #Setting trans to true allows this function to be called on cam.onDraw
            self.trans = True
            
        if self.nIncre > 0:
            self.x += self.increx
            self.y += self.increy
            self.z += self.increz
        
            self.nIncre -= 1
        else:
            self.x = round(self.x, 2)
            self.y = round(self.y, 2)
            self.z = round(self.z, 2)
            self.trans = False