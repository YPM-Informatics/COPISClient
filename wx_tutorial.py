#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import wx
from wx import glcanvas
import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from moderngl import *
import numpy as np
from enum import Enum
import webcolors
import random

APP_EXIT = 1

class Axis(Enum):
    X = "x"
    Y = "y"
    Z = "z"
    P = "p"
    T = "t"
    Plus = "++"
    Minus = "-"
        
class CanvasBase(glcanvas.GLCanvas):
    def __init__(self, parent):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.init = False
        self.context = glcanvas.GLContext(self)
        
        # initial mouse position
        self.lastx = self.x = 30
        self.lasty = self.y = 30
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
        self.x, self.y = self.lastx, self.lasty = evt.GetPosition()

    def OnMouseUp(self, evt):
        self.ReleaseMouse()

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            self.lastx, self.lasty = self.x, self.y
            self.x, self.y = evt.GetPosition()
            self.Refresh(False)


class Canvas(CanvasBase):
    def InitGL(self):
        # set viewing projection
        glMatrixMode(GL_PROJECTION)
        glFrustum(-0.5, 0.5, -0.5, 0.5, 0.4, 5)

        # position viewer
        glMatrixMode(GL_MODELVIEW)
        glTranslatef(0.0, 0.0, -1.5)

        # position object
        glRotatef(self.y, 1.0, 0.0, 0.0)
        glRotatef(self.x, 0.0, 1.0, 0.0)

        self.cameras = []

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
        yScale = 180.0 / h

        ## object
        glPushMatrix()
        glColor3ub(0, 0, 128)
        glTranslated(0.0,0.0,0.0)
        glutSolidSphere(0.2,60,60)
        glPopMatrix()
        glRotatef((self.y - self.lasty) * yScale, 1.0, 0.0, 0.0)
        glRotatef((self.x - self.lastx) * xScale, 0.0, 1.0, 0.0)

        for camera in self.cameras:
            camera.onDraw()

        self.SwapBuffers()

    def InitGrid(self):
        glColor3ub(255, 255, 255)
        
        glBegin(GL_LINES)
        for i in np.arange(-1, 1, 0.05):
            glVertex3f(i, 0, 1)
            glVertex3f(i, 0, -1)
            glVertex3f(1, 0, i)
            glVertex3f(-1, 0, i)
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

    def OnDrawCamera(self, x, y, z, p, t):
        camera = Camera(x, y, z, p, t)
        self.cameras.append(camera)
        self.OnDraw()

class Camera():
    def __init__(self, x, y, z, p, t):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.p = float(p)
        self.t = float(t)
    
        colors = webcolors.css3_hex_to_names
        chosenColor = random.choice(list(colors.keys()))
        chosenRgb = webcolors.hex_to_rgb(chosenColor)
        self.r = chosenRgb.red
        self.g = chosenRgb.green
        self.b = chosenRgb.blue

    def onDraw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        if self.p != 0.0:
            glRotatef(self.p, 0, 1, 0)
        if self.t != 0.0:
            glRotatef(-self.t, 0, 0, 1)

        glBegin(GL_QUADS)
        ## bottom
        glColor3ub(self.r, self.g, self.b)
        glVertex3f(-0.025, -0.05, -0.05)
        glVertex3f( 0.025, -0.05, -0.05)
        glVertex3f( 0.025, -0.05,  0.05)
        glVertex3f(-0.025, -0.05,  0.05)

        ## right
        glColor3ub(self.r, self.g, self.b)
        glVertex3f(-0.025,  0.05, -0.05)
        glVertex3f( 0.025,  0.05, -0.05)
        glVertex3f( 0.025, -0.05, -0.05)
        glVertex3f(-0.025, -0.05, -0.05)
        
        ## top
        glColor3ub(self.r, self.g, self.b)
        glVertex3f(-0.025,  0.05, -0.05)
        glVertex3f( 0.025,  0.05, -0.05)
        glVertex3f( 0.025,  0.05,  0.05)
        glVertex3f(-0.025,  0.05,  0.05)

        ## left
        glColor3ub(self.r, self.g, self.b)
        glVertex3f(-0.025, -0.05,  0.05)
        glVertex3f( 0.025, -0.05,  0.05)
        glVertex3f( 0.025,  0.05,  0.05)
        glVertex3f(-0.025,  0.05,  0.05)

        ## back
        glColor3ub(self.r, self.g, self.b)
        glVertex3f( 0.025, -0.05, -0.05)
        glVertex3f( 0.025, -0.05,  0.05)
        glVertex3f( 0.025,  0.05,  0.05)
        glVertex3f( 0.025,  0.05, -0.05)

        ## front
        glColor3ub(self.r, self.g, self.b)
        glVertex3f(-0.025, -0.05, -0.05)
        glVertex3f(-0.025, -0.05,  0.05)
        glVertex3f(-0.025,  0.05,  0.05)
        glVertex3f(-0.025,  0.05, -0.05)
        glEnd()

        glPushMatrix()
        glColor3ub(self.r, self.g, self.b)
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

    def onRotate(self):
        cameraCenterPoint = (x, y, z)
        currentFacingPoint = (x - 0.5, y, z)
        desirableFacingPoint = (0.0, 0.0, 0.0)

        v1 = np.subtract(currentFacingPoint, cameraCenterPoint)
        v2 = np.subtract(desirableFacingPoint, cameraCenterPoint)
        
        self.angle = self.getRotationAngle(v1, v2)
        self.rotationVector = np.cross(self.getUnitVector(v1), self.getUnitVector(v2))

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
            elif axis == Axis.P:
                self.p += amount
            elif axis == Axis.T:
                self.t += amount

class MyPopupMenu(wx.Menu):
    def __init__(self, parent):
        super(MyPopupMenu, self).__init__()
        self.parent = parent

        mmi = wx.MenuItem(self, wx.NewId(), 'Minimize')
        self.Append(mmi)
        self.Bind(wx.EVT_MENU, self.OnMinimize, mmi)

        cmi = wx.MenuItem(self, wx.NewId(), 'Close')
        self.Append(cmi)
        self.Bind(wx.EVT_MENU, self.OnClose, cmi)

    def OnMinimize(self, e):
        self.parent.Iconize()

    def OnClose(self, e):
        self.parent.Close()

class LeftPanel(wx.Panel):
    def __init__(self, parent):
        super(LeftPanel, self).__init__(parent, style = wx.BORDER_SUNKEN)
        self.parent = parent
        self.InitPanel()
        self.canvas = ""

    def InitPanel(self):
        vboxLeft = wx.BoxSizer(wx.VERTICAL)
        
        ## header font
        self.font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(15)

        ## Adding camera section
        add_camera_hbox = self.InitAddCamera()
        vboxLeft.Add(add_camera_hbox, 0.5, wx.LEFT|wx.TOP, border = 15)

        ## Positioning section starts
        positioning_vbox = self.InitPositioning()
        vboxLeft.Add(positioning_vbox, 0.5, flag = wx.LEFT|wx.TOP, border = 15)

        ## Circular path generator section
        circular_path_hbox = self.InitCircularPathGenerator()
        vboxLeft.Add(circular_path_hbox, 0.5, flag = wx.LEFT, border = 15)

        ## Z stack generator and camera control section
        z_stack_hbox = self.InitZStackAndCamControl()
        vboxLeft.Add(z_stack_hbox, 0.5, flag = wx.LEFT|wx.TOP, border = 15)
        
        self.SetSizerAndFit(vboxLeft)
        
    def InitAddCamera(self):
        ## LAYOUT
        
        ########################################################################################
        ##                                                                                    ##
        ## hbox ----------------------------------------------------------------------------- ##
        ##      | vbox  ------------------------------------------ vbox     --------------- | ##
        ##      | Xyzpt | hbox --------------------------------- | AddClear | ----------- | | ##
        ##      |       | Xyz  |    ------    ------    ------ | |          | |   Add   | | | ##
        ##      |       |      | X: |    | Y: |    | Z: |    | | |          | ----------- | | ##
        ##      |       |      |    ------    ------    ------ | |          | ----------- | | ##
        ##      |       |      --------------------------------- |          | |  Clear  | | | ##
        ##      |       | hbox --------------------------------- |          | ----------- | | ##
        ##      |       | Pt   |    ------    ------           | |          --------------- | ##
        ##      |       |      | P: |    | P: |    |           | |                          | ##
        ##      |       |      |    ------    ------           | |                          | ##
        ##      |       |      --------------------------------- |                          | ##
        ##      |       ------------------------------------------                          | ##
        ##      ----------------------------------------------------------------------------- ##
        ##                                                                                    ##
        ########################################################################################
        hbox = wx.BoxSizer()
        vboxXyzpt = wx.BoxSizer(wx.VERTICAL)
        hboxXyz = wx.BoxSizer()
        xInputLabel = wx.StaticText(self, -1, "X: ")
        hboxXyz.Add(xInputLabel, 1, flag = wx.RIGHT, border = 10)
        self.xTc = wx.TextCtrl(self)
        hboxXyz.Add(self.xTc)
        yInputLabel = wx.StaticText(self, -1, "Y: ")
        hboxXyz.Add(yInputLabel, 1, flag = wx.RIGHT|wx.LEFT, border = 10)
        self.yTc = wx.TextCtrl(self)
        hboxXyz.Add(self.yTc)
        zInputLabel = wx.StaticText(self, -1, "Z: ")
        hboxXyz.Add(zInputLabel, 1, flag = wx.RIGHT|wx.LEFT, border = 10)
        self.zTc = wx.TextCtrl(self)
        hboxXyz.Add(self.zTc)
        vboxXyzpt.Add(hboxXyz)

        hboxPt = wx.BoxSizer()
        pInputLabel = wx.StaticText(self, -1, "P: ")
        hboxPt.Add(pInputLabel, 1, flag = wx.RIGHT, border = 10)
        self.pTc = wx.TextCtrl(self)
        hboxPt.Add(self.pTc)
        tInputLabel = wx.StaticText(self, -1, "T: ")
        hboxPt.Add(tInputLabel, 1, flag = wx.RIGHT|wx.LEFT, border = 10)
        self.tTc = wx.TextCtrl(self)
        hboxPt.Add(self.tTc)
        vboxXyzpt.Add(hboxPt, 1, flag = wx.TOP, border = 2)
        hbox.Add(vboxXyzpt)

        vboxAddClear = wx.BoxSizer(wx.VERTICAL)
        addCamBtn = wx.Button(self, wx.ID_ANY, label = 'Add')
        vboxAddClear.Add(addCamBtn)
        clearCamBtn = wx.Button(self, wx.ID_ANY, label = 'Clear')
        vboxAddClear.Add(clearCamBtn)
        hbox.Add(vboxAddClear, 1, flag = wx.LEFT, border = 10)

        addCamBtn.Bind(wx.EVT_BUTTON, self.OnAddCameraButton)
        
        return hbox

    def InitPositioning(self):
        ## LAYOUT
        
	####################################################################################################
        ##                                                                                                ##
        ## vbox        ---------------------------------------------------------------------------------- ##
        ## Positioning | self.hbox  ------------------------------------------------------------------- | ##
	##             | CameraInfo |                                                                 | | ##
	##             |            ------------------------------------------------------------------- | ##
	##             | Positioning                                                                    | ##
	##             | hboxTop ---------------------------------------------------------------------- | ##
        ##             |         | -----------  ------------------  --------------------  ----------- | | ##
        ##             |         | | camList |  |   Set Center   |  |Refresh From COPIS|  |  slider | | | ##
        ##             |         | -----------  ------------------  --------------------  ----------- | | ##
        ##             |         ---------------------------------------------------------------------- | ##
        ##             | hbox  ------------------------------------------------------------------------ | ##
        ##             | Xyzpt | vbox ----------------------------- vbox ---------------------------- | | ##
        ##             |       | Xyz  | XYZ Increment Size        | Pt   | PT Increment Size        | | | ##
        ##             |       |      | hboxXyz ----------------- |      | hboxPt ----------------- | | | ##
        ##             |       |      | Size    |  ________ mm  | |      | Size   |  ________ dd  | | | | ##
        ##             |       |      |         ----------------- |      |        ----------------- | | | ##
        ##             |       |      -----------------------------      ---------------------------- | | ##
	##             |       | hbox  ----------------------------                                   | | ##
	##             |       | YzInc |         Y++         Z++  |                   T++             | | ##
	##             |       |       ----------------------------                                   | | ##
	##             |       | hboxX ---------------------------- hboxP --------------------------- | | ##
	##             |       |       |    X-          X++       |       |     P-     c      P++   | | | ##
	##             |       |       ----------------------------       --------------------------- | | ##
	##             |       | hbox  ----------------------------                                   | | ##
	##             |       | YzDec |         Y-          Z-   |                   T-              | | ##
	##             |       |       ----------------------------                                   | | ##
	##             |       ------------------------------------------------------------------------ | ##
	##             | hbox  ------------------------------------------------------------------------ | ##
	##             | Extra |  Enable Motors   Disable Motors   Record Position   Home   Set Home  | | ##
	##             |       ------------------------------------------------------------------------ | ##
        ##             ---------------------------------------------------------------------------------- ##
        ##                                                                                                ##
        ####################################################################################################
        vboxPositioning = wx.BoxSizer(wx.VERTICAL)
        self.hboxCameraInfo = wx.BoxSizer()
        vboxPositioning.Add(self.hboxCameraInfo, 0.5, wx.EXPAND)
        
        positionLabel = wx.StaticText(self, wx.ID_ANY, label = 'Positioning', style = wx.ALIGN_LEFT)
        positionLabel.SetFont(self.font)
        vboxPositioning.Add(positionLabel, 0.5, flag = wx.BOTTOM|wx.TOP, border = 10)
        
        hboxTop = wx.BoxSizer()
        self.masterCombo = wx.ComboBox(self, wx.ID_ANY, choices = [])
        hboxTop.Add(self.masterCombo)
        self.setCenterBtn = wx.Button(self, wx.ID_ANY, label = 'Set Center')
        hboxTop.Add(self.setCenterBtn, 1, flag = wx.LEFT, border = 5)
        
        self.setCenterBtn = wx.Button(self, wx.ID_ANY, label = 'Refresh From COPIS')
        hboxTop.Add(self.setCenterBtn)
        sld = wx.Slider(self, maxValue = 500, style = wx.SL_HORIZONTAL)
        hboxTop.Add(sld)
        vboxPositioning.Add(hboxTop, 0.5 , flag = wx.LEFT|wx.BOTTOM|wx.EXPAND, border = 15)

        hboxXyzpt = wx.BoxSizer()
        vboxXyz = wx.BoxSizer(wx.VERTICAL)
        xyzLabel = wx.StaticText(self, wx.ID_ANY, label = 'XYZ Increment Size', style = wx.ALIGN_LEFT)
        vboxXyz.Add(xyzLabel, 1, flag = wx.BOTTOM, border = 10)
        
        hboxXyzSize = wx.BoxSizer()
        self.xyzSc = wx.SpinCtrl(self, value = '0')
        self.xyzSc.SetRange(0, 100)
        hboxXyzSize.Add(self.xyzSc, 1, flag = wx.RIGHT|wx.BOTTOM, border = 5)
        mmLabel = wx.StaticText(self, wx.ID_ANY, label = 'mm', style = wx.ALIGN_LEFT)
        hboxXyzSize.Add(mmLabel)
        vboxXyz.Add(hboxXyzSize)
        
        hboxYzInc = wx.BoxSizer()
        self.yiBtn = wx.Button(self, wx.ID_ANY, label = 'Y++')
        self.yiBtn.axis = Axis.Y
        self.yiBtn.direction = Axis.Plus
        hboxYzInc.Add(self.yiBtn, 1, flag = wx.LEFT|wx.RIGHT, border = 55)
        self.yiBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.ziBtn = wx.Button(self, wx.ID_ANY, label = 'Z++')
        self.ziBtn.axis = Axis.Z
        self.ziBtn.direction = Axis.Plus
        hboxYzInc.Add(self.ziBtn)
        self.ziBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxXyz.Add(hboxYzInc)
        
        hboxX = wx.BoxSizer()
        self.xrBtn = wx.Button(self, wx.ID_ANY, label = 'X-')
        self.xrBtn.axis = Axis.X
        self.xrBtn.direction = Axis.Minus
        hboxX.Add(self.xrBtn)
        self.xrBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.xiBtn = wx.Button(self, wx.ID_ANY, label = 'X++')
        self.xiBtn.axis = Axis.X
        self.xiBtn.direction = Axis.Plus
        hboxX.Add(self.xiBtn, 1, flag = wx.LEFT, border = 20)
        self.xiBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxXyz.Add(hboxX)
        
        hboxYzDec = wx.BoxSizer()
        self.yrBtn = wx.Button(self, wx.ID_ANY, label = 'Y-')
        self.yrBtn.axis = Axis.Y
        self.yrBtn.direction = Axis.Minus
        hboxYzDec.Add(self.yrBtn, 1, flag = wx.LEFT|wx.RIGHT, border = 55)
        self.yrBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.zrBtn = wx.Button(self, wx.ID_ANY, label = 'Z-')
        self.zrBtn.axis = Axis.Z
        self.zrBtn.direction = Axis.Minus
        hboxYzDec.Add(self.zrBtn)
        self.zrBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxXyz.Add(hboxYzDec)
        hboxXyzpt.Add(vboxXyz)

        vboxPt = wx.BoxSizer(wx.VERTICAL)
        ptLabel = wx.StaticText(self, wx.ID_ANY, label = 'PT Increment Size', style = wx.ALIGN_LEFT)
        vboxPt.Add(ptLabel, 1, flag = wx.BOTTOM, border = 10)
        
        hboxPtSize = wx.BoxSizer()
        self.ptSc = wx.SpinCtrl(self, value = '0')
        self.ptSc.SetRange(0, 100)
        hboxPtSize.Add(self.ptSc, 1, flag = wx.RIGHT|wx.BOTTOM, border = 5)
        ddLabel = wx.StaticText(self, wx.ID_ANY, label = 'dd', style = wx.ALIGN_LEFT)
        hboxPtSize.Add(ddLabel)
        vboxPt.Add(hboxPtSize)
        self.tiBtn = wx.Button(self, wx.ID_ANY, label = 'T++')
        self.tiBtn.axis = Axis.T
        self.tiBtn.direction = Axis.Plus
        vboxPt.Add(self.tiBtn, 1, flag = wx.LEFT, border = 88)
        self.tiBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        
        hboxP = wx.BoxSizer()
        self.prBtn = wx.Button(self, wx.ID_ANY, label = 'P-')
        self.prBtn.axis = Axis.P
        self.prBtn.direction = Axis.Minus
        hboxP.Add(self.prBtn)
        self.prBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.cBtn = wx.Button(self, wx.ID_ANY, label = 'c')
        hboxP.Add(self.cBtn)
        self.piBtn = wx.Button(self, wx.ID_ANY, label = 'P++')
        self.piBtn.axis = Axis.P
        self.piBtn.direction = Axis.Plus
        hboxP.Add(self.piBtn)
        self.piBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxPt.Add(hboxP)
        self.trBtn = wx.Button(self, wx.ID_ANY, label = 'T-')
        self.trBtn.axis = Axis.T
        self.trBtn.direction = Axis.Minus
        vboxPt.Add(self.trBtn, 1, flag = wx.LEFT, border = 88)
        self.trBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        hboxXyzpt.Add(vboxPt)

        vboxPositioning.Add(hboxXyzpt, 1, flag = wx.LEFT, border = 15)

        hboxExtra = wx.BoxSizer()
        self.eMotorBtn = wx.Button(self, wx.ID_ANY, label = 'Enable Motors')
        hboxExtra.Add(self.eMotorBtn, 1, flag = wx.RIGHT, border = 10)
        self.dMotorBtn = wx.Button(self, wx.ID_ANY, label = 'Disable Motors')
        hboxExtra.Add(self.dMotorBtn, 1, flag = wx.RIGHT, border = 10)
        self.recordBtn = wx.Button(self, wx.ID_ANY, label = 'Record Position')
        hboxExtra.Add(self.recordBtn, 1, flag = wx.RIGHT, border = 10)
        self.homeBtn = wx.Button(self, wx.ID_ANY, label = 'Home')
        hboxExtra.Add(self.homeBtn, 1, flag = wx.RIGHT, border = 10)
        self.setHomeBtn = wx.Button(self, wx.ID_ANY, label = 'Set Home')
        hboxExtra.Add(self.setHomeBtn)
        vboxPositioning.Add(hboxExtra, 0.5, flag = wx.LEFT, border = 15)
        
        return vboxPositioning

    def InitCircularPathGenerator(self):
        ## LAYOUT

     	##################################################################################################
        ##                                                                                              ##
        ## hbox --------------------------------------------------------------------------------------- ##
        ##      | vbox1  ------------------------------  vbox2 --------------------  vbox3 ---------- | ##
	##      |        | Circular Path Generator    |        |  Take Photo at   |        | rpm:   | | ##
	##      |        | hbox   ------------------- |        |  Each Vertex     |        | X:     | | ##
	##      |        | Points | No.Points: ____ | |        |                  |        | Y:     | | ##
	##      |        |        ------------------- |        |  Generate Circle |        | Z:     | | ##
	##      |        | hbox   ------------------- |        |                  |        | P:     | | ##
	##      |        | Radius | Radius (mm): ___| |        |  Generate Sphere |        | T:     | | ##
	##      |        |        ------------------- |        --------------------        ---------- | ##
	##      |        | hbox   ------------------- |                                               | ##
	##      |        | StartX | Start X: ____   | |                                               | ##
	##      |        |        ------------------- |                                               | ##
	##      |        | hbox   ------------------- |                                               | ##
	##      |        | StartY | Start Y: ____   | |                                               | ##
	##      |        |        ------------------- |                                               | ##
	##      |        | hbox   ------------------- |                                               | ##
	##      |        | StartZ | Start Z: ____   | |                                               | ##
	##      |        |        ------------------- |                                               | ##
        ##      |        | hbox   ------------------- |                                               | ##
        ##      |        | Cameras| No. Cams: ____  | |                                               | ##
        ##      |        |        ------------------- |                                               | ##
        ##      |        ------------------------------                                               | ##
        ##      --------------------------------------------------------------------------------------- ##
        ##                                                                                              ##
        ##################################################################################################
        hbox = wx.BoxSizer()
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        cGeneratorLabel = wx.StaticText(self, wx.ID_ANY, label = 'Circular Path Generator', style = wx.ALIGN_LEFT)
        cGeneratorLabel.SetFont(self.font)
        vbox1.Add(cGeneratorLabel, 1, flag = wx.TOP|wx.BOTTOM, border = 5)
        hboxPoints = wx.BoxSizer()
        noPointsLabel = wx.StaticText(self, wx.ID_ANY, label = 'No. Points: ')
        hboxPoints.Add(noPointsLabel, 1, flag = wx.RIGHT, border = 5)
        self.noPointsSc = wx.SpinCtrl(self, value = '0')
        self.noPointsSc.SetRange(0, 100)
        hboxPoints.Add(self.noPointsSc)
        vbox1.Add(hboxPoints, 1, flag = wx.LEFT, border = 15)

        hboxRadius = wx.BoxSizer()
        radiusLabel = wx.StaticText(self, wx.ID_ANY, label = 'Radius (mm): ')
        hboxRadius.Add(radiusLabel, 1, flag = wx.RIGHT, border = 5)
        self.radiusSc = wx.SpinCtrl(self, value = '0')
        self.radiusSc.SetRange(0, 100)
        hboxRadius.Add(self.radiusSc)
        vbox1.Add(hboxRadius, 1, flag = wx.LEFT, border = 15)

        hboxStartX = wx.BoxSizer()
        startXLabel = wx.StaticText(self, wx.ID_ANY, label = 'Start X: ')
        hboxStartX.Add(startXLabel, 1, flag = wx.RIGHT, border = 5)
        self.startXSc = wx.SpinCtrl(self, value = '0')
        self.startXSc.SetRange(0, 100)
        hboxStartX.Add(self.startXSc)
        vbox1.Add(hboxStartX, 1, flag = wx.LEFT, border = 15)

        hboxStartY = wx.BoxSizer()
        startYLabel = wx.StaticText(self, wx.ID_ANY, label = 'Start Y: ')
        hboxStartY.Add(startYLabel, 1, flag = wx.RIGHT, border = 5)
        self.startYSc = wx.SpinCtrl(self, value = '0')
        self.startYSc.SetRange(0, 100)
        hboxStartY.Add(self.startYSc)
        vbox1.Add(hboxStartY, 1, flag = wx.LEFT, border = 15)

        hboxStartZ = wx.BoxSizer()
        startZLabel = wx.StaticText(self, wx.ID_ANY, label = 'Start Z: ')
        hboxStartZ.Add(startZLabel, 1, flag = wx.RIGHT, border = 5)
        self.startZSc = wx.SpinCtrl(self, value = '0')
        self.startZSc.SetRange(0, 100)
        hboxStartZ.Add(self.startZSc)
        vbox1.Add(hboxStartZ, 1, flag = wx.LEFT, border = 15)

        hboxCameras = wx.BoxSizer()
        noCamsLabel = wx.StaticText(self, wx.ID_ANY, label = 'No. Cams: ')
        hboxCameras.Add(noCamsLabel, 1, flag = wx.RIGHT, border = 5)
        self.noCamsSc = wx.SpinCtrl(self, value = '0')
        self.noCamsSc.SetRange(0, 100)
        hboxCameras.Add(self.noCamsSc)
        vbox1.Add(hboxCameras, 1, flag = wx.LEFT, border = 15)
        hbox.Add(vbox1)
        
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        self.vertextPhotoCb = wx.CheckBox(self, label = 'Take Photo at Each Vertex')
        vbox2.Add(self.vertextPhotoCb)
        self.generateCBtn = wx.Button(self, wx.ID_ANY, label = 'Generate Circle')
        vbox2.Add(self.generateCBtn, 1, flag = wx.TOP, border = 5)
        self.generateSBtn = wx.Button(self, wx.ID_ANY, label = 'Generate Sphere')
        vbox2.Add(self.generateSBtn, 1, flag = wx.TOP, border = 5)
        hbox.Add(vbox2, 1, flag = wx.TOP|wx.LEFT, border = 30)

        vbox3 = wx.BoxSizer(wx.VERTICAL)
        self.rpmLabel = wx.StaticText(self, wx.ID_ANY, label = 'rpm: ')
        vbox3.Add(self.rpmLabel, 1, flag = wx.BOTTOM, border = 10)
        self.xLabel = wx.StaticText(self, wx.ID_ANY, label = 'X: ')
        vbox3.Add(self.xLabel, 1, flag = wx.BOTTOM, border = 10)
        self.yLabel = wx.StaticText(self, wx.ID_ANY, label = 'Y: ')
        vbox3.Add(self.yLabel, 1, flag = wx.BOTTOM, border = 10)
        self.zLabel = wx.StaticText(self, wx.ID_ANY, label = 'Z: ')
        vbox3.Add(self.zLabel, 1, flag = wx.BOTTOM, border = 10)
        self.pLabel = wx.StaticText(self, wx.ID_ANY, label = 'P: ')
        vbox3.Add(self.pLabel, 1, flag = wx.BOTTOM, border = 10)
        self.tLabel = wx.StaticText(self, wx.ID_ANY, label = 'T: ')
        vbox3.Add(self.tLabel)
        hbox.Add(vbox3, 1, flag = wx.TOP|wx.LEFT, border = 30)
        
        return hbox

    def InitZStackAndCamControl(self):
        ## LAYOUT

        ##########################################################################################################
        ##                                                                                                      ##
        ## hbox ----------------------------------------------------------------------------------------------- ##
        ##      | vbox1  ----------------------------------  vbox2 ------------------------------------------ | ##
        ##      |        | Z Stack Generator              |        |  Camera Control                        | | ##
    	##      |        | hbox  ------------------------ |        |  hbox   ------------------------------ | | ##
	##      |        | Focal | No.Focal Steps: ____ | |        |  Remote | Remote   vboxAF  --------- | | | ##
	##      |        | Steps ------------------------ |        |         | Shutter  Shutter |  A/F  | | | | ##
	##      |        | hbox   -------------------     |        |         |                  |Shutter| | | | ##
	##      |        | StartZ | Start Z: ___    |     |        |         |                  --------- | | | ##
	##      |        |        -------------------     |        |         ------------------------------ | | ##
	##      |        | hbox ------------------------- |        | hboxUSB ---------------------------    | | ##
	##      |        | ZInc | Z Increment (mm): ____| |        |         | USB/PTP  vboxF -------- |    | | ##
	##      |        |      ------------------------- |        |         |                |  F-  | |    | | ##
	##      |        | ------------                   |        |         |                |  F++ | |    | | ##
	##      |        | | Generate |                   |        |         |                -------- |    | | ##
	##      |        | ------------                   |        |         ---------------------------    | | ##
	##      |        ----------------------------------        ------------------------------------------ | ##
        ##      ----------------------------------------------------------------------------------------------- ##
        ##                                                                                                      ##
        ##########################################################################################################
        hbox = wx.BoxSizer()
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        zGeneratorLabel = wx.StaticText(self, wx.ID_ANY, label = 'Z Stack Generator', style = wx.ALIGN_LEFT)
        zGeneratorLabel.SetFont(self.font)
        vbox1.Add(zGeneratorLabel, 1, flag = wx.TOP|wx.BOTTOM, border = 5)
        
        hboxFocalSteps = wx.BoxSizer()
        noFocalStepsLabel = wx.StaticText(self, wx.ID_ANY, label = 'No. Focal Steps: ')
        hboxFocalSteps.Add(noFocalStepsLabel)
        self.noFocalStepsSc = wx.SpinCtrl(self, value = '0')
        self.noFocalStepsSc.SetRange(0, 100)
        hboxFocalSteps.Add(self.noFocalStepsSc, 1, flag = wx.LEFT, border = 5)
        vbox1.Add(hboxFocalSteps, 1, flag = wx.LEFT, border = 15)
        
        hboxStartZ = wx.BoxSizer()
        startZLabel2 = wx.StaticText(self, wx.ID_ANY, label = 'Start Z: ')
        hboxStartZ.Add(startZLabel2)
        self.startZSc2 = wx.SpinCtrl(self, value = '0')
        self.startZSc2.SetRange(0, 100)
        hboxStartZ.Add(self.startZSc2, 1, flag = wx.TOP, border = 5)
        vbox1.Add(hboxStartZ, 1, flag = wx.LEFT, border = 15)
        
        hboxZInc = wx.BoxSizer()
        zIncrementLabel = wx.StaticText(self, wx.ID_ANY, label = 'Z Increment (mm): ')
        hboxZInc.Add(zIncrementLabel)
        self.zIncrementSc = wx.SpinCtrl(self, value = '0')
        self.zIncrementSc.SetRange(0, 100)
        hboxZInc.Add(self.zIncrementSc, flag = wx.TOP, border = 5)
        vbox1.Add(hboxZInc, 1, flag = wx.LEFT, border = 15)
        self.generateBtn = wx.Button(self, wx.ID_ANY, label = 'Generate')
        vbox1.Add(self.generateBtn, 1, flag = wx.TOP|wx.LEFT, border = 10)
        hbox.Add(vbox1)

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        cameraControlLabel = wx.StaticText(self, wx.ID_ANY, label = 'Camera Control', style = wx.ALIGN_LEFT)
        cameraControlLabel.SetFont(self.font)
        vbox2.Add(cameraControlLabel, 1, flag = wx.TOP|wx.BOTTOM, border = 5)

        hboxRemote = wx.BoxSizer()
        self.remoteRb = wx.RadioButton(self, label = 'Remote Shutter')
        hboxRemote.Add(self.remoteRb)

        vboxAFShutter = wx.BoxSizer(wx.VERTICAL)
        self.afBtn = wx.Button(self, wx.ID_ANY, label = 'A/F')
        vboxAFShutter.Add(self.afBtn)
        self.shutterBtn = wx.Button(self, wx.ID_ANY, label = 'Shutter')
        vboxAFShutter.Add(self.shutterBtn)
        hboxRemote.Add(vboxAFShutter, 1, flag = wx.LEFT, border = 5)
        vbox2.Add(hboxRemote)

        hboxUSB = wx.BoxSizer()
        self.usbRb = wx.RadioButton(self, label = 'USB/PTP')
        hboxUSB.Add(self.usbRb)
        
        vboxF = wx.BoxSizer(wx.VERTICAL)
        self.frBtn = wx.Button(self, wx.ID_ANY, label = 'F-')
        vboxF.Add(self.frBtn)
        self.fiBtn = wx.Button(self, wx.ID_ANY, label = 'F++')
        vboxF.Add(self.fiBtn)
        hboxUSB.Add(vboxF, 1, flag = wx.LEFT, border = 5)
        vbox2.Add(hboxUSB, 1, flag = wx.TOP, border = 5)
        
        hbox.Add(vbox2, 1, flag = wx.LEFT, border = 30)

        return hbox

    def OnAddCameraButton(self, event):
        if self.canvas == "":
            self.canvas = self.parent.GetWindow2().canvas
        x = float(self.xTc.GetValue()) / 100
        y = float(self.yTc.GetValue()) / 100
        z = float(self.zTc.GetValue()) / 100
        p = self.pTc.GetValue()
        t = self.tTc.GetValue()

        self.canvas.OnDrawCamera(x, y, z, p, t)
        ## get the camera added
        camera = self.parent.GetWindow2().canvas.cameras[-1]

        ## set the new camera option to positioning DDL
        cameraLabelTxt = "camera" + str(len(self.parent.GetWindow2().canvas.cameras))
        self.masterCombo.Append(cameraLabelTxt)

        ## Display camera name and color before "Positioning" label
        cameraLabel = wx.StaticText(self, wx.ID_ANY, label = cameraLabelTxt, style = wx.ALIGN_LEFT)
        cameraLabel.SetForegroundColour((0, 0, 0))
        cameraLabel.SetBackgroundColour((camera.r, camera.g, camera.b))
        self.hboxCameraInfo.Add(cameraLabel, 1, wx.SHAPED)
        self.hboxCameraInfo.Layout()
        self.Fit()

    def SetDialog(self, message):
        msg = wx.MessageDialog(self, message, "Confirm Exit", wx.OK)
        msg.ShowModal()
        msg.Destroy()

    def OnMove(self, event):
        if self.canvas == "":
            self.canvas = self.parent.GetWindow2().canvas
            
        cameraOption = self.masterCombo.GetSelection()
        if cameraOption != -1:
            axis = event.GetEventObject().axis
            direction = event.GetEventObject().direction
            if axis in [Axis.X, Axis.Y, Axis.Z]:
                size = self.xyzSc.GetValue() / 100
            else:
                size = self.ptSc.GetValue()
                
            if direction == Axis.Minus:
                size = -size
            self.canvas.cameras[cameraOption].onMove(axis, size)
            self.canvas.OnDraw()
        else:
            self.SetDialog("Please select the camera to control")
        

class RightPanel(wx.Panel):
    def __init__(self, parent):
        super(RightPanel, self).__init__(parent)
        self.parent = parent
        self.InitPanel()

    def InitPanel(self):
        ## LAYOUT

	#################################################################################################
        ##                                                                                             ##
        ## vbox  ------------------------------------------------------------------------------------- ##
        ## Right | --------------------------------------------------------------------------------- | ##
	##       | |                                                                               | | ##
	##       | |                                                                               | | ##
	##       | |                                                                               | | ##
	##       | |                                 C A N V A S                                   | | ##
        ##       | |                                                                               | | ##
        ##       | |                                                                               | | ##
        ##       | |                                                                               | | ##
        ##       | |                                                                               | | ##
        ##       | --------------------------------------------------------------------------------- | ##
        ##       | hbox   -------------------------------------------------------------------------- | ##
        ##       | Bottom | Online  vbox ------------------------------------- vbox -------------- | | ##
        ##       |        |         Cmd  | --------------------------------- | Btns |     Up     | | | ##
        ##       |        |              | |                               | |      |    Down    | | | ##
        ##       |        |              | |                               | |      |            | | | ##
        ##       |        |              | |                               | |      |   Replace  | | | ##
	##       |        |              | |          C O M M A N D        | |      |   Delete   | | | ##
	##       |        |              | |                               | |      | Delete All | | | ##
	##       |        |              | |                               | |      |            | | | ##
	##       |        |              | |                               | |      |Save To File| | | ##
	##       |        |              | --------------------------------- |      |  Send All  | | | ##
	##       |        |              | hbox   -------------------------- |      |  Send Sel  | | | ##
	##       |        |              | AddCmd | __________________ Add | |      -------------- | | ##
	##       |        |              |        -------------------------- |                     | | ##
	##       |        |              -------------------------------------                     | | ##
	##       |        -------------------------------------------------------------------------- | ##
        ##       ------------------------------------------------------------------------------------- ##
        ##                                                                                             ##
        #################################################################################################
        vboxRight = wx.BoxSizer(wx.VERTICAL)
        self.canvas = Canvas(self)
        self.canvas.SetMinSize((200, 200))
        vboxRight.Add(self.canvas, 2, wx.EXPAND)

        hboxBottom = wx.BoxSizer()
        self.onlineCb = wx.CheckBox(self, label = 'Online')
        hboxBottom.Add(self.onlineCb, 0.5, flag = wx.LEFT|wx.TOP|wx.RIGHT, border = 10)
        
        vboxCmd = wx.BoxSizer(wx.VERTICAL)
        self.cmd = wx.ListBox(self, style = wx.LB_SINGLE)
        vboxCmd.Add(self.cmd, 1, wx.EXPAND)

        hboxAddCmd = wx.BoxSizer()
        self.cmdWriter = wx.TextCtrl(self)
        hboxAddCmd.Add(self.cmdWriter, 1, wx.EXPAND)
        self.addBtn = wx.Button(self, wx.ID_ANY, label = 'Add')
        self.addBtn.Bind(wx.EVT_BUTTON, self.OnAddCommand)
        hboxAddCmd.Add(self.addBtn)
        vboxCmd.Add(hboxAddCmd, 0.5, wx.EXPAND)
        hboxBottom.Add(vboxCmd, 2, wx.EXPAND)

        vboxBtns = wx.BoxSizer(wx.VERTICAL)
        self.upBtn = wx.Button(self, wx.ID_ANY, label = 'Up')
        self.upBtn.direction = 'up'
        self.upBtn.Bind(wx.EVT_BUTTON, self.OnMoveCommand)
        vboxBtns.Add(self.upBtn)
        self.downBtn = wx.Button(self, wx.ID_ANY, label = 'Down')
        self.downBtn.direction = 'down'
        self.downBtn.Bind(wx.EVT_BUTTON, self.OnMoveCommand)
        vboxBtns.Add(self.downBtn)
        self.replaceBtn = wx.Button(self, wx.ID_ANY, label = 'Replace')
        self.replaceBtn.Bind(wx.EVT_BUTTON, self.OnReplaceCommand)
        vboxBtns.Add(self.replaceBtn, 1, flag = wx.TOP, border = 30)
        self.deleteBtn = wx.Button(self, wx.ID_ANY, label = 'Delete')
        self.deleteBtn.size = 'single'
        self.deleteBtn.Bind(wx.EVT_BUTTON, self.OnDeleteCommand)
        vboxBtns.Add(self.deleteBtn)
        self.deleteAllBtn = wx.Button(self, wx.ID_ANY, label = 'Delete All')
        self.deleteAllBtn.size = 'all'
        self.deleteAllBtn.Bind(wx.EVT_BUTTON, self.OnDeleteCommand)
        vboxBtns.Add(self.deleteAllBtn)
        self.saveToFileBtn = wx.Button(self, wx.ID_ANY, label = 'Save To File')
        vboxBtns.Add(self.saveToFileBtn, 1, flag = wx.TOP, border = 30)
        self.sendAllBtn = wx.Button(self, wx.ID_ANY, label = 'Send All')
        vboxBtns.Add(self.sendAllBtn)
        self.sendSelBtn = wx.Button(self, wx.ID_ANY, label = 'Send Sel')
        vboxBtns.Add(self.sendSelBtn)
        hboxBottom.Add(vboxBtns)
        vboxRight.Add(hboxBottom, 1, wx.EXPAND)

        self.SetSizerAndFit(vboxRight)

    def OnAddCommand(self, event):
        cmd = self.cmdWriter.GetValue()
        if cmd != "":
            self.cmd.Append(cmd)
            self.cmdWriter.SetValue("")

    def OnMoveCommand(self, event):
        selected = self.cmd.GetStringSelection()
        
        if selected != "":
            direction = event.GetEventObject().direction
            index = self.cmd.GetSelection()
            self.cmd.Delete(index)
            
            if direction == "up":
                index -= 1
            else:
                index += 1

            self.cmd.InsertItems([selected], index)
            
    def SetDialog(self, message):
        msg = wx.MessageDialog(self, message, "Confirm Exit", wx.OK)
        msg.ShowModal()
        msg.Destroy()

    def OnReplaceCommand(self, event):
        selected = self.cmd.GetSelection()

        if selected != -1:
            replacement = self.cmdWriter.GetValue()
            
            if replacement != "":
                self.cmd.SetString(selected, replacement)
                self.cmdWriter.SetValue("")
            else:
                self.SetDialog("Please type command to replace.")
        else:
            self.SetDialog("Please select the command to replace.")

    def OnDeleteCommand(self, event):
        size = event.GetEventObject().size
        if size == "single":
            index = self.cmd.GetSelection()
            if index != -1:
                self.cmd.Delete(index)
            else:
                self.SetDialog("Please select the command to delete.")
        else:
            self.cmd.Clear()
        

class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs, style = wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE, title = "COPIS")

        ## set minimum size to show whole interface properly
        self.SetMinSize(wx.Size(1352, 850))

        ## initialize menu bar
        self.InitMenuBar()

        ## initialize tool bar
        self.InitToolBar()

        ## initialize status bar
        self.InitStatusBar()

        ## split the window in a half
        self.splitter = wx.SplitterWindow(self)
        self.panelLeft = LeftPanel(self.splitter)
        self.panelRight = RightPanel(self.splitter)

        self.splitter.SplitVertically(self.panelLeft, self.panelRight)
        self.panelLeft.SetFocus()
        
        self.Centre()
        

    def InitToolBar(self):
        toolbar = self.CreateToolBar()

        ## undo, redo and refresh buttons
        ## TO DO: create and bind functions
        undoImg = wx.Image('img/undo.png')
        undoImg = undoImg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        toolbar.AddTool(1, 'Undo', wx.BitmapFromImage(undoImg))

        redoImg = wx.Image('img/redo.png')
        redoImg = redoImg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        toolbar.AddTool(1, 'Redo', wx.BitmapFromImage(redoImg))

        refreshImg = wx.Image('img/refresh.png')
        refreshImg = refreshImg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        toolbar.AddTool(1, 'Refresh', wx.BitmapFromImage(refreshImg))

        ## port and baud options
        ## TO DO: it should detect ports and baud options when the machine is connected
        toolbar.AddStretchableSpace()
        portLabel = wx.StaticText(toolbar, id = wx.ID_ANY, label = "Port: ", style = wx.ALIGN_LEFT)
        toolbar.AddControl(portLabel)
        portCombo = wx.ComboBox(toolbar, wx.ID_ANY, value = "", choices = ["Port 1", "Port 2", "Port 3"])
        toolbar.AddControl(portCombo)
        baudLabel = wx.StaticText(toolbar, id = wx.ID_ANY, label = " Baud: ", style = wx.ALIGN_RIGHT)
        toolbar.AddControl(baudLabel)
        baudCombo = wx.ComboBox(toolbar, wx.ID_ANY, value = "", choices = ["Baud 1", "Baud 2", "Baud 3"])
        toolbar.AddControl(baudCombo)

        ## connect and disconnect to the port buttons
        ## TO DO: create and bind functions
        connectBtn = wx.Button(toolbar, wx.ID_ANY, label = "Connect")
        toolbar.AddControl(connectBtn)

        disconnectBtn = wx.Button(toolbar, wx.ID_ANY, label = "Disconnect")
        toolbar.AddControl(disconnectBtn)

        ## play, pause and stop buttons to animate the commands
        ## TO DO: create and bind functions
        toolbar.AddStretchableSpace()
        playImg = wx.Image('img/play.png')
        playImg = playImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        toolbar.AddTool(1, 'Play', wx.BitmapFromImage(playImg))

        pauseImg = wx.Image('img/pause.png')
        pauseImg = pauseImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        toolbar.AddTool(1, 'Pause', wx.BitmapFromImage(pauseImg))
        
        stopImg = wx.Image('img/stop.png')
        stopImg = stopImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        toolbar.AddTool(1, 'Stop', wx.BitmapFromImage(stopImg))

        ## import file
        ## TO DO: create and bind function to "Browse" button
        toolbar.AddStretchableSpace()
        fileLabel = wx.StaticText(toolbar, id = wx.ID_ANY, label = "File: ", style = wx.ALIGN_LEFT)
        toolbar.AddControl(fileLabel)
        fileBox = wx.TextCtrl(toolbar)
        toolbar.AddControl(fileBox)
        loadBtn = wx.Button(toolbar, wx.ID_ANY, label = "Browse")
        toolbar.AddControl(loadBtn)

        ## setting options
        ## TO DO: figure out what settings are needed and create a popup box with setting options
        toolbar.AddStretchableSpace()
        settingImg = wx.Image('img/setting.png')
        settingImg = settingImg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        toolbar.AddTool(1, 'Setting', wx.BitmapFromImage(settingImg))
        
        toolbar.Realize()

    def InitMenuBar(self):
        menubar = wx.MenuBar()

        ## view menu that shows view options
        viewMenu = wx.Menu()
        ## add statusbar show option to view menu
        self.shst = viewMenu.Append(wx.ID_ANY, 'Show statusbar', 'Show Statusbar', kind=wx.ITEM_CHECK)
        ## set default true
        viewMenu.Check(self.shst.GetId(), True)
        self.Bind(wx.EVT_MENU, self.ToggleStatusBar, self.shst)

        ## add view menu to menu bar
        menubar.Append(viewMenu, '&View')
        ## set menu bar to the frame
        self.SetMenuBar(menubar)

    def InitStatusBar(self):
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('Ready')

    def OnQuit(self, e):
        self.Close()

    def ToggleStatusBar(self, e):
        if self.shst.IsChecked():
            self.statusbar.Show()
        else:
            self.statusbar.Hide()

    def OnRightDown(self, e):
        self.PopupMenu(MyPopupMenu(self), e.GetPosition())
        

class COPISApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None)
        frame.Show()
        return True
    

if __name__ == '__main__':
    app = COPISApp()
    app.MainLoop()
