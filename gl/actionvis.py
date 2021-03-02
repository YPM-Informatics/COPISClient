# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

"""ActionVis class.

TODO: Add rendering functionality to more than just G0 and C0 actions.
TODO: Signify via color or border when action is selected
"""

from collections import defaultdict

import glm
import numpy as np
from enums import ActionType
from OpenGL.GL import *
from OpenGL.GLU import *
from pydispatch import dispatcher
from utils import shade_color, xyzpt_to_mat4


class GLActionVis:
    """Manage action list visualization in a GLCanvas."""

    # colors to differentiate devices
    colors = [
        (0.0000, 0.4088, 0.9486, 1.000),    # blueish
        (0.4863, 0.0549, 0.3725, 1.000),    # purpleish
        (0.9255, 0.0588, 0.2784, 1.000),    # reddish
        (0.9333, 0.4196, 0.2314, 1.000),    # orangeish
        (0.9804, 0.7016, 0.3216, 1.000),    # yellowish
        (0.2706, 0.6824, 0.4345, 1.000),    # lightgreenish
        (0.0314, 0.5310, 0.3255, 1.000),    # greenish
        (0.0157, 0.3494, 0.3890, 1.000),    # tealish
    ]

    def __init__(self, parent):
        """Inits GLActionVis with constructors."""
        self.p = parent
        self.c = self.p.c

        self._initialized = False
        self.device_len = None

        self._items = {
            'line': defaultdict(list),
            'point': defaultdict(list)}
        self._vaos = {
            'line': {},
            'point': {}}

        self._vao_box = None
        self._num_points = 0

        dispatcher.connect(self.update_vaos, signal='core_p_selected')
        dispatcher.connect(self.update_vaos, signal='core_p_deselected')

    def create_vaos(self) -> None:
        """Bind VAOs to define vertex data."""
        vbo = glGenBuffers(1)

        # initialize camera box
        # TODO: update to stl
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

        self._vao_box = glGenVertexArrays(1)
        glBindVertexArray(self._vao_box)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

    def update_vaos(self) -> None:
        """Update VAOs when action list changes."""
        for vao in self._vaos.values():
            vao.clear()

        # --- bind data for lines ---

        for key, value in self._items['line'].items():
            # ignore if 1 or fewer points
            if len(value) <= 1:
                continue

            points = glm.array([glm.vec3(mat[1][3]) for mat in value])

            vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, points.nbytes, glm.value_ptr(points), GL_STATIC_DRAW)

            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            self._vaos['line'][key] = vao

            glBindVertexArray(0)

        # --- bind data for points ---

        point_mats = None
        point_colors = None
        point_ids = None
        scale = glm.scale(glm.mat4(), glm.vec3(3, 3, 3))

        for key, value in self._items['point'].items():
            new_mats = glm.array([p[1] * scale for p in value])
            color = shade_color(glm.vec4(self.colors[key % len(self.colors)]), -0.3)

            new_colors = glm.array([color] * len(value))

            # if point is selected, darken its color
            for i, v in enumerate(value):
                if v[0] in self.c.selected_points:
                    new_colors[i] = shade_color(new_colors[i], 0.6)

            new_ids = [p[0] for p in value]

            if not point_mats:
                point_mats = new_mats
                point_colors = new_colors
                point_ids = new_ids
            else:
                point_mats += new_mats
                point_colors += new_colors
                point_ids += new_ids

        self._num_points = 0 if not point_mats else len(point_mats)

        # stop if no points to set
        if not point_mats:
            return

        point_ids = np.array(point_ids, dtype=np.int32)

        vbo = glGenBuffers(3)
        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, point_mats.nbytes, glm.value_ptr(point_mats), GL_STATIC_DRAW)
        glBindVertexArray(self._vao_box)

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

    def update_actions(self) -> None:
        """Update lines and points when action list changes.

        Called from GLCanvas upon core_a_list_changed signal.

        # TODO: process other action ids
        """
        for item in self._items.values():
            item.clear()

        self.device_len = len(self.c.devices)

        for i, action in enumerate(self.c.actions):
            if action.atype in (ActionType.G0, ActionType.G1):
                self._items['line'][action.device].append((self.device_len + i, xyzpt_to_mat4(*action.args)))

            elif action.atype in (ActionType.C0, ActionType.C1):
                if action.device not in self._items['line'].keys():
                    continue
                self._items['point'][action.device].append(self._items['line'][action.device][-1])

            else:
                # TODO!
                pass

        self.update_vaos()

    def init(self) -> bool:
        """Initialize for rendering.

        Returns:
            True if initialized without error, False otherwise.
        """
        if self._initialized:
            return True

        self.create_vaos()
        self.update_actions()

        self._initialized = True
        return True

    def render(self) -> None:
        """Render actions to canvas."""
        if not self.init():
            return

        proj = self.p.projection_matrix
        view = self.p.modelview_matrix
        model = glm.mat4()

        # render path lines
        glUseProgram(self.p.shaders['single_color'])
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(2, 1, GL_FALSE, glm.value_ptr(model))

        for key, value in self._vaos['line'].items():
            color = glm.vec4(self.colors[key % len(self.colors)])
            glUniform4fv(3, 1, glm.value_ptr(color))
            glBindVertexArray(value)
            glDrawArrays(GL_LINE_STRIP, 0, len(self._items['line'][key]))

        if self._num_points <= 0:
            return

        # render points
        glUseProgram(self.p.shaders['instanced_model_color'])
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))

        glBindVertexArray(self._vao_box)
        glDrawArraysInstanced(GL_QUADS, 0, 24, self._num_points)

        glBindVertexArray(0)
        glUseProgram(0)

    def render_for_picking(self) -> None:
        """Render action "pickables" for picking pass."""
        if not self.init():
            return

        proj = self.p.projection_matrix
        view = self.p.modelview_matrix

        # render picking
        glUseProgram(self.p.shaders['instanced_picking'])
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))

        glBindVertexArray(self._vao_box)
        glDrawArraysInstanced(GL_QUADS, 0, 24, self._num_points)

        glBindVertexArray(0)
        glUseProgram(0)
