"""ActionVis class."""


from collections import defaultdict
from typing import Tuple, Union

import glm
import numpy as np
import wx
from enums import ActionType
from OpenGL.GL import *
from OpenGL.GLU import *
from utils import point5_to_mat4, shade_color, xyzpt_to_mat4


class GLActionVis:
    """Manage action list visualization in a GLCanvas.

    """

    # colors to differentiate devices
    colors = [
        (0.0000, 0.4588, 0.9686, 1.000),    # blueish
        (0.4863, 0.0549, 0.3725, 1.000),    # purpleish
        (0.9255, 0.0588, 0.2784, 1.000),    # reddish
        (0.9333, 0.4196, 0.2314, 1.000),    # orangeish
        (0.9804, 0.7216, 0.3216, 1.000),    # yellowish
        (0.2510, 0.7843, 0.4980, 1.000),    # limeish
        (0.0706, 0.6824, 0.4745, 1.000),    # lighttealish
        (0.0314, 0.4510, 0.3255, 1.000),    # greenish
        (0.0157, 0.3294, 0.3490, 1.000),    # tealish
    ]

    def __init__(self, parent):
        """Inits GLActionVis with constructors."""
        self.parent = parent
        self._initialized = False
        self.device_len = None

        self._lines = defaultdict(list)
        self._points = defaultdict(list)

        self._vao_point_volumes = None
        self._point_count = 0

        self._vao_lines = {}
        self._vao_points = {}

    def create_vaos(self) -> None:
        """Bind VAOs to define vertex data."""
        vbo = glGenBuffers(1)
        vertices = glm.array(
            glm.vec3(-0.5, -1.0, -1.0),     # bottom
            glm.vec3(0.5, -1.0, -1.0),
            glm.vec3(0.5, -1.0, 1.0),
            glm.vec3(-0.5, -1.0, 1.0),
            glm.vec3(-0.5, 1.0, -1.0),      # right
            glm.vec3(0.5, 1.0, -1.0),
            glm.vec3(0.5, -1.0, -1.0),
            glm.vec3(-0.5, -1.0, -1.0),
            glm.vec3(-0.5, 1.0, 1.0),       # top
            glm.vec3(0.5, 1.0, 1.0),
            glm.vec3(0.5, 1.0, -1.0),
            glm.vec3(-0.5, 1.0, -1.0),
            glm.vec3(-0.5, -1.0, 1.0),      # left
            glm.vec3(0.5, -1.0, 1.0),
            glm.vec3(0.5, 1.0, 1.0),
            glm.vec3(-0.5, 1.0, 1.0),
            glm.vec3(0.5, 1.0, -1.0),       # back
            glm.vec3(0.5, 1.0, 1.0),
            glm.vec3(0.5, -1.0, 1.0),
            glm.vec3(0.5, -1.0, -1.0),
            glm.vec3(-0.5, -1.0, -1.0),     # front
            glm.vec3(-0.5, -1.0, 1.0),
            glm.vec3(-0.5, 1.0, 1.0),
            glm.vec3(-0.5, 1.0, -1.0),
        )
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, glm.value_ptr(vertices), GL_STATIC_DRAW)

        self._vao_point_volumes = glGenVertexArrays(1)
        glBindVertexArray(self._vao_point_volumes)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

    def _update_vaos(self) -> None:
        """Update VAOs when action list changes."""
        self._vao_lines.clear()
        self._vao_points.clear()

        for key, value in self._lines.items():
            # ignore if 1 or fewer points
            if len(value) > 1:
                points = glm.array([glm.vec3(mat[1][3]) for mat in value])

                vbo = glGenBuffers(1)
                glBindBuffer(GL_ARRAY_BUFFER, vbo)
                glBufferData(GL_ARRAY_BUFFER, points.nbytes, glm.value_ptr(points), GL_STATIC_DRAW)

                vao = glGenVertexArrays(1)
                glBindVertexArray(vao)
                glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
                glEnableVertexAttribArray(0)
                self._vao_lines[key] = vao

                glBindVertexArray(0)

        point_mats = None
        point_colors = None
        point_ids = None
        scale = glm.scale(glm.mat4(), glm.vec3(3, 3, 3))

        for key, value in self._points.items():
            if len(value) > 1:
                new_mats = glm.array([p[1] * scale for p in value[1:]])
                color = shade_color(glm.vec4(self.colors[key]), -0.3)
                new_colors = glm.array([color] * (len(value) - 1))
                print(value)
                new_ids = [p[0] for p in value[1:]]
                if not point_mats:
                    point_mats = new_mats
                    point_colors = new_colors
                    point_ids = new_ids
                else:
                    point_mats += new_mats
                    point_colors += new_colors
                    point_ids += new_ids

        point_ids = np.array(point_ids, dtype=np.intc) # 32 bit signed integer
        self._point_count = 0 if not point_mats else len(point_mats)

        if not point_mats:
            return

        vbo = glGenBuffers(3)
        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, point_mats.nbytes, glm.value_ptr(point_mats), GL_STATIC_DRAW)
        glBindVertexArray(self._vao_point_volumes)

        # modelmats
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(0))
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(16)) # sizeof(glm::vec4)
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(5, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(32)) # 2 * sizeof(glm::vec4)
        glEnableVertexAttribArray(5)
        glVertexAttribPointer(6, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(48)) # 3 * sizeof(glm::vec4)
        glEnableVertexAttribArray(6)

        glVertexAttribDivisor(3, 1)
        glVertexAttribDivisor(4, 1)
        glVertexAttribDivisor(5, 1)
        glVertexAttribDivisor(6, 1)

        # colors
        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, point_colors.nbytes, glm.value_ptr(point_colors), GL_STATIC_DRAW)
        glVertexAttribPointer(7, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(7)
        glVertexAttribDivisor(7, 1)

        # ids for picking
        glBindBuffer(GL_ARRAY_BUFFER, vbo[2])
        glBufferData(GL_ARRAY_BUFFER, point_ids.nbytes, point_ids, GL_STATIC_DRAW)
        # huhhhh?????? I must have done something wrong because only GL_FLOAT works
        glVertexAttribPointer(8, 1, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(8)
        glVertexAttribDivisor(8, 1)

        glEnableVertexAttribArray(0)
        glBindVertexArray(0)

    def update_colors(self) -> None:
        return

    def update_arrays(self) -> None:
        """Update lines and points when action list changes.

        Called from GLCanvas upon core_a_list_changed signal.
        """
        core = wx.GetApp().core
        self._lines.clear()
        self._points.clear()

        self.device_len = len(core.devices)

        # add initial points
        for i, device in enumerate(core.devices):
            self._points[device.device_id].append((i, point5_to_mat4(device.position)))

        for i, action in enumerate(core.actions):
            if action.atype == ActionType.G0 or action.atype == ActionType.G1:
                if action.argc == 5:
                    self._lines[action.device].append((self.device_len + i, xyzpt_to_mat4(*action.args)))
            elif action.atype == ActionType.C0:
                if action.device in self._lines.keys():
                    self._points[action.device].append(self._lines[action.device][-1])
                else:
                    self._points[action.device].append(self._points[action.device][0])
            else:
                # TODO: process other action ids
                pass

        self._update_vaos()

    def init(self) -> bool:
        """Initialize for rendering.

        Returns:
            True if initialized without error, False otherwise.
        """
        if self._initialized:
            return True

        self.create_vaos()
        self.update_arrays()

        self._initialized = True
        return True

    def render(self) -> None:
        """Render actions to canvas."""
        if not self.init():
            return

        proj = self.parent.projection_matrix
        view = self.parent.modelview_matrix
        model = glm.mat4()

        # render path lines
        glUseProgram(self.parent.color_shader) # TODO: improve this
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(2, 1, GL_FALSE, glm.value_ptr(model))

        for key, value in self._vao_lines.items():
            color = glm.vec4(self.colors[key])
            glUniform4fv(3, 1, glm.value_ptr(color))
            glBindVertexArray(value)
            glDrawArrays(GL_LINE_STRIP, 0, len(self._lines[key]))

        if self._point_count <= 0:
            return

        # render points
        glUseProgram(self.parent.instanced_color_shader)
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))

        glBindVertexArray(self._vao_point_volumes)
        glDrawArraysInstanced(GL_QUADS, 0, 24, self._point_count)

        glBindVertexArray(0)
        glUseProgram(0)

    def render_for_picking(self) -> None:
        """Render action "pickables" for picking pass."""
        if not self.init():
            return

        proj = self.parent.projection_matrix
        view = self.parent.modelview_matrix

        # render picking
        glUseProgram(self.parent.instanced_picking_shader)
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))

        glBindVertexArray(self._vao_point_volumes)
        glDrawArraysInstanced(GL_QUADS, 0, 24, self._point_count)

        glBindVertexArray(0)
        glUseProgram(0)
