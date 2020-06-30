#!/usr/bin/env python3
"""TODO: Fill in docstring"""

import math
import numpy as np
from enums import Axis

import wx
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


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