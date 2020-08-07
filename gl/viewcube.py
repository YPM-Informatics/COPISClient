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

        self._shader_program = None
        self._vao = None

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
        out vec4 outColor;

        void main() {
            // outColor = vec4(0.8, 0.8, 0.8, 1.0);
            outColor = vec4(newColor, 1.0);
        }
        """

        vertex_shader = shaders.compileShader(vertex, GL_VERTEX_SHADER)
        fragment_shader = shaders.compileShader(fragment, GL_FRAGMENT_SHADER)
        self._shader_program = shaders.compileProgram(vertex_shader, fragment_shader)

    def create_vao(self):
        vertices = np.array([
            1.0, 1.0, 1.0,      1.0, 0.0, 0.0,
            1.0, -1.0, 1.0,     0.0, 1.0, 0.0,
            1.0, -1.0, -1.0,    0.0, 0.0, 1.0,
            1.0, 1.0, -1.0,     1.0, 1.0, 1.0,
            -1.0, 1.0, -1.0,    0.0, 1.0, 0.0,
            -1.0, 1.0, 1.0,     1.0, 0.0, 1.0,
            -1.0, -1.0, 1.0,    1.0, 1.0, 0.0,
            -1.0, -1.0, -1.0,   0.0, 1.0, 1.0
        ], dtype=np.float32)

        indices = np.array([
            0, 1, 2, 2, 3, 0,
            0, 3, 4, 4, 5, 0,
            0, 5, 6, 6, 1, 0,
            1, 6, 7, 7, 2, 1,
            7, 4, 3, 3, 2, 7,
            4, 7, 6, 6, 5, 4
        ], dtype=np.uint16)

        self._vao = glGenVertexArrays(1)
        vbo = glGenBuffers(3)

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

        glBindVertexArray(0)
        """
        glBindVertexArray(vaoIds[0]);

        glBindBuffer(GL_ARRAY_BUFFER, vboIds[0]);  // coordinates
        glBufferData(GL_ARRAY_BUFFER, sizeof(ave), ave, GL_STATIC_DRAW);
        glVertexAttribPointer(vertexAttribCoords, nCoordsComponents, GL_FLOAT, GL_FALSE, 0, 0);
        glEnableVertexAttribArray(vertexAttribCoords);

        glBindBuffer(GL_ARRAY_BUFFER, vboIds[1]);  // color
        glBufferData(GL_ARRAY_BUFFER, sizeof(ace), ace, GL_STATIC_DRAW);
        glVertexAttribPointer(vertexAttribColor, nColorComponents, GL_FLOAT, GL_FALSE, 0, 0);
        glEnableVertexAttribArray(vertexAttribColor);

        // Bind VAO (set current) to define pyramid data
        glBindVertexArray(vaoIds[1]);

        glBindBuffer(GL_ARRAY_BUFFER, vboIds[2]);  // coordinates
        glBufferData(GL_ARRAY_BUFFER, sizeof(pve), pve, GL_STATIC_DRAW);
        glVertexAttribPointer(vertexAttribCoords, nCoordsComponents, GL_FLOAT, GL_FALSE, 0, 0);
        glEnableVertexAttribArray(vertexAttribCoords);

        glBindBuffer(GL_ARRAY_BUFFER, vboIds[3]);  // color
        glBufferData(GL_ARRAY_BUFFER, sizeof(pce), pce, GL_STATIC_DRAW);
        glVertexAttribPointer(vertexAttribColor, nColorCo
        """

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
