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

        self._devices = []
        self._items = {
            'line': defaultdict(list),
            'point': defaultdict(list),
        }
        self._vaos = {
            'line': {},
            'point': None,
            'device': None,
        }

    def create_vaos(self) -> None:
        """Bind VAOs to define vertex data."""
        vbo = glGenBuffers(1)

        # initialize camera box
        # TODO: update to obj file
        size = vec3(350, 250, 200)
        scale = 3 * self._SCALE_FACTOR
        size_nm = vec3([round(v * scale, 1) for v in glm.normalize(size)])
        # arg = vec3(2, 1, 2)
        vertices = glm.array(*create_cuboid(size_nm))

        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW)

        self._vaos['point'] = glGenVertexArrays(1)
        glBindVertexArray(self._vaos['point'])
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        self._vaos['device'] = glGenVertexArrays(1)
        glBindVertexArray(self._vaos['device'])
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

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

        point_mats: glm.array = None
        point_cols: glm.array = None
        point_ids: glm.array = None
        scale = glm.scale(mat4(), vec3(self._SCALE_FACTOR))

        for key, value in self._items['point'].items():
            new_mats = glm.array([p[1] * scale for p in value])
            color = shade_color(vec4(self.colors[key % len(self.colors)]), -0.3)
            new_cols = glm.array([color] * len(value))

            # if point is selected, darken its color
            for i, v in enumerate(value):
                # un-offset ids
                if (v[0] - self._num_devices) in self.core.selected_points:
                    new_cols[i] = shade_color(vec4(new_cols[i]), 0.6)

            new_ids = glm.array.from_numbers(ctypes.c_int, *(p[0] for p in value))

            point_mats = new_mats if point_mats is None else point_mats.concat(new_mats)
            point_cols = new_cols if point_cols is None else point_cols.concat(new_cols)
            point_ids  = new_ids  if point_ids is None  else point_ids.concat(new_ids)

        # we're done if no points to set
        if not self._items['point']:
            return

        self._num_points = sum(len(i) for i in self._items['point'].values())

        self._bind_vao_mat_col_id(self._vaos['point'], point_mats, point_cols, point_ids)

    def update_device_vaos(self) -> None:
        """Update VAO when device list changes."""
        self._num_devices = len(self.core.devices)

        if self._num_devices > 0:
            scale = glm.scale(mat4(), vec3(self._SCALE_FACTOR))
            mats = glm.array([mat * scale for mat in self._devices])

            colors = [self.colors[i % len(self.colors)]
                if self.core.devices[i].is_homed else
                    fade_color(self.colors[i % len(self.colors)], .8, .4)
                for i in range(self._num_devices)]
            cols = glm.array(colors)

            ids = glm.array(ctypes.c_int, *list(range(self._num_devices)))

            self._bind_vao_mat_col_id(self._vaos['device'], mats, cols, ids)

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
        self._devices.clear()
        for device in self.core.devices:
            self._devices.append(point5_to_mat4(device.position))

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

        # --- render cameras ---

        glUseProgram(self.parent.shaders['instanced_model_color'])
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))
        glBindVertexArray(self._vaos['device'])
        glDrawArraysInstanced(GL_QUADS, 0, 24, self._num_devices)

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
            glBindVertexArray(self._vaos['point'])
            glDrawArraysInstanced(GL_QUADS, 0, 24, self._num_points)

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

        # render cameras for picking
        glBindVertexArray(self._vaos['device'])
        glDrawArraysInstanced(GL_QUADS, 0, 24, self._num_devices)

        # render points for picking
        if self._num_points > 0:
            glBindVertexArray(self._vaos['point'])
            glDrawArraysInstanced(GL_QUADS, 0, 24, self._num_points)

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
