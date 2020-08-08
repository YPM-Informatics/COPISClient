#!/usr/bin/env python3
"""ViewCube class."""

import numpy as np
import glm

import wx
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GLU import *

from enums import ViewCubePos, ViewCubeSize


class GLViewCube():
    def __init__(self, parent, position=ViewCubePos.TOP_RIGHT, size=ViewCubeSize.MEDIUM):
        self.parent = parent
        self._position = position if position in ViewCubePos else ViewCubePos.TOP_RIGHT
        self._size = size if size in ViewCubeSize else ViewCubeSize.MEDIUM

        self._shader_program = None
        self._shader_program_picking = None
        self._vao = None
        self._vao_picking = None
        self._picked_side = -1

        self._volumes = None
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

        self._vao, self._vao_picking = glGenVertexArrays(2)
        vbo = glGenBuffers(5)

        glBindVertexArray(self._vao)

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

        glBindBuffer(GL_ARRAY_BUFFER, vbo[3])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[4])
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

    def init(self):
        if self._initialized:
            return True

        self.init_shaders()
        self.create_vao()

        self._initialized = True
        return True

    def render(self):
        """Render ViewCube."""
        if not self.init():
            return

        glViewport(*self._get_viewcube_viewport())

        proj = glm.ortho(-2.3, 2.3, -2.3, 2.3, -2.3, 2.3)
        view = glm.mat4_cast(self.parent.rot_quat)

        glUseProgram(self._shader_program)
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))

        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, 36, GL_UNSIGNED_SHORT, ctypes.c_void_p(0))
        glBindVertexArray(0)
        glUseProgram(0)

    def render_for_picking(self):
        """Render ViewCube for picking pass."""
        if not self.init():
            return

        glViewport(*self._get_viewcube_viewport())

        proj = glm.ortho(-2.3, 2.3, -2.3, 2.3, -2.3, 2.3)
        view = glm.mat4_cast(self.parent.rot_quat)

        glUseProgram(self._shader_program)
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))
        glBindVertexArray(self._vao_picking)
        glDrawArrays(GL_QUADS, 0, 24)
        glBindVertexArray(0)
        glUseProgram(0)

    def _render_highlighted(self, side):
        if side == -1:
            return

    def _get_viewcube_viewport(self):
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
    def picked_side(self):
        return self._picked_side

    @picked_side.setter
    def picked_side(self, value):
        self._picked_side = value

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
