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
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""GLActionVis class.

TODO: Add rendering functionality to more than just G0 and C0 actions.
TODO: Signify via color or border when action is selected
"""

from collections import defaultdict

from glm import vec3, vec4, mat4
import glm

from OpenGL.GL import (
    GL_FLOAT, GL_FALSE, GL_ARRAY_BUFFER, GL_STATIC_DRAW, GL_QUADS, GL_LINE_STRIP,
    glGenBuffers, glGenVertexArrays, glUniformMatrix4fv, glUniform4fv,
    glBindBuffer, glBufferData, glBindVertexArray, glVertexAttribPointer,
    glVertexAttribDivisor, glEnableVertexAttribArray, glUseProgram,
    glDrawArrays, glDrawArraysInstanced)
from OpenGL.GLU import ctypes

from copis.globals import ActionType
from copis.helpers import (
    create_cuboid, fade_color, get_action_args_values, point5_to_mat4, shade_color, xyzpt_to_mat4)


class GLActionVis:
    """Manage action list rendering in a GLCanvas."""

    # colors to differentiate devices
    colors = [
        vec4(0.0000, 0.4088, 0.9486, 1.0),    # blueish
        vec4(0.4863, 0.0549, 0.3725, 1.0),    # purpleish
        vec4(0.9255, 0.0588, 0.2784, 1.0),    # reddish
        vec4(0.9333, 0.4196, 0.2314, 1.0),    # orangeish
        vec4(0.9804, 0.7016, 0.3216, 1.0),    # yellowish
        vec4(0.2706, 0.6824, 0.4345, 1.0),    # lightgreenish
        vec4(0.0314, 0.5310, 0.3255, 1.0),    # greenish
        vec4(0.0157, 0.3494, 0.3890, 1.0),    # tealish
    ]

    _SCALE_FACTOR = 3

    def __init__(self, parent):
        """Initialize GLActionVis with constructors."""
        self.parent = parent
        self.core = self.parent.core

        self._initialized = False
        self._num_points = 0
        self._num_devices = 0

        self._items = {
            'line': defaultdict(list),
            'point': defaultdict(list),
            'device': defaultdict(list)
        }
        self._vaos = {
            'line': {},
            'point': {},
            'device': {},
        }

    def create_vaos(self) -> None:
        """Bind VAOs to define vertex data."""
        # Initialize device boxes
        for dvc in self.core.devices:
            key = dvc.device_id
            size = dvc.size
            scale = 3 * self._SCALE_FACTOR
            size_nm = vec3([round(v * scale, 1) for v in glm.normalize(size)])
            vertices = glm.array(*create_cuboid(size_nm))

            vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW)

            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            self._vaos['device'][key] = vao

            glBindVertexArray(0)

            vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW)

            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            self._vaos['point'][key] = vao

            glBindVertexArray(0)

    def update_action_vaos(self) -> None:
        """Update VAOs when action list changes."""
        self._vaos['line'].clear()

        # --- bind data for lines ---

        for key, value in self._items['line'].items():
            # ignore if 1 or fewer points
            if len(value) <= 1:
                continue

            points = glm.array([vec3(mat[1][3]) for mat in value])

            vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, points.nbytes, points.ptr, GL_STATIC_DRAW)

            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            self._vaos['line'][key] = vao

            glBindVertexArray(0)

        # --- bind data for points ---

        self._num_points = sum(len(i) for i in self._items['point'].values())

        if self._num_points > 0:
            scale = glm.scale(mat4(), vec3(self._SCALE_FACTOR))

            for key, value in self._items['point'].items():
                mats = glm.array([p[1] * scale for p in value])
                color = shade_color(vec4(self.colors[key % len(self.colors)]), -0.3)
                cols = glm.array([color] * len(value))

                # If point is selected, darken its color.
                for i, v in enumerate(value):
                    # Un-offset ids.
                    if v[0] - self._num_devices in self.core.selected_points:
                        cols[i] = shade_color(vec4(cols[i]), 0.6)

                ids = glm.array.from_numbers(ctypes.c_int, *(p[0] for p in value))

                self._bind_vao_mat_col_id(self._vaos['point'][key], mats, cols, ids)

    def update_device_vaos(self) -> None:
        """Update VAO when device list changes."""
        self._num_devices = len(self.core.devices)

        if self._num_devices > 0:
            scale = glm.scale(mat4(), vec3(self._SCALE_FACTOR))

            for key, value in self._items['device'].items():
                mats = glm.array([mat * scale for mat in value])
                device = next(filter(lambda d, k = key: d.device_id == k, self.core.devices))

                color = self.colors[key % len(self.colors)]
                if not device.is_homed:
                    color = fade_color(color, .8, .4)
                cols = glm.array([color])

                ids = glm.array(ctypes.c_int, key)

                self._bind_vao_mat_col_id(self._vaos['device'][key], mats, cols, ids)

    def update_actions(self) -> None:
        """Update lines and points when action list changes.

        Called from GLCanvas upon core_a_list_changed signal.

        # TODO: process other action ids
        """
        self._items['line'].clear()
        self._items['point'].clear()
        self._num_points = 0

        for i, pose in enumerate(self.core.actions):
            for action in pose.get_actions():
                if action.atype in (ActionType.G0, ActionType.G1):
                    args = get_action_args_values(action.args)
                    self._items['line'][action.device].append(
                        (i + self._num_devices, xyzpt_to_mat4(*args[:5])))
                elif action.atype in (ActionType.C0, ActionType.C1):
                    if action.device not in self._items['line'].keys():
                        continue
                    self._items['point'][action.device].append(
                        self._items['line'][action.device][-1])
                else:
                    # TODO!
                    pass

        self.update_action_vaos()

    def update_devices(self) -> None:
        """Update device locations when device list changes.

        Called from GLCanvas upon core_d_list_changed signal.
        """
        self._items['device'].clear()
        for device in self.core.devices:
            self._items['device'][device.device_id].append(point5_to_mat4(device.position))

        self.update_device_vaos()

    def init(self) -> bool:
        """Initialize for rendering.

        Returns:
            True if initialized without error, False otherwise.
        """
        if self._initialized:
            return True

        self.create_vaos()
        self.update_devices()
        self.update_actions()

        self._initialized = True
        return True

    def render(self) -> None:
        """Render actions to canvas."""
        if not self.init():
            return

        proj = self.parent.projection_matrix
        view = self.parent.modelview_matrix
        model = mat4()

        # --- render devices ---

        glUseProgram(self.parent.shaders['instanced_model_color'])
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))

        for key, value in self._vaos['device'].items():
            glBindVertexArray(value)
            glDrawArraysInstanced(GL_QUADS, 0, 24, len(self._items['device'][key]))

        # --- render path lines ---

        glUseProgram(self.parent.shaders['single_color'])
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(2, 1, GL_FALSE, glm.value_ptr(model))

        for key, value in self._vaos['line'].items():
            color = self.colors[key % len(self.colors)]
            glUniform4fv(3, 1, glm.value_ptr(color))
            glBindVertexArray(value)
            glDrawArrays(GL_LINE_STRIP, 0, len(self._items['line'][key]))

        # --- render points ---

        if self._num_points > 0:
            glUseProgram(self.parent.shaders['instanced_model_color'])
            glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
            glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))

            for key, value in self._vaos['point'].items():
                glBindVertexArray(value)
                glDrawArraysInstanced(GL_QUADS, 0, 24, len(self._items['point'][key]))

        glBindVertexArray(0)
        glUseProgram(0)

    def render_for_picking(self) -> None:
        """Render action "pickables" for picking pass."""
        if not self.init():
            return

        proj = self.parent.projection_matrix
        view = self.parent.modelview_matrix

        glUseProgram(self.parent.shaders['instanced_picking'])
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))

        # render devices for picking
        for key, value in self._vaos['device'].items():
            glBindVertexArray(value)
            glDrawArraysInstanced(GL_QUADS, 0, 24, len(self._items['device'][key]))

        # render points for picking
        for key, value in self._vaos['point'].items():
            glBindVertexArray(value)
            glDrawArraysInstanced(GL_QUADS, 0, 24, len(self._items['point'][key]))

        glBindVertexArray(0)
        glUseProgram(0)

    def _bind_vao_mat_col_id(self, vao, mat: glm.array, col: glm.array, ids: glm.array) -> None:
        vbo = glGenBuffers(3)
        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, mat.nbytes, mat.ptr, GL_STATIC_DRAW)
        glBindVertexArray(vao)

        # modelmats
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(0))
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(16)) # sizeof(glm::vec4)
        glVertexAttribDivisor(3, 1)
        glEnableVertexAttribArray(4)
        glVertexAttribDivisor(4, 1)
        glVertexAttribPointer(5, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(32)) # 2 * sizeof(glm::vec4)
        glEnableVertexAttribArray(5)
        glVertexAttribDivisor(5, 1)
        glVertexAttribPointer(6, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(48)) # 3 * sizeof(glm::vec4)
        glEnableVertexAttribArray(6)
        glVertexAttribDivisor(6, 1)

        # colors
        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, col.nbytes, col.ptr, GL_STATIC_DRAW)
        glVertexAttribPointer(7, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(7)
        glVertexAttribDivisor(7, 1)

        # ids for picking
        glBindBuffer(GL_ARRAY_BUFFER, vbo[2])
        glBufferData(GL_ARRAY_BUFFER, ids.nbytes, ids.ptr, GL_STATIC_DRAW)
        # it should be GL_INT here, yet only GL_FLOAT works. huh??
        glVertexAttribPointer(8, 1, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(8)
        glVertexAttribDivisor(8, 1)

        glEnableVertexAttribArray(0)
        glBindVertexArray(0)
