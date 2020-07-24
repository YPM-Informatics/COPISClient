#!/usr/bin/env python3
"""Bed3D class and associated classes."""

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from gl.proxy3d import Proxy3D


class _Axes():

    origin = (0.0, 0.0, 0.0)

    def __init__(self, build_dimensions):
        self._build_dimensions = build_dimensions
        dist = 0.5 * (build_dimensions[1] + max(build_dimensions[0], build_dimensions[2]))
        self._arrow_base_radius = dist / 75.0
        self._arrow_length = 2.5 * self._arrow_base_radius
        self._quadric = gluNewQuadric()
        gluQuadricDrawStyle(self._quadric, GLU_FILL)

    def render(self):
        """Render colored axes and arrows."""
        if self._quadric is None:
            return

        x = self._build_dimensions[0] - self._build_dimensions[3], self._build_dimensions[3]
        y = self._build_dimensions[1] - self._build_dimensions[4], self._build_dimensions[4]
        z = self._build_dimensions[2] - self._build_dimensions[5], self._build_dimensions[5]

        verts = np.array([
            x[0], 0, 0, -x[1], 0, 0,
            0, y[0], 0, 0, -y[1], 0,
            0, 0, z[0], 0, 0, -z[1]])
        colors = np.array([
            1.0, 0.0, 0.0, 1.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 1.0, 0.0, 0.0, 1.0])

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, verts)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawArrays(GL_LINES, 0, 6)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

        # x axis
        glColor3f(1.0, 0.0, 0.0)
        glPushMatrix()
        glTranslated(*self.origin)
        glRotated(90.0, 0.0, 1.0, 0.0)
        self._render_arrow(x[0])
        glPopMatrix()

        # y axis
        glColor3f(0.0, 1.0, 0.0)
        glPushMatrix()
        glTranslated(*self.origin)
        glRotated(-90.0, 1.0, 0.0, 0.0)
        self._render_arrow(y[0])
        glPopMatrix()

        # z axis
        glColor3f(0.0, 0.0, 1.0)
        glPushMatrix()
        glTranslated(*self.origin)
        self._render_arrow(z[0])
        glPopMatrix()

    def _render_arrow(self, length):
        glTranslated(0.0, 0.0, length)
        gluQuadricOrientation(self._quadric, GLU_OUTSIDE)
        gluCylinder(self._quadric, self._arrow_base_radius, 0.0, self._arrow_length, 32, 1)
        gluQuadricOrientation(self._quadric, GLU_INSIDE)
        gluDisk(self._quadric, 0.0, self._arrow_base_radius, 32, 1)

    def __delete__(self, _):
        if not self._quadric:
            gluDeleteQuadric(self._quadric)


class Bed3D():
    """Bed3D class."""
    color_light = 0.91
    color_dark = 0.72
    color_border = 0.40

    def __init__(self, build_dimensions, axes=True, bounding_box=True, every=100, subdivisions=10):
        if not all([0 <= build_dimensions[i+3] <= build_dimensions[i] for i in range(3)]):
            raise ValueError('build dimension origin out of range')

        self._build_dimensions = build_dimensions
        self._show_axes = axes
        self._show_bounding_box = bounding_box
        self._every = every
        self._subdivisions = subdivisions
        self._axes = _Axes(build_dimensions)

        self._initialized = False
        self._gridlines = None
        self._bounding_box = None

    def init(self):
        """Initialize vertices."""
        if self._initialized:
            return True

        if self._show_bounding_box:
            self.create_bounding_box()

        self.create_gridlines()

        self._initialized = True
        return True

    def render(self):
        """Render bed."""
        if not self.init():
            return

        glDisable(GL_LINE_SMOOTH)

        if self._show_axes:
            self._render_axes()

        if self._show_bounding_box:
            self._render_bounding_box()

        self._render_gridlines()

        glEnable(GL_LINE_SMOOTH)

    def create_gridlines(self):
        """Generate vertices and colors for bed gridlines."""
        x = self._build_dimensions[0] - self._build_dimensions[3], self._build_dimensions[3]
        z = self._build_dimensions[2] - self._build_dimensions[5], self._build_dimensions[5]
        step = self._every / self._subdivisions

        def darken(a):
            a[self._subdivisions-1::self._subdivisions] = self.color_dark
            a[-1] = self.color_border
            return a

        if self._show_axes:
            axes_verts = np.array([])
            axes_colors = np.array([])
        else:
            axes_verts = np.array([
                x[0], 0, 0, -x[1], 0, 0,
                0, 0, z[0], 0, 0, -z[1]])
            axes_colors = np.array([self.color_dark]).repeat(12)

        # gridlines parallel to x axis
        i = np.append(np.arange(-step, -z[1], -step), -z[1])
        j = np.append(np.arange(step, z[0], step), z[0])
        k = np.concatenate([i, j])
        x_verts = np.zeros(k.size * 6)
        x_verts[2::3] = k.repeat(2)
        x_verts[0::6] = -x[1]
        x_verts[3::6] = x[0]
        x_colors = np.concatenate([
            darken(np.full(i.size, self.color_light)),
            darken(np.full(j.size, self.color_light))]).repeat(6)

        # gridlines parallel to z axis
        i = np.append(np.arange(-step, -x[1], -step), -x[1])
        j = np.append(np.arange(step, x[0], step), x[0])
        k = np.concatenate([i, j])
        z_verts = np.zeros(k.size * 6)
        z_verts[0::3] = k.repeat(2)
        z_verts[2::6] = -z[1]
        z_verts[5::6] = z[0]
        z_colors = np.concatenate([
            darken(np.full(i.size, self.color_light)),
            darken(np.full(j.size, self.color_light))]).repeat(6)

        self._gridlines = (
            np.concatenate([axes_verts, x_verts, z_verts]),
            np.concatenate([axes_colors, x_colors, z_colors]))

    def create_bounding_box(self):
        """Generate vertices and indices for bed bounding box."""
        x = self._build_dimensions[0] - self._build_dimensions[3], self._build_dimensions[3]
        y = self._build_dimensions[1] - self._build_dimensions[4], self._build_dimensions[4]
        z = self._build_dimensions[2] - self._build_dimensions[5], self._build_dimensions[5]

        # 8 corners
        vertices = np.array([
            x[0], y[0], z[0],
            x[0], -y[1], z[0],
            x[0], -y[1], -z[1],
            x[0], y[0], -z[1],
            -x[1], y[0], -z[1],
            -x[1], y[0], z[0],
            -x[1], -y[1], z[0],
            -x[1], -y[1], -z[1]])
        # 12 edges
        indices = np.array([
            0, 1, 1, 2, 2, 3, 3, 0,
            0, 5, 1, 6, 2, 7, 3, 4,
            4, 5, 5, 6, 6, 7, 7, 4])

        self._bounding_box = (vertices, indices)

    def _render_gridlines(self):
        if self._gridlines is None:
            return

        vertices, colors = self._gridlines
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, vertices)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawArrays(GL_LINES, 0, vertices.size // 3)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

    def _render_bounding_box(self):
        if self._bounding_box is None:
            return

        vertices, indices = self._bounding_box
        glColor3f(self.color_dark, self.color_dark, self.color_dark)
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, vertices)
        glDrawElements(GL_LINES, indices.size, GL_UNSIGNED_INT, indices)
        glDisableClientState(GL_VERTEX_ARRAY)

    def _render_axes(self):
        if self._axes is None:
            return

        self._axes.render()

    @property
    def show_axes(self):
        return self._show_axes

    @show_axes.setter
    def show_axes(self, value):
        self._show_axes = value
        self._initialized = False

    @property
    def show_bounding_box(self):
        return self._show_bounding_box

    @show_bounding_box.setter
    def show_bounding_box(self, value):
        self._show_bounding_box = value
        self._initialized = False