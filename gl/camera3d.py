#!/usr/bin/env python3
"""Camera3D class."""

import math
import numpy as np
from enums import CamAxis, CamMode

import wx
from OpenGL.GL import *
from OpenGL.GLU import *


class Camera3D():
    def __init__(self, cam_id, x, y, z, b, c):
        self._dirty = False  # dirty flag to track when we need to re-render the camera
        self.is_selected = False

        self._cam_id = cam_id
        self._x = float(x)
        self._y = float(y)
        self._z = float(z)
        self._b = float(b)
        self._c = float(c)
        self._scale = 10

        self.start = (self._x, self._y, self._z, self._b, self._c)
        self.mode = CamMode.NORMAL

        self._angle = 0
        self._rotation_vector = []

        self.trans = False
        self.n_increment = 0
        self.increment_x = 0
        self.increment_y = 0
        self.increment_z = 0

    def render(self):
        """Render camera."""
        # Set color based on selection
        if self.is_selected:
            color = (75, 230, 150)
        else:
            color = (125, 125, 125)

        scale = self._scale

        glPushMatrix()
        glTranslatef(self._x, self._y, self._z)
        if self.mode == CamMode.NORMAL:
            if self._b != 0.0:
                glRotatef(self._b, 0, 0, 1)
            if self._c != 0.0:
                glRotatef(self._c, 0, 1, 0)
        elif self.mode == CamMode.ROTATE:
            glRotatef(self._angle, *self._rotation_vector)

        if self.trans:
            self.translate()
            self._dirty = True

        glBegin(GL_QUADS)

        # bottom
        glColor3ub(*color)
        glVertex3f(-0.25 * scale, -0.5 * scale, -0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, -0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, 0.5 * scale)
        glVertex3f(-0.25 * scale, -0.5 * scale, 0.5 * scale)

        # right
        glVertex3f(-0.25 * scale, 0.5 * scale, -0.5 * scale)
        glVertex3f(0.25 * scale, 0.5 * scale, -0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, -0.5 * scale)
        glVertex3f(-0.25 * scale, -0.5 * scale, -0.5 * scale)

        # top
        glVertex3f(-0.25 * scale, 0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, 0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, 0.5 * scale, -0.5 * scale)
        glVertex3f(-0.25 * scale, 0.5 * scale, -0.5 * scale)

        # left
        glVertex3f(-0.25 * scale, -0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, 0.5 * scale, 0.5 * scale)
        glVertex3f(-0.25 * scale, 0.5 * scale, 0.5 * scale)

        # back
        glVertex3f(0.25 * scale, 0.5 * scale, -0.5 * scale)
        glVertex3f(0.25 * scale, 0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, -0.5 * scale)

        # front
        glVertex3f(-0.25 * scale, -0.5 * scale, -0.5 * scale)
        glVertex3f(-0.25 * scale, -0.5 * scale, 0.5 * scale)
        glVertex3f(-0.25 * scale, 0.5 * scale, 0.5 * scale)
        glVertex3f(-0.25 * scale, 0.5 * scale, -0.5 * scale)
        glEnd()

        glPushMatrix()

        # lens
        glColor3ub(*[x - 15 for x in color])
        glTranslated(-0.5 * scale, 0.0, 0.0)
        quadric = gluNewQuadric()
        glRotatef(90.0, 0.0, 1.0, 0.0)
        gluCylinder(quadric, 0.25 * scale, 0.25 * scale, 0.3 * scale, 16, 16)
        gluDeleteQuadric(quadric)

        # cap
        glColor3ub(*[x - 25 for x in color])
        circle_quad = gluNewQuadric()
        gluQuadricOrientation(circle_quad, GLU_INSIDE)
        gluDisk(circle_quad, 0.0, 0.25 * scale, 16, 1)
        gluDeleteQuadric(circle_quad)

        glPopMatrix()
        glPopMatrix()

    def render_for_picking(self):
        """Render camera for picking pass."""
        scale = self._scale

        glPushMatrix()
        glTranslatef(self._x, self._y, self._z)
        if self.mode == CamMode.NORMAL:
            if self._b != 0.0:
                glRotatef(self._b, 0, 0, 1)
            if self._c != 0.0:
                glRotatef(self._c, 0, 1, 0)
        elif self.mode == CamMode.ROTATE:
            glRotatef(self._angle, *self._rotation_vector)

        glBegin(GL_QUADS)

        # bottom
        glVertex3f(-0.25 * scale, -0.5 * scale, -0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, -0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, 0.5 * scale)
        glVertex3f(-0.25 * scale, -0.5 * scale, 0.5 * scale)

        # right
        glVertex3f(-0.25 * scale, 0.5 * scale, -0.5 * scale)
        glVertex3f(0.25 * scale, 0.5 * scale, -0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, -0.5 * scale)
        glVertex3f(-0.25 * scale, -0.5 * scale, -0.5 * scale)

        # top
        glVertex3f(-0.25 * scale, 0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, 0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, 0.5 * scale, -0.5 * scale)
        glVertex3f(-0.25 * scale, 0.5 * scale, -0.5 * scale)

        # left
        glVertex3f(-0.25 * scale, -0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, 0.5 * scale, 0.5 * scale)
        glVertex3f(-0.25 * scale, 0.5 * scale, 0.5 * scale)

        # back
        glVertex3f(0.25 * scale, 0.5 * scale, -0.5 * scale)
        glVertex3f(0.25 * scale, 0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, 0.5 * scale)
        glVertex3f(0.25 * scale, -0.5 * scale, -0.5 * scale)

        # front
        glVertex3f(-0.25 * scale, -0.5 * scale, -0.5 * scale)
        glVertex3f(-0.25 * scale, -0.5 * scale, 0.5 * scale)
        glVertex3f(-0.25 * scale, 0.5 * scale, 0.5 * scale)
        glVertex3f(-0.25 * scale, 0.5 * scale, -0.5 * scale)
        glEnd()
        glPushMatrix()

        # lens
        glTranslated(-0.5 * scale, 0.0, 0.0)
        quadric = gluNewQuadric()
        glRotatef(90.0, 0.0, 1.0, 0.0)
        gluCylinder(quadric, 0.25 * scale, 0.25 * scale, 0.3 * scale, 16, 16)
        gluDeleteQuadric(quadric)

        # cap
        circle_quad = gluNewQuadric()
        gluQuadricOrientation(circle_quad, GLU_INSIDE)
        gluDisk(circle_quad, 0.0, 0.25 * scale, 16, 1)
        gluDeleteQuadric(circle_quad)

        glPopMatrix()
        glPopMatrix()

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value

    @property
    def cam_id(self):
        return self._cam_id

    @cam_id.setter
    def cam_id(self, value):
        self._cam_id = value

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    def get_rotation_angle(self, v1, v2):
        v1_u = self.get_unit_vector(v1)
        v2_u = self.get_unit_vector(v2)
        return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1, 1)))

    def get_unit_vector(self, vector):
        return vector / np.linalg.norm(vector)

    def on_focus_center(self):
        self.mode = CamMode.ROTATE
        camera_center = (self._x, self._y, self._z)
        current_facing = (self._x - 0.5, self._y, self._z)
        target_facing = (0.0, 0.0, 0.0)

        v1 = np.subtract(current_facing, camera_center)
        v2 = np.subtract(target_facing, camera_center)

        self._angle = self.get_rotation_angle(v1, v2)
        self._rotation_vector = np.cross(self.get_unit_vector(v1), self.get_unit_vector(v2))
        self.render()

    def get_z_by_angle(self, angle):
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
        # initialize nIncre and increxyz, skip if already initialized
        if self.trans:
            return

        dx = round(newx - self._x, 2)
        dy = round(newy - self._y, 2)
        dz = round(newz - self._z, 2)

        maxd = max(dx, dy, dz)
        scale = maxd / 0.01

        self.nIncre = scale
        self.increx = dx / scale
        self.increy = dy / scale
        self.increz = dz / scale

        # setting trans to true allows this function to be called on cam.render
        self.trans = True

        if self.n_increment > 0:
            self._x += self.increment_x
            self._y += self.increment_y
            self._z += self.increment_z

            self.n_increment -= 1
        else:
            self._x = round(self._x, 2)
            self._y = round(self._y, 2)
            self._z = round(self._z, 2)
            self.trans = False

        self._dirty = True
