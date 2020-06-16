from OpenGL.GL import *
from OpenGL.GLU import *
import wx
from wx import glcanvas
import numpy as np
from enums import Axis

class CanvasBase(glcanvas.GLCanvas):
    def __init__(self, parent):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.init = False
        self.context = glcanvas.GLContext(self)
        
        self.viewPoint = (0.0, 0.0, 0.0)
        self.zoom = 1
        self.nearClip = 3.0
        self.farClip = 7.0

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
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)

    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def OnSize(self, event):
        wx.CallAfter(self.DoSetViewport)
        event.Skip()

    def DoSetViewport(self):
        width, height = size = self.size = self.GetClientSize()
        self.SetCurrent(self.context)

        # set viewport dimensions to square (may change later)
        min_size = min(width, height)
        glViewport(0, 0, min_size, min_size)

        aspect = size.width / size.height;
        
    def OnPaint(self, event):
        self.SetCurrent(self.context)
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnDraw()

    def OnMouseDown(self, evt):
        self.CaptureMouse()
        self.x, self.z = self.lastx, self.lastz = evt.GetPosition()

        x = float(self.x)
        y = self.size[1] - float(self.z)
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
        print (ray_near, ray_far)

        # transform Gui coordinates into GL
        # self.size = GetClientSize()
        # wxPoint pt = event.GetPosition()
        # int gx = (2.0 * pt.x) / (siz.GetWidth() - 1) - 1.0
        # int gy = 1.0 - (2.0 * pt.y) / (siz.GetHeight() - 1)

        # # Get x,y coords of mouse click in Normalized Device Coords
        # x = 2.0 * self.x / self.size[0] - 1.0
        # y = 1.0 - 2.0 * self.z / self.size[1]
        # # print(x,y)

        # #4D homogenous clip coordinates
        # rayClip = np.array([x,y, -1.0, 1.0])

        # #4D Eye (Camera) coordinates)
        # mPersp = glGetDoublev(GL_PROJECTION_MATRIX)
        # rayEye = np.linalg.inv(mPersp).dot(rayClip)
        # rayEye[2] = -1.0
        # rayEye[3] = 0.0
        
        # #4D World Coordinates
        # view = glGetDoublev(GL_MODELVIEW_MATRIX)
        # rayWorld = np.linalg.inv(view).dot(rayEye)
        # #Normalize
        # norm = np.linalg.norm(rayWorld)
        # rayWorld = rayWorld/norm

        # # print(rayWorld)
        # camList = self.camera_objects

        # for cam in camList:
        #     if rayWorld[0] < cam.x + 0.01 and rayWorld[0] > cam.x - 0.01:
        #         print("In x")
        #     else:
        #         print("X: ", rayWorld[0], cam.x)
        #         print("Z: ", rayWorld[2], cam.z)

        # if camList:
        #     print(camList[0].x)
        # else:
        #     print("No cams")

        # print(GL_QUADS[0])
########

    def OnMouseUp(self, evt):
        # clear "residual movement"
        self.lastx, self.lastz = self.x, self.z
        self.ReleaseMouse()

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            self.lastx, self.lastz = self.x, self.z
            self.x, self.z = evt.GetPosition()
            self.Refresh(False)

    def OnMouseWheel(self, event):
        wheelRotation = event.GetWheelRotation()

        if wheelRotation != 0:
            if wheelRotation > 0:
                self.zoom += 0.1
            elif wheelRotation < 0:
                self.zoom -= 0.1

            if self.zoom < 0.8:
                self.zoom = 0.8
            elif self.zoom > 3.0:
                self.zoom = 3.0

        self.Refresh()

class Canvas(CanvasBase):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.scale = 1.0
        self.camera_objects = []

        if self.size is None:
            self.size = self.GetClientSize()
            self.w, self.h = self.size

    def InitGL(self):
        self.quadratic = gluNewQuadric()
        # set viewing projection
        self.setProjectionMatrix()

        # initialize view
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 5.0,
             0.0, 0.0, 0.0,
             0.0, 1.0, 0.0)

    def OnDraw(self):
        # clear color and depth buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.setProjectionMatrix()

        # there seems to be a difference between the commented chunk
        # and the one below, but I'm not sure why they're different
        # w = max(self.w, 1.0)
        # h = max(self.h, 1.0)
        # xScale = 180.0 / w
        # zScale = 180.0 / h

        w, h = self.size
        w = max(w, 1.0)
        h = max(h, 1.0)
        xScale = 180.0 / w
        zScale = 180.0 / h
        
        glRotatef((self.x - self.lastx) * xScale, 0.0, 1.0, 0.0)
        glRotatef((self.z - self.lastz) * zScale, 1.0, 0.0, 0.0)

        self.InitGrid()
        
        ## object
        glColor3ub(0, 0, 128)
        gluSphere(self.quadratic, 0.2, 32, 32)
       
        for cam in self.camera_objects:
            cam.onDraw()

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

    def setProjectionMatrix(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        if self.w / self.h < 1:
            self.zoom *= self.w / self.h

        gluPerspective(np.arctan(np.tan(50.0 * 3.14159 / 360.0) / self.zoom) * 360.0 / 3.14159, self.w / self.h, self.nearClip, self.farClip)
        # glFrustum(-0.5 / self.zoom, 0.5 / self.zoom, -0.5 / self.zoom, 0.5 / self.zoom, self.nearClip, self.farClip)

        # set to position viewer
        glMatrixMode(GL_MODELVIEW)


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
        glColor3ub(255, 0, 255)	
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
