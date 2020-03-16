from OpenGL.GL import *
from OpenGL.GLU import *
import wx
from wx import glcanvas
import numpy as np
from camera import Camera
import time
from enums import Axis

class CanvasBase(glcanvas.GLCanvas):
    def __init__(self, parent):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.init = False
        self.context = glcanvas.GLContext(self)
        
        # initial mouse position
        self.lastx = self.x = 30
        self.lastz = self.z = 30
        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)

    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def OnSize(self, event):
        wx.CallAfter(self.DoSetViewport)
        event.Skip()

    def DoSetViewport(self):
        size = self.size = self.GetClientSize()
        self.SetCurrent(self.context)
        glViewport(0, 0, size.width, size.height)
        
    def OnPaint(self, event):
        self.SetCurrent(self.context)
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnDraw()

    def OnMouseDown(self, evt):
        self.CaptureMouse()
        self.x, self.z = self.lastx, self.lastz = evt.GetPosition()

    def OnMouseUp(self, evt):
        self.ReleaseMouse()

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            self.lastx, self.lastz = self.x, self.z
            self.x, self.z = evt.GetPosition()
            self.Refresh(False)

class Canvas(CanvasBase):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def InitGL(self):
        global quadratic
        quadratic = gluNewQuadric()
        # set viewing projection
        glMatrixMode(GL_PROJECTION)
        glFrustum(-0.5, 0.5, -0.5, 0.5, 0.4, 5)

        # position viewer
        glMatrixMode(GL_MODELVIEW)
        glTranslatef(0.0, 0.0, -1.5)

    def OnDraw(self):
        # clear color and depth buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.InitGrid()

        if self.size is None:
            self.size = self.GetClientSize()
        w, h = self.size
        w = max(w, 1.0)
        h = max(h, 1.0)
        xScale = 180.0 / w
        zScale = 180.0 / h

        ## object
        #glPushMatrix()
        #glColor3ub(0, 0, 128)
        #gluSphere(quadratic, 0.2, 32, 32)
        #glPopMatrix()
        glRotatef((self.z - self.lastz) * zScale, 1.0, 0.0, 0.0)
        glRotatef((self.x - self.lastx) * xScale, 0.0, 0.0, 1.0)

        #for camera in self.parent.parent.GetParent().camera_models:
        #    camera.onDraw()

        self.SwapBuffers()

    def InitGrid(self):
        glColor3ub(255, 255, 255)
        
        glBegin(GL_LINES)
        for i in np.arange(-1, 1, 0.05):
            glVertex3f(i,  1, 0)
            glVertex3f(i, -1, 0)
            glVertex3f( 1, i, 0)
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

    def OnDrawSphere(self):
        pass

    def OnDrawCamera(self, id, x, y, z, b, c):
        cam = Camera3D(id, x, y, z, b, c)
        cam.onDraw()

class Camera3D():
    def __init__(self, id, x, y, z, b, c):
        self.id = id
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.b = float(b)
        self.c = float(c)

        self.start = (self.x, self.y, self.z, self.b, self.c)

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
        glColor3ub(self.red, self.green, self.blue)	
        glVertex3f(-0.025, -0.05, -0.05)	
        glVertex3f( 0.025, -0.05, -0.05)	
        glVertex3f( 0.025, -0.05,  0.05)	
        glVertex3f(-0.025, -0.05,  0.05)	

        ## right	
        glColor3ub(self.red, self.green, self.blue)	
        glVertex3f(-0.025,  0.05, -0.05)	
        glVertex3f( 0.025,  0.05, -0.05)	
        glVertex3f( 0.025, -0.05, -0.05)	
        glVertex3f(-0.025, -0.05, -0.05)

        ## top
        glColor3ub(self.red, self.green, self.blue)	
        glVertex3f(-0.025,  0.05, -0.05)	
        glVertex3f( 0.025,  0.05, -0.05)	
        glVertex3f( 0.025,  0.05,  0.05)	
        glVertex3f(-0.025,  0.05,  0.05)	

        ## left	
        glColor3ub(self.red, self.green, self.blue)	
        glVertex3f(-0.025, -0.05,  0.05)	
        glVertex3f( 0.025, -0.05,  0.05)	
        glVertex3f( 0.025,  0.05,  0.05)	
        glVertex3f(-0.025,  0.05,  0.05)	

        ## back	
        glColor3ub(self.red, self.green, self.blue)	
        glVertex3f( 0.025, -0.05, -0.05)	
        glVertex3f( 0.025, -0.05,  0.05)	
        glVertex3f( 0.025,  0.05,  0.05)	
        glVertex3f( 0.025,  0.05, -0.05)

        ## front	
        glColor3ub(self.red, self.green, self.blue)	
        glVertex3f(-0.025, -0.05, -0.05)	
        glVertex3f(-0.025, -0.05,  0.05)	
        glVertex3f(-0.025,  0.05,  0.05)	
        glVertex3f(-0.025,  0.05, -0.05)	
        glEnd()	

        glPushMatrix()	
        glColor3ub(self.red, self.green, self.blue)	
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
