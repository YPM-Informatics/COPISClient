#!/usr/bin/env python3
"""Camera3D class."""

import math
import numpy as np
from enums import CamAxis, CamMode
import threading

import wx
from OpenGL.GL import *
from OpenGL.GLU import *


class Camera3D():
    def __init__(self, id, x, y, z, b, c):
        self._dirty = False  # dirty flag to track when we need to re-render the camera
        self.is_selected = False

        self._id = id
        self._x = float(x)
        self._y = float(y)
        self._z = float(z)
        self._b = float(b)
        self._c = float(c)

        self.start = (self._x, self._y, self._z, self._b, self._c)
        self.mode = CamMode.NORMAL

        self.angle = 0
        self.rotationVector = []

        self.trans = False
        self.nIncre = 0
        self.increx = 0
        self.increy = 0
        self.increz = 0

    def render(self):
        """Render camera."""
        ## Set color based on selection
        if self.is_selected:
            color = [75, 230, 150]
        else:
            hue = 125 - self._id
            color = [hue, hue, hue]

        glPushMatrix()
        glTranslatef(self._x, self._y, self._z)
        if self.mode == CamMode.NORMAL:
            if self._b != 0.0:
                glRotatef(self._b, 0, 0, 1)
            if self._c != 0.0:
                glRotatef(self._c, 0, 1, 0)
        elif self.mode == CamMode.ROTATE:
            glRotatef(self.angle, *self.rotationVector)

        if self.trans:
            self.translate()
            self._dirty = True

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

    @property
    def get_id(self):
        return self._id

    @property
    def get_dirty(self):
        return self._dirty

    def getRotationAngle(self, v1, v2):
        v1_u = self.getUnitVector(v1)
        v2_u = self.getUnitVector(v2)
        return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1, 1)))

    def getUnitVector(self, vector):
        return vector / np.linalg.norm(vector)

    def onFocusCenter(self):
        self.mode = CamMode.ROTATE
        cameraCenterPoint = (self._x, self._y, self._z)
        currentFacingPoint = (self._x - 0.5, self._y, self._z)
        desirableFacingPoint = (0.0, 0.0, 0.0)

        v1 = np.subtract(currentFacingPoint, cameraCenterPoint)
        v2 = np.subtract(desirableFacingPoint, cameraCenterPoint)

        self.angle = self.getRotationAngle(v1, v2)
        self.rotationVector = np.cross(self.getUnitVector(v1), self.getUnitVector(v2))
        self.render()

    def getZbyAngle(self, angle):
        return np.sqrt(np.square(0.5 / angle) - 0.25)

    def on_move(self, axis, amount):
        if axis in CamAxis and amount != 0:
            if axis == CamAxis.X:
                self._x += amount
            elif axis == CamAxis.Y:
                self._y += amount
            elif axis == CamAxis.Z:
                self._z += amount
            elif axis == CamAxis.B:
                self._b += amount
            elif axis == CamAxis.C:
                self._c += amount

    def translate(self, newx=0, newy=0, newz=0):
        #Initialize nIncre and increxyz, skip if already initialized
        if not self.trans:
            dx = round(newx - self._x, 2)
            dy = round(newy - self._y, 2)
            dz = round(newz - self._z, 2)

            maxd = max(dx, dy, dz)
            scale = maxd/0.01

            self.nIncre = scale
            self.increx = dx/scale
            self.increy = dy/scale
            self.increz = dz/scale

            #Setting trans to true allows this function to be called on cam.render
            self.trans = True

        if self.nIncre > 0:
            self._x += self.increx
            self._y += self.increy
            self._z += self.increz

            self.nIncre -= 1
        else:
            self._x = round(self._x, 2)
            self._y = round(self._y, 2)
            self._z = round(self._z, 2)
            self.trans = False

        self._dirty = True
