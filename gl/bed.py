#!/usr/bin/env python3
"""GLBed and associated classes."""

import numpy as np

import glm

from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import *
from OpenGL.GLU import *


class _Axes():
    origin = (0.0, 0.0, 0.0)

    def __init__(self, parent):
        self.parent = parent

        self._vao_axes = None
        self._vao_arrows = None

        build_dimensions = self.parent.build_dimensions
        dist = 0.5 * (build_dimensions[1] + max(build_dimensions[0], build_dimensions[2]))
        self._arrow_base_radius = dist / 75.0
        self._arrow_length = 2.5 * self._arrow_base_radius
        self._quadric = gluNewQuadric()
        gluQuadricDrawStyle(self._quadric, GLU_FILL)

    def create_vao(self):
        build_dimensions = self.parent.build_dimensions
        x = build_dimensions[0] - build_dimensions[3], build_dimensions[3]
        y = build_dimensions[1] - build_dimensions[4], build_dimensions[4]
        z = build_dimensions[2] - build_dimensions[5], build_dimensions[5]

        vao = glGenVertexArrays(2)
        vbo = glGenBuffers(4)

        points = np.array([
            x[0], 0.0, 0.0,  1.0, 0.0, 0.0,
            -x[1], 0.0, 0.0, 1.0, 0.0, 0.0,
            0.0, y[0], 0.0,  0.0, 1.0, 0.0,
            0.0, -y[1], 0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, z[0],  0.0, 0.0, 1.0,
            0.0, 0.0, -z[1], 0.0, 0.0, 1.0
        ], dtype=np.float32)
        glBindVertexArray(vao[0])

        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, points.nbytes, points, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, points.nbytes, points, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindVertexArray(vao[1])

        glBindVertexArray(0)
        self._vao_axes, self._vao_arrows = vao

    def render(self):
        """Render colored axes and arrows."""
        if self._quadric is None:
            return

        glBindVertexArray(self._vao_axes)
        glDrawArrays(GL_LINES, 0, 6)

        glBindVertexArray(0)
        glUseProgram(0)
        return

        build_dimensions = self.parent.build_dimensions

        x = build_dimensions[0] - build_dimensions[3], build_dimensions[3]
        y = build_dimensions[1] - build_dimensions[4], build_dimensions[4]
        z = build_dimensions[2] - build_dimensions[5], build_dimensions[5]

        verts = np.array([
            x[0], 0, 0, -x[1], 0, 0,
            0, y[0], 0, 0, -y[1], 0,
            0, 0, z[0], 0, 0, -z[1]])
        colors = np.array([
            1.0, 0.0, 0.0, 1.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 1.0, 0.0, 0.0, 1.0])

        glDisable(GL_DEPTH_TEST)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, verts)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawArrays(GL_LINES, 0, 6)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)
        glEnable(GL_DEPTH_TEST)

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

        # origin sphere
        glColor3f(0.0, 0.0, 0.0)
        gluSphere(self._quadric, self._arrow_base_radius, 32, 32)

    def _render_arrow(self, length):
        glTranslated(0.0, 0.0, length)
        gluQuadricOrientation(self._quadric, GLU_OUTSIDE)
        gluCylinder(self._quadric, self._arrow_base_radius, 0.0, self._arrow_length, 32, 1)
        gluQuadricOrientation(self._quadric, GLU_INSIDE)
        gluDisk(self._quadric, 0.0, self._arrow_base_radius, 32, 1)

    def __delete__(self, _):
        if not self._quadric:
            gluDeleteQuadric(self._quadric)


class GLBed():
    """GLBed class."""
    color_light = 0.91
    color_dark = 0.72
    color_border = 0.40

    def __init__(self, parent, build_dimensions, axes=True, bounding_box=True, every=100, subdivisions=10):
        if not all([0 <= build_dimensions[i+3] <= build_dimensions[i] for i in range(3)]):
            raise ValueError('build dimension origin out of range')
        self.parent = parent

        self._shader_program = None
        self._vao_gridlines = None
        self._vao_bounding_box = None
        self._count_gridlines = None
        self._count_bounding_box = None

        self._build_dimensions = build_dimensions
        self._show_axes = axes
        self._show_bounding_box = bounding_box
        self._every = every
        self._subdivisions = subdivisions
        self._axes = _Axes(self)

        self._initialized = False

    def init_shaders(self):
        vertex = """
        #version 450 core

        layout (location = 0) in vec3 positions;
        layout (location = 1) in vec3 colors;

        layout (location = 0) uniform mat4 projection;
        layout (location = 1) uniform mat4 modelview;

        out vec3 newColor;

        void main() {
            gl_Position = projection * modelview * vec4(positions, 1.0);
            newColor = colors;
        }
        """

        fragment = """
        #version 450 core

        in vec3 newColor;
        out vec4 color;

        void main() {
            color = vec4(newColor, 1.0);
        }
        """

        vertex_shader = shaders.compileShader(vertex, GL_VERTEX_SHADER)
        fragment_shader = shaders.compileShader(fragment, GL_FRAGMENT_SHADER)
        self._shader_program = shaders.compileProgram(vertex_shader, fragment_shader)

    def create_vao(self):
        vao = glGenVertexArrays(2)
        vbo = glGenBuffers(5)

        vertices, colors = self._generate_gridlines()
        self._count_gridlines = vertices.size // 3
        glBindVertexArray(vao[0])

        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        vertices, colors, indices = self._generate_bounding_box()
        self._count_bounding_box = indices.size
        glBindVertexArray(vao[1])

        glBindBuffer(GL_ARRAY_BUFFER, vbo[2])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[3])
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo[4])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        glBindVertexArray(0)
        self._vao_gridlines, self._vao_bounding_box = vao

        self._axes.create_vao()

    def init(self):
        """Initialize vertices."""
        if self._initialized:
            return True

        self.init_shaders()
        self.create_vao()

        self._initialized = True
        return True

    def render(self):
        """Render bed."""
        if not self.init():
            return

        glDisable(GL_LINE_SMOOTH)

        proj = glGetDoublev(GL_PROJECTION_MATRIX)
        view = glGetDoublev(GL_MODELVIEW_MATRIX)

        glUseProgram(self._shader_program)
        glUniformMatrix4fv(0, 1, GL_FALSE, proj)
        glUniformMatrix4fv(1, 1, GL_FALSE, view)

        self._render_gridlines()

        if self._show_axes:
            self._render_axes()

        if self._show_bounding_box:
            self._render_bounding_box()

        glBindVertexArray(0)
        glUseProgram(0)
        glEnable(GL_LINE_SMOOTH)

    def _generate_gridlines(self):
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

        verts = np.concatenate([axes_verts, x_verts, z_verts]).astype(np.float32)
        colors = np.concatenate([axes_colors, x_colors, z_colors]).astype(np.float32)
        return verts, colors

    def _generate_bounding_box(self):
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
            -x[1], -y[1], -z[1]
        ], dtype=np.float32)

        # 12 edges
        indices = np.array([
            0, 1, 1, 2, 2, 3, 3, 0,
            0, 5, 1, 6, 2, 7, 3, 4,
            4, 5, 5, 6, 6, 7, 7, 4
        ], dtype=np.uint16)

        return vertices, np.full(24, self.color_dark, dtype=np.float32), indices

    def _render_gridlines(self):
        if self._vao_gridlines is None:
            return

        glBindVertexArray(self._vao_gridlines)
        glDrawArrays(GL_LINES, 0, self._count_gridlines)

    def _render_bounding_box(self):
        if self._vao_bounding_box is None:
            return

        glBindVertexArray(self._vao_bounding_box)
        glDrawElements(GL_LINES, self._count_bounding_box, GL_UNSIGNED_SHORT, ctypes.c_void_p(0))

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
        self.create_vao()

    @property
    def show_bounding_box(self):
        return self._show_bounding_box

    @show_bounding_box.setter
    def show_bounding_box(self, value):
        self._show_bounding_box = value

    @property
    def build_dimensions(self):
        return self._build_dimensions

    @build_dimensions.setter
    def build_dimensions(self, value):
        self._build_dimensions = value
        self._initialized = False
