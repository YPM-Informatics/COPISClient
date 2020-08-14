"""Camera3D class."""

import math
from gl.thing import GLThing

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

import glm
from enums import CamAxis, CamMode


class Camera3D(GLThing):
    """[summary]

    Args:
        GLThing ([type]): [description]

    Returns:
        [type]: [description]
    """

    _scale = 10

    def __init__(self, parent, cam_id, x, y, z, b, c):
        super().__init__(parent)
        self._canvas = parent
        self._cam_id = cam_id
        self._x = float(x)
        self._y = float(y)
        self._z = float(z)
        self._b = float(b)
        self._c = float(c)

        self.start = (self._x, self._y, self._z, self._b, self._c)
        self.mode = CamMode.NORMAL

        self._angle = 0
        self._rotation_vector = []

        self.trans = False
        self.n_increment = 0
        self.increment_x = 0
        self.increment_y = 0
        self.increment_z = 0

        self._vao_box = None
        self._vao_side = None
        self._vao_top = None

    def create_vao(self):
        """
        TODO: add cylinders to camera model
        """
        self._vao_box, self._vao_side, self._vao_top = glGenVertexArrays(3)
        vbo = glGenBuffers(4)

        vertices = np.array([
            -0.5, -1.0, -1.0,  # bottom
            0.5, -1.0, -1.0,
            0.5, -1.0, 1.0,
            -0.5, -1.0, 1.0,

            -0.5, 1.0, -1.0,   # right
            0.5, 1.0, -1.0,
            0.5, -1.0, -1.0,
            -0.5, -1.0, -1.0,

            -0.5, 1.0, 1.0,    # top
            0.5, 1.0, 1.0,
            0.5, 1.0, -1.0,
            -0.5, 1.0, -1.0,

            -0.5, -1.0, 1.0,   # left
            0.5, -1.0, 1.0,
            0.5, 1.0, 1.0,
            -0.5, 1.0, 1.0,

            0.5, 1.0, -1.0,    # back
            0.5, 1.0, 1.0,
            0.5, -1.0, 1.0,
            0.5, -1.0, -1.0,

            -0.5, -1.0, -1.0,  # front
            -0.5, -1.0, 1.0,
            -0.5, 1.0, 1.0,
            -0.5, 1.0, -1.0,
        ], dtype=np.float32)
        glBindVertexArray(self._vao_box)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # ---

        thetas = np.linspace(0, 2 * np.pi, 24, endpoint=True)
        y = np.cos(thetas) * 0.7
        z = np.sin(thetas) * 0.7
        vertices = np.zeros(6 * 24, dtype=np.float32)
        vertices[::3] = np.tile(np.array([1.0, 0.5], dtype=np.float32), 24)
        vertices[1::3] = np.repeat(y, 2)
        vertices[2::3] = np.repeat(z, 2)
        glBindVertexArray(self._vao_side)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # ---

        vertices = np.concatenate((np.array([1.0, 0.0, 0.0]), vertices)).astype(np.float32)
        indices = np.insert(np.arange(24) * 2 + 1, 0, 0).astype(np.uint16)
        glBindVertexArray(self._vao_top)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[2])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo[3])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        glBindVertexArray(0)
        glDeleteBuffers(4, vbo)

    def render(self):
        """Render camera."""
        if not self.init():
            return

        # color based on selection type
        if self._selected:
            color = glm.vec4(75, 230, 150, 255) / 255.0
        elif self._hovered:
            color = glm.vec4(151, 191, 237, 255) / 255.0
        else:
            color = glm.vec4(125, 125, 125, 255) / 255.0

        proj = self._canvas.projection_matrix
        modelview = self._canvas.modelview_matrix * self.get_model_matrix()

        glUseProgram(self._canvas.get_shader_program('color'))
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(modelview))
        glUniform4fv(2, 1, glm.value_ptr(color))

        glBindVertexArray(self._vao_box)
        glDrawArrays(GL_QUADS, 0, 24)

        color -= 0.03
        glUniform4fv(2, 1, glm.value_ptr(color))
        glBindVertexArray(self._vao_side)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 48)

        color -= 0.03
        glUniform4fv(2, 1, glm.value_ptr(color))
        glBindVertexArray(self._vao_top)
        glDrawElements(GL_TRIANGLE_FAN, 25, GL_UNSIGNED_SHORT, ctypes.c_void_p(0))

        glBindVertexArray(0)
        glUseProgram(0)

    def render_for_picking(self):
        if not self.init():
            return

        proj = self._canvas.projection_matrix
        modelview = self._canvas.modelview_matrix * self.get_model_matrix()

        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(modelview))

        # render all parts of camera
        glBindVertexArray(self._vao_box)
        glDrawArrays(GL_QUADS, 0, 24)
        glBindVertexArray(self._vao_side)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 48)
        glBindVertexArray(self._vao_top)
        glDrawElements(GL_TRIANGLE_FAN, 25, GL_UNSIGNED_SHORT, ctypes.c_void_p(0))

        glBindVertexArray(0)
        glUseProgram(0)

    def get_model_matrix(self):
        scale = glm.vec3(self._scale, self._scale, self._scale)
        return glm.translate(glm.mat4(), glm.vec3(self._x, self._y, self._z)) * \
            glm.scale(glm.mat4(), scale) * \
            glm.rotate(glm.mat4(), self._b, glm.vec3(0.0, 0.0, 1.0)) * \
            glm.rotate(glm.mat4(), self._c, glm.vec3(0.0, 1.0, 0.0))

    @classmethod
    def set_scale(cls, value: int) -> None:
        cls._scale = value

    @property
    def cam_id(self):
        return self._cam_id

    @cam_id.setter
    def cam_id(self, value):
        self._cam_id = value

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
