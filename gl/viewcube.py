#!/usr/bin/env python3
"""ViewCube class."""

import numpy as np
import math
import glm

from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GLU import *

from enums import ViewCubePos, ViewCubeSize


class GLViewCube():
    def __init__(self, parent, position=ViewCubePos.TOP_RIGHT, size=ViewCubeSize.MEDIUM):
        self.parent = parent
        self._position = position if position in ViewCubePos else ViewCubePos.TOP_RIGHT
        self._size = size if size in ViewCubeSize else ViewCubeSize.MEDIUM

        self._vao = None
        self._vao_picking = None
        self._vao_highlight = None

        self._hover_id = -1
        self._hovered = False
        self._selected = False
        self._initialized = False

    def create_vao(self):
        """Bind VAOs to define vertex data."""
        self._vao, self._vao_picking, *self._vao_highlight = glGenVertexArrays(4)
        vbo = glGenBuffers(9)

        vertices = np.array([
            1.0, 1.0, 1.0, 0.7, 0.7, 0.7,
            1.0, -1.0, 1.0, 0.5, 0.5, 0.5,
            1.0, -1.0, -1.0, 0.5, 0.5, 0.5,
            1.0, 1.0, -1.0, 0.7, 0.7, 0.7,
            -1.0, 1.0, -1.0, 0.7, 0.7, 0.7,
            -1.0, 1.0, 1.0, 0.7, 0.7, 0.7,
            -1.0, -1.0, 1.0, 0.5, 0.5, 0.5,
            -1.0, -1.0, -1.0, 0.5, 0.5, 0.5
        ], dtype=np.float32)
        indices = np.array([
            0, 1, 2, 2, 3, 0,
            0, 3, 4, 4, 5, 0,
            0, 5, 6, 6, 1, 0,
            1, 6, 7, 7, 2, 1,
            7, 4, 3, 3, 2, 7,
            4, 7, 6, 6, 5, 4
        ], dtype=np.uint16)
        glBindVertexArray(self._vao)
        # standard viewcube

        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo[2])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        # ---

        vertices = np.array([
            1.0, 1.0, 1.0,      # 0 front   (id = 0)
            -1.0, 1.0, 1.0,     # 5
            -1.0, -1.0, 1.0,    # 6
            1.0, -1.0, 1.0,     # 1

            1.0, 1.0, 1.0,      # 0 top     (id = 1)
            1.0, 1.0, -1.0,     # 3
            -1.0, 1.0, -1.0,    # 4
            -1.0, 1.0, 1.0,     # 5

            1.0, 1.0, 1.0,      # 0 right   (id = 2)
            1.0, -1.0, 1.0,     # 1
            1.0, -1.0, -1.0,    # 2
            1.0, 1.0, -1.0,     # 3

            1.0, -1.0, 1.0,     # 1 bottom  (id = 3)
            -1.0, -1.0, 1.0,    # 6
            -1.0, -1.0, -1.0,   # 7
            1.0, -1.0, -1.0,    # 2

            -1.0, -1.0, -1.0,   # 7 left    (id = 4)
            -1.0, -1.0, 1.0,    # 6
            -1.0, 1.0, 1.0,     # 5
            -1.0, 1.0, -1.0,    # 4

            -1.0, -1.0, -1.0,   # 7 back    (id = 5)
            -1.0, 1.0, -1.0,    # 4
            1.0, 1.0, -1.0,     # 3
            1.0, -1.0, -1.0     # 2
        ], dtype=np.float32)
        colors = np.zeros(72, dtype=np.float32)
        colors[::3] = np.arange(6).repeat(4) / 255.0
        glBindVertexArray(self._vao_picking)
        # viewcube for picking

        glBindBuffer(GL_ARRAY_BUFFER, vbo[3])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[4])
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        # ---

        colors_fill = np.tile(np.array([0.561, 0.612, 0.729], dtype=np.float32), 24)
        glBindVertexArray(self._vao_highlight[0])
        # highlighted face of viewcube

        glBindBuffer(GL_ARRAY_BUFFER, vbo[5])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[6])
        glBufferData(GL_ARRAY_BUFFER, colors_fill.nbytes, colors_fill, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        colors_border = np.tile(np.array([0.220, 0.388, 0.659], dtype=np.float32), 24)
        glBindVertexArray(self._vao_highlight[1])
        # outlined face of viewcube

        glBindBuffer(GL_ARRAY_BUFFER, vbo[7])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[8])
        glBufferData(GL_ARRAY_BUFFER, colors_border.nbytes, colors_border, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

    def init(self):
        if self._initialized:
            return True

        self.create_vao()

        self._initialized = True
        return True

    def render(self):
        """Render ViewCube."""
        if not self.init():
            return

        glViewport(*self.get_viewport())

        proj = glm.ortho(-2.3, 2.3, -2.3, 2.3, -2.3, 2.3)
        modelview = glm.mat4_cast(self.parent.rot_quat)

        glUseProgram(self.parent.get_shader_program())
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(modelview))

        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, 36, GL_UNSIGNED_SHORT, ctypes.c_void_p(0))

        self._render_highlighted()

        glBindVertexArray(0)
        glUseProgram(0)

    def render_for_picking(self):
        """Render ViewCube for picking pass."""
        if not self.init():
            return

        glViewport(*self.get_viewport())

        proj = glm.ortho(-2.3, 2.3, -2.3, 2.3, -2.3, 2.3)
        modelview = glm.mat4_cast(self.parent.rot_quat)

        glUseProgram(self.parent.get_shader_program())
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(modelview))
        glBindVertexArray(self._vao_picking)
        glDrawArrays(GL_QUADS, 0, 24)
        glBindVertexArray(0)
        glUseProgram(0)

    def _render_highlighted(self):
        if not self._hovered:
            return

        glDisable(GL_DEPTH_TEST)
        glBindVertexArray(self._vao_highlight[0])
        # glDrawArrays(GL_QUADS, self._hover_id * 4, 4)

        glLineWidth(1.5)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glBindVertexArray(self._vao_highlight[1])
        glDrawArrays(GL_QUADS, self._hover_id * 4, 4)

        glLineWidth(1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glEnable(GL_DEPTH_TEST)

    def get_viewport(self):
        canvas_size = self.parent.get_canvas_size()
        width, height = canvas_size.width, canvas_size.height
        if self._position == ViewCubePos.TOP_LEFT:
            corner = (0, height - self._size)
        elif self._position == ViewCubePos.TOP_RIGHT:
            corner = (width - self._size, height - self._size)
        elif self._position == ViewCubePos.BOTTOM_LEFT:
            corner = (0, 0)
        elif self._position == ViewCubePos.BOTTOM_LEFT:
            corner = (width - self._size, 0)
        return (*corner, self._size, self._size)

    @property
    def hover_id(self):
        return self._hover_id

    @hover_id.setter
    def hover_id(self, value):
        self._hover_id = value
        if self._hover_id < 0 or self._hover_id > 5:
            self._hovered = False
        else:
            self._hovered = True

    @property
    def hovered(self):
        return self._hovered

    @hovered.setter
    def hovered(self, value):
        self._hovered = value

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        if value not in ViewCubePos:
            return
        self._position = value
        self._initialized = False

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        print(value)
        print(value in ViewCubeSize)
        if value not in ViewCubeSize:
            return
        self._size = value
        self._initialized = False
