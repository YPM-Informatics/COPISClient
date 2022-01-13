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
from collections import defaultdict, namedtuple

import numpy as np

from glm import vec3, vec4, mat4
import glm

from OpenGL.GL import (
    GL_FLOAT, GL_FALSE, GL_ARRAY_BUFFER, GL_STATIC_DRAW, GL_QUADS, GL_LINES, GL_LINE_STRIP,
    glGenBuffers, glGenVertexArrays, glUniformMatrix4fv, glUniform4fv, glDeleteBuffers,
    glBindBuffer, glBufferData, glBindVertexArray, glVertexAttribPointer,
    glVertexAttribDivisor, glEnableVertexAttribArray, glUseProgram,
    glDrawArrays, glDrawArraysInstanced)
from OpenGL.GLU import ctypes

from copis.globals import ActionType
from copis.helpers import (
    create_cuboid, create_device_features, fade_color,
    get_action_args_values, point5_to_mat4, shade_color, xyzpt_to_mat4)

ArrayInfo = namedtuple('ArrayInfo', 'name key')

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
            'device': defaultdict(list),
            'dvc_feature_vtx': defaultdict(list),
            'pt_feature_vtx': defaultdict(list)
        }
        self._vaos = {
            'line': {},
            'point': {},
            'device': {},
            'dvc_feature': {},
            'pt_feature': {}
        }

    def create_vaos(self) -> None:
        """Bind VAOs to define vertex data."""
        # Initialize device boxes
        for dvc in self.core.devices:
            key = dvc.device_id
            size = vec3(dvc.size.x, dvc.size.y / 2, dvc.size.z)
            scale = 2 * self._SCALE_FACTOR
            size_nm = vec3([round(v * scale, 1) for v in glm.normalize(size)])
            vertices = glm.array(*create_cuboid(size_nm))
            feat_vertices = np.array(
                create_device_features(dvc.size, 3 * self._SCALE_FACTOR),
                dtype=np.float32)

            vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW)

            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            self._vaos['device'][key] = vao

            vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW)

            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            self._vaos['point'][key] = vao

            vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, feat_vertices.nbytes, feat_vertices, GL_STATIC_DRAW)

            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            self._vaos['dvc_feature'][key] = vao
            self._items['dvc_feature_vtx'][key] = feat_vertices

            vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, feat_vertices.nbytes, feat_vertices, GL_STATIC_DRAW)

            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            self._vaos['pt_feature'][key] = vao
            self._items['pt_feature_vtx'][key] = feat_vertices

            glBindVertexArray(0)
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

        self._num_points = sum(len(i) for i in self._items['point'].values())

        if self._num_points > 0:
            scale = glm.scale(mat4(), vec3(self._SCALE_FACTOR))

            for key, value in self._items['point'].items():
                mats = glm.array([p[1] * scale for p in value])

                color = shade_color(vec4(self.colors[key % len(self.colors)]), -0.3)
                cols = glm.array([color] * len(value))

                feat_colors = self._get_dvc_feature_cols(('pt_feature_vtx', key))
                feat_cols = glm.array(feat_colors * len(value))

                # If point is selected, darken its color.
                for i, v in enumerate(value):
                    # Un-offset ids.
                    if v[0] - self._num_devices in self.core.selected_points:
                        shade_factor = .6
                        cols[i] = shade_color(vec4(cols[i]), shade_factor)

                        item_count = len(feat_colors)
                        start = i * item_count
                        stop = (i + 1) * item_count
                        for j in range(start, stop):
                            feat_cols[j] = shade_color(vec4(feat_cols[j]), shade_factor)

                ids = glm.array.from_numbers(ctypes.c_int, *(p[0] for p in value))

                self._bind_vao_mat_col_id(('point', key), mats, cols, ids)
                self._bind_device_features(('pt_feature', key), mats, feat_cols)

    def update_device_vaos(self) -> None:
        """Update VAO when device list changes."""
        self._num_devices = len(self.core.devices)

        if self._num_devices > 0:
            scale = glm.scale(mat4(), vec3(self._SCALE_FACTOR))

            for key, value in self._items['device'].items():
                mats = glm.array([mat * scale for mat in value])
                device = next(filter(lambda d, k = key: d.device_id == k, self.core.devices))

                color = self.colors[key % len(self.colors)]
                feat_colors = self._get_dvc_feature_cols(('dvc_feature_vtx', key))

                if not device.is_homed:
                    fade_pct = .5
                    alpha = .6
                    color = fade_color(color, fade_pct, alpha)
                    feat_colors = list(map(lambda c, f = fade_pct, a = alpha:
                        fade_color(c, f, a), feat_colors))

                ids = glm.array(ctypes.c_int, key)

                self._bind_vao_mat_col_id(('device', key), mats, glm.array(color), ids)
                self._bind_device_features(('dvc_feature', key), mats, glm.array(feat_colors))

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

                    data = self._items['line'][action.device][-1]
                    self._items['point'][action.device].append(data)

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

        for key, value in self._items['device'].items():
            index_count = self._get_dvc_feature_vtx_count(('dvc_feature_vtx', key))
            glBindVertexArray(self._vaos['dvc_feature'][key])
            glDrawArraysInstanced(GL_LINES, 0, index_count, len(value))

            glBindVertexArray(self._vaos['device'][key])
            glDrawArraysInstanced(GL_QUADS, 0, 24, len(value))

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

            for key, value in self._items['point'].items():
                index_count = self._get_dvc_feature_vtx_count(('pt_feature_vtx', key))
                glBindVertexArray(self._vaos['pt_feature'][key])
                glDrawArraysInstanced(GL_LINES, 0, index_count, len(value))

                glBindVertexArray(self._vaos['point'][key])
                glDrawArraysInstanced(GL_QUADS, 0, 24, len(value))

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
        for key, value in self._items['device'].items():
            glBindVertexArray(self._vaos['device'][key])
            glDrawArraysInstanced(GL_QUADS, 0, 24, len(value))

        # render points for picking
        for key, value in self._items['point'].items():
            glBindVertexArray(self._vaos['point'][key])
            glDrawArraysInstanced(GL_QUADS, 0, 24, len(value))

        glBindVertexArray(0)
        glUseProgram(0)

    def _bind_vao_mat_col_id(self, vao_info: ArrayInfo, mat: glm.array,
        col: glm.array, ids: glm.array):

        name, key = vao_info
        vao = self._vaos[name][key]
        vbo = glGenBuffers(3)
        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, mat.nbytes, mat.ptr, GL_STATIC_DRAW)
        glBindVertexArray(vao)

        # Modelmats.
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(0))
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(16)) # sizeof(glm::vec4)
        glVertexAttribDivisor(3, 1)
        glEnableVertexAttribArray(4)
        glVertexAttribDivisor(4, 1)
        glVertexAttribPointer(
            5, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(32)) # 2 * sizeof(glm::vec4)
        glEnableVertexAttribArray(5)
        glVertexAttribDivisor(5, 1)
        glVertexAttribPointer(
            6, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(48)) # 3 * sizeof(glm::vec4)
        glEnableVertexAttribArray(6)
        glVertexAttribDivisor(6, 1)

        # Colors.
        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, col.nbytes, col.ptr, GL_STATIC_DRAW)
        glVertexAttribPointer(7, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(7)
        glVertexAttribDivisor(7, 1)

        # Ids for picking.
        glBindBuffer(GL_ARRAY_BUFFER, vbo[2])
        glBufferData(GL_ARRAY_BUFFER, ids.nbytes, ids.ptr, GL_STATIC_DRAW)
        # It should be GL_INT here, yet only GL_FLOAT works. huh??
        glVertexAttribPointer(8, 1, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(8)
        glVertexAttribDivisor(8, 1)

        glEnableVertexAttribArray(0)
        glBindVertexArray(0)
        glDeleteBuffers(3, vbo)

    def _bind_device_features(self, vao_info: ArrayInfo, mat: glm.array, col: glm.array):
        name, key = vao_info
        vao = self._vaos[name][key]
        vbo = glGenBuffers(2)
        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, mat.nbytes, mat.ptr, GL_STATIC_DRAW)
        glBindVertexArray(vao)

        # Modelmats.
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(0))
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(16)) # sizeof(glm::vec4)
        glVertexAttribDivisor(3, 1)
        glEnableVertexAttribArray(4)
        glVertexAttribDivisor(4, 1)
        glVertexAttribPointer(
            5, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(32)) # 2 * sizeof(glm::vec4)
        glEnableVertexAttribArray(5)
        glVertexAttribDivisor(5, 1)
        glVertexAttribPointer(
            6, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(48)) # 3 * sizeof(glm::vec4)
        glEnableVertexAttribArray(6)
        glVertexAttribDivisor(6, 1)

        # Colors.
        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, col.nbytes, col.ptr, GL_STATIC_DRAW)
        glVertexAttribPointer(7, 4, GL_FLOAT, GL_FALSE, 352, ctypes.c_void_p(0))
        glEnableVertexAttribArray(7)
        glVertexAttribDivisor(7, 1)

        glEnableVertexAttribArray(0)
        glBindVertexArray(0)
        glDeleteBuffers(2, vbo)

    def _get_dvc_feature_cols(self, item_info: ArrayInfo):
        name, key = item_info
        vertices = self._items[name][key]

        dim_1 = 2 # 2  vec3s: position and color
        dim_2 = 3 # 3 scalars in a vec3
        dim_0 = int(len(vertices) / (dim_1 * dim_2))

        part = vertices.reshape(dim_0, dim_1, dim_2)
        colors = [list(a[1]) for a in part]

        return list(map(lambda a: vec4(*a, 1), colors))

    def _get_dvc_feature_vtx_count(self, item_info: ArrayInfo):
        name, key = item_info
        vertices = self._items[name][key]

        # A feature vertex consists of 2 vec3s for 6 scalars
        return int(len(vertices) / 6)
