#!/usr/bin/env python3
"""ViewCube class."""

import numpy as np

import wx
import glm

from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import *
from OpenGL.GLU import *

from enums import ViewCubePos, ViewCubeSize


class GLViewCube():
    def __init__(self, parent, position=ViewCubePos.TOP_RIGHT, size=ViewCubeSize.MEDIUM):
        self.parent = parent
        self._position = position if position in ViewCubePos else ViewCubePos.TOP_RIGHT
        self._size = size if size in ViewCubeSize else ViewCubeSize.MEDIUM

        self.shader = None
        self.vao = None
        self.vbo = None
        self.elementbuffer = None
        self._volumes = None
        self._initialized = False

    def init(self):
        if self._initialized:
            return True

        vertex_shader = """
        #version 450 core

        layout(location = 0) in vec3 positions;
        layout(location = 1) in vec3 colors;

        layout(location = 0) uniform mat4 projection;
        layout(location = 1) uniform mat4 view;
        layout(location = 2) uniform mat4 model;

        out vec3 newColor;

        void main() {
            gl_Position = projection * view * vec4(positions, 1.0);
            newColor = colors;
        }
        """

        fragment_shader = """
        #version 450 core

        in vec3 newColor;
        out vec4 outColor;

        void main() {
            outColor = vec4(0.8, 0.8, 0.8, 1.0);
            outColor = vec4(newColor, 1.0);
        }
        """

        VERTEX_SHADER = shaders.compileShader(vertex_shader, GL_VERTEX_SHADER)
        FRAGMENT_SHADER = shaders.compileShader(fragment_shader, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(VERTEX_SHADER, FRAGMENT_SHADER)

        vertices = np.array([
            1.0, 1.0, 1.0, 1.0, 0.0, 0.0,
            1.0, -1.0, 1.0, 0.0, 1.0, 0.0,
            1.0, -1.0, -1.0, 0.0, 0.0, 1.0,
            1.0, 1.0, -1.0, 1.0, 0.0, 0.0,
            -1.0, 1.0, -1.0, 0.0, 1.0, 0.0,
            -1.0, 1.0, 1.0, 1.0, 0.0, 1.0,
            -1.0, -1.0, 1.0, 1.0, 1.0, 0.0,
            -1.0, -1.0, -1.0, 0.0, 1.0, 1.0], dtype=np.float32)

        indices = np.array([
            0, 1, 2, 2, 3, 0,
            0, 3, 4, 4, 5, 0,
            0, 5, 6, 6, 1, 0,
            1, 6, 7, 7, 2, 1,
            7, 4, 3, 3, 2, 7,
            4, 7, 6, 6, 5, 4])

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        self.elementbuffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.elementbuffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        stride = 24 # 6 * 4
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))

        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glUseProgram(self.shader)

        self._initialized = True
        return True

    def render(self):
        """Render ViewCube."""
        if not self.init():
            return

        glViewport(*self._get_viewcube_viewport())
        # glOrtho(-2.3, 2.3, -2.3, 2.3, -2.3, 2.3)

        glUseProgram(self.shader)

        proj = glm.ortho(-2.3, 2.3, -2.3, 2.3, -2.3, 2.3)
        view = glm.mat4_cast(self.parent.rot_quat)

        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))

        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, 36, GL_UNSIGNED_INT, ctypes.c_void_p(0))

        # try:
        #     self.vbo.bind()
        #     try:
        #         glEnableClientState(GL_VERTEX_ARRAY)
        #         glVertexPointerf(self.vbo)
        #         glDrawArrays(GL_TRIANGLES, 0, 9)
        #     finally:
        #         self.vbo.unbind()
        #         glDisableClientState(GL_VERTEX_ARRAY)
        # finally:
        #     glUseProgram(0)

    def render_for_picking(self):
        """Render ViewCube for picking pass."""
        if not self.init():
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
