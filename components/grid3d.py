#!/usr/bin/env python3
"""Grid3D class and associated classes."""

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *


class _Axes():
    def __init__(self, build_dimensions):
        self._build_dimensions = build_dimensions
        self._quadric = gluNewQuadric()
        gluQuadricDrawStyle(self._quadric, GLU_FILL)

    def render(self):
        x = self._build_dimensions[0] - self._build_dimensions[3], self._build_dimensions[3]
        y = self._build_dimensions[1] - self._build_dimensions[4], self._build_dimensions[4]
        z = self._build_dimensions[2] - self._build_dimensions[5], self._build_dimensions[5]

        verts = np.array([
            x[0], 0, 0, -x[1], 0, 0,
            0, y[0], 0, 0, -y[1], 0,
            0, 0, z[0], 0, 0, -z[1]])
        colors = np.array([
            1.0, 0.0, 0.0, 1.0, 0.0, 0.0,   # red
            0.0, 1.0, 0.0, 0.0, 1.0, 0.0,   # green
            0.0, 0.0, 1.0, 0.0, 0.0, 1.0])  # blue

        glLineWidth(1.5)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        glVertexPointer(3, GL_FLOAT, 0, verts)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawArrays(GL_LINES, 0, 6)

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)
        glLineWidth(1.0)

    def __delete__(self):
        if not self._quadric:
            gluDeleteQuadric(self._quadric)


class Grid3D():
    def __init__(self, build_dimensions, axes=True, every=100, subdivisions=10):
        self._build_dimensions = build_dimensions
        self._show_axes = axes
        self._every = every
        self._subdivisions = subdivisions

        self._axes = _Axes(build_dimensions) if axes else None

        self._initialized = False
        self._vertices = None
        self._colors = None

    def init(self):
        if self._initialized:
            return True

        self.create()

        self._initialized = True
        return True

    def render(self):
        if not self.init():
            return

        if self._show_axes:
            self.render_axes()

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        glVertexPointer(3, GL_FLOAT, 0, self._vertices)
        glColorPointer(3, GL_FLOAT, 0, self._colors)
        glDrawArrays(GL_LINES, 0, self.get_vertices_count())

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

    def create(self):
        step = self._every / self._subdivisions

        x = self._build_dimensions[0] - self._build_dimensions[3], self._build_dimensions[3]
        y = self._build_dimensions[1] - self._build_dimensions[4], self._build_dimensions[4]
        z = self._build_dimensions[2] - self._build_dimensions[5], self._build_dimensions[5]

        light  = 0.90
        dark   = 0.72
        border = 0.40
        def darken(a):
            a[self._subdivisions-1::self._subdivisions] = dark
            a[-1] = border
            return a

        axes_verts = np.array([]) if self._show_axes else np.array([
            x[0], 0, 0, -x[1], 0, 0,
            0, y[0], 0, 0, -y[1], 0])
        axes_colors = np.array([]) if self._show_axes else np.array([dark]).repeat(12)

        # gridlines parallel to x axis
        i = np.append(np.arange(-step, -y[1], -step), -y[1])
        j = np.append(np.arange(step, y[0], step), y[0])
        k = np.concatenate([i, j])
        x_verts = np.zeros(k.size * 6)
        x_verts[1::3] = k.repeat(2)
        x_verts[0::3] = -x[1]
        x_verts[3::6] = x[0]
        x_colors = np.concatenate([
            darken(np.full(i.size, light)),
            darken(np.full(j.size, light))]).repeat(6)

        # gridlines parallel to y axis
        i = np.append(np.arange(-step, -x[1], -step), -x[1])
        j = np.append(np.arange(step, x[0], step), x[0])
        k = np.concatenate([i, j])
        y_verts = np.zeros(k.size * 6)
        y_verts[0::3] = k.repeat(2)
        y_verts[1::6] = -y[1]
        y_verts[4::6] = y[0]
        y_colors = np.concatenate([
            darken(np.full(i.size, light)),
            darken(np.full(j.size, light))]).repeat(6)

        self._vertices = np.concatenate([axes_verts, x_verts, y_verts])
        self._colors = np.concatenate([axes_colors, x_colors, y_colors])

    def render_axes(self):
        if not self._axes:
            return

        self._axes.render()

    def get_vertices_count(self):
        return self._vertices.size // 3 if self._vertices.size else 0

    def get_colors(self):
        return self._colors if self._colors.size > 0 else None

    def get_vertices(self):
        return self._vertices if self._vertices.size > 0 else None

    def enable_axes(self):
        if not self._show_axes:
            self._show_axes = True
            self.create()

    def disable_axes(self):
        if self._show_axes:
            self._show_axes = False
            self.create()
