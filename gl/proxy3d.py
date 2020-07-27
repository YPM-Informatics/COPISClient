#!/usr/bin/env python3
"""Proxy3D class"""

from OpenGL.GL import *
from OpenGL.GLU import *

class Proxy3D():
    def __init__(self, style, dimensions, color):
        self._style = style

        if self._style == 'Sphere':
            self._quadric = gluNewQuadric()

            self._radius = dimensions[0]
            self._color = color
    
        elif self._style == 'Cylinder':
            self._quadric = gluNewQuadric()
            self._radius = dimensions[0]
            self._height = dimensions[1]
            self._color = color
            
        elif self._style == 'Cube':
            self._width = dimensions[0]
            self._length = dimensions[1]
            self._height = dimensions[2]
            self._color = color

    def render(self):
        
        if self._style == 'Sphere':
            glColor3ub(*self._color)
            gluSphere(self._quadric, self._radius, 32, 32)
        
        elif self._style == 'Cylinder':

            glColor3ub(*self._color)
            glTranslate(0.0, 0.0, self._height / -2)
            gluCylinder(self._quadric, self._radius, self._radius, self._height, 32, 4)

            disk_quad = gluNewQuadric()
            gluQuadricOrientation(disk_quad, GLU_INSIDE)
            gluDisk(disk_quad, 0.0, self._radius, 32, 1)
            gluDeleteQuadric(disk_quad)

            glPushMatrix()

            glTranslate(0.0, 0.0,self._height, )
            disk_quad2 = gluNewQuadric()
            gluQuadricOrientation(disk_quad2, GLU_OUTSIDE)
            gluDisk(disk_quad2, 0.0, self._radius, 32, 1)
            gluDeleteQuadric(disk_quad2)

            glPopMatrix()

        elif self._style == 'Cube':
            hw = self._width / 2
            hl = self._length / 2
            hh = self._height / 2

            glBegin(GL_QUADS)

            # Bottom
            glColor3ub(*self._color)
            glVertex3f(-hw, -hh, -hl)
            glVertex3f( hw, -hh, -hl)
            glVertex3f( hw, -hh,  hl)
            glVertex3f(-hw, -hh,  hl)

            # Top
            glVertex3f(-hw, hh,  hl)
            glVertex3f( hw, hh,  hl)
            glVertex3f( hw, hh, -hl)
            glVertex3f(-hw, hh, -hl)

            # Back
            glVertex3f(-hw,  hh, -hl)
            glVertex3f( hw,  hh, -hl)
            glVertex3f( hw, -hh, -hl)
            glVertex3f(-hw, -hh, -hl)

            # Front
            glVertex3f(-hw, -hh, hl)
            glVertex3f( hw, -hh, hl)
            glVertex3f( hw,  hh, hl)
            glVertex3f(-hw,  hh, hl)

            # Right
            glVertex3f( hw,  hh, -hl)
            glVertex3f( hw,  hh,  hl)
            glVertex3f( hw, -hh,  hl)
            glVertex3f( hw, -hh, -hl)

            # Left
            glVertex3f(-hw, -hh, -hl)
            glVertex3f(-hw, -hh,  hl)
            glVertex3f(-hw,  hh,  hl)
            glVertex3f(-hw,  hh, -hl)

            glEnd()

    @property
    def style(self):
        return self._style

    @style.setter
    def style(self, value):
        self._style = value

    @property
    def dimensions(self):
        if self._style == 'Sphere':
            return [self._radius]
        elif self._style == 'Cylinder':
            return [self._radius, self._height]
        elif self._style == 'Cube':
            return [self._width, self._length, self._height]
    
    @dimensions.setter
    def dimensions(self, value):
        if self._style == 'Sphere':
            self._radius = value[0]
        elif self._style == 'Cylinder':
            self._radius = value[0]
            self._height = value[1]
        elif self._style == 'Cube':
            self._width = value[0]
            self._length = value[1]
            self._height = value[2]

    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, value):
        self._color = value 


