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

"""GLChamber and associated classes."""

from typing import List, Tuple

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

import glm


class _Axes():
    """Manage and render origin axes in a GLChamber.

    Subclass of GLChamber.

    Args:
        parent: Pointer to a parent GLChamber.
    """

    origin = (0.0, 0.0, 0.0)

    def __init__(self, parent) -> None:
        """Initializes _Axes with constructors."""
        self.parent = parent

        self._vao_axes = None
        self._vao_arrows = None

        build_dimensions = self.parent.build_dimensions
        dist = 0.5 * (build_dimensions[1] + max(build_dimensions[0], build_dimensions[2]))
        self._arrow_base_radius = dist / 75.0
        self._arrow_length = 2.5 * self._arrow_base_radius
        self._quadric = gluNewQuadric()
        gluQuadricDrawStyle(self._quadric, GLU_FILL)

    def create_vaos(self) -> None:
        """Bind VAOs to define vertex data."""
        self._vao_axes, *self._vao_arrows = glGenVertexArrays(3)
        vbo = glGenBuffers(5)

        build_dimensions = self.parent.build_dimensions
        x = build_dimensions[0] - build_dimensions[3], build_dimensions[3]
        y = build_dimensions[1] - build_dimensions[4], build_dimensions[4]
        z = build_dimensions[2] - build_dimensions[5], build_dimensions[5]
        points = np.array([
            x[0], 0.0, 0.0, 1.0, 0.0, 0.0,
            -x[1], 0.0, 0.0, 1.0, 0.0, 0.0,
            0.0, y[0], 0.0, 0.0, 1.0, 0.0,
            0.0, -y[1], 0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, z[0], 0.0, 0.0, 1.0,
            0.0, 0.0, -z[1], 0.0, 0.0, 1.0,
        ], dtype=np.float32)
        glBindVertexArray(self._vao_axes)

        # colored axes lines
        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, points.nbytes, points, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, points.nbytes, points, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        # ---

        vertices, colors = self._get_cones()
        glBindVertexArray(self._vao_arrows[0])

        # colored axes arrows, cone
        glBindBuffer(GL_ARRAY_BUFFER, vbo[2])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[3])
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        # ---

        vertices[0] = x[0]
        vertices[17*3+1] = y[0]
        vertices[17*6+2] = z[0]
        glBindVertexArray(self._vao_arrows[1])

        # colored axes arrows, base
        glBindBuffer(GL_ARRAY_BUFFER, vbo[4])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[3])
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        # ---

        glBindVertexArray(0)
        glDeleteBuffers(5, vbo)

    def render(self) -> None:
        """Render colored axes and arrows."""
        if self._quadric is None:
            return

        glBindVertexArray(self._vao_axes)
        glDrawArrays(GL_LINES, 0, 6)
        glBindVertexArray(self._vao_arrows[0])
        glMultiDrawArrays(GL_TRIANGLE_FAN, (0, 17, 34), (17, 17, 17), 3)
        glFrontFace(GL_CW)
        glBindVertexArray(self._vao_arrows[1])
        glMultiDrawArrays(GL_TRIANGLE_FAN, (0, 17, 34), (17, 17, 17), 3)
        glFrontFace(GL_CCW)

        glBindVertexArray(0)

    def _get_cones(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return vertices and colors to draw colored axes end arrows.

        Draw using:
            glMultiDrawArrays(GL_TRIANGLE_FAN, (0, 17, 34), (17, 17, 17), 3)

        Returns:
            An np.ndarray for vertices, and an np.ndarray for color values.
        """
        x = self.parent.build_dimensions[0] - self.parent.build_dimensions[3]
        y = self.parent.build_dimensions[1] - self.parent.build_dimensions[4]
        z = self.parent.build_dimensions[2] - self.parent.build_dimensions[5]

        thetas = np.linspace(0, 2 * np.pi, 16, endpoint=True)
        cos = np.cos(thetas) * self._arrow_base_radius
        sin = np.sin(thetas) * self._arrow_base_radius
        vertices = np.zeros(9 * 17, dtype=np.float32)

        # x-axis cone
        vertices[0] = x + self._arrow_length
        vertices[3:3*17:3] = x
        vertices[4:3*17:3] = cos
        vertices[5:3*17:3] = sin

        # y-axis cone
        vertices[17*3+1] = y + self._arrow_length
        vertices[3*17+3:6*17:3] = sin
        vertices[3*17+4:6*17:3] = y
        vertices[3*17+5:6*17:3] = cos

        # z-axis cone
        vertices[17*6+2] = z + self._arrow_length
        vertices[6*17+3::3] = cos
        vertices[6*17+4::3] = sin
        vertices[6*17+5::3] = z

        # 17 red, 17 blue, 17 green
        colors = np.zeros(9 * 17, dtype=np.float32)
        colors[:3*17:3] = 0.9
        colors[3*17+1:6*17:3] = 0.9
        colors[6*17+2::3] = 0.9

        return vertices, colors


class GLChamber:
    """Manage build dimensions and chamber bed surface in a GLCanvas.

    Args:
        parent: Pointer to a parent GLCanvas.
        build_dimensions: Optional; A list indicating dimensions and origin.
            First three values specify xyz build dimensions, and last three
            values specificy xyz origin position. Defaults to
            [400, 400, 400, 200, 200, 200] = 400x400x400mm, (200,200,200).
        every: Optional; An integer representing units between every major
            gridline (displayed darker). Defaults to 100.
        subdivisions: Optional; An integer representing subdivisions between
            major gridlines (displayed lighter). Defaults to 10.

    Attributes:
        build_dimensions: See Args section.
        grid_shown: A boolean indicating if chamber gridlines should be rendered
            or not. Defaults to True.
        axes_shown: A boolean indicating if origin axes should be rendered
            or not. Defaults to True.
        bbox_shown: A boolean indicating if a bounding box should be rendered
            or not. Defaults to True.
    """
    col_light = 0.95
    col_dark = 0.80
    col_border = 0.50

    def __init__(self, parent,
                 build_dimensions: List[int] = [400, 400, 400, 200, 200, 200],
                 every: int = 100,
                 subdivisions: int = 10) -> None:
        """Initializes GLChamber with constructors.

        Raises:
            ValueError: If provided build dimension is invalid.
        """
        if not all([0 <= build_dimensions[i+3] <= build_dimensions[i] for i in range(3)]):
            raise ValueError('build dimension origin out of range')
        self.parent = parent
        self._build_dimensions = build_dimensions
        self._every = every
        self._subdivisions = subdivisions

        self._vao_gridlines = None
        self._vao_bounding_box = None
        self._count_gridlines = None
        self._count_bounding_box = None

        self._grid_shown = True
        self._axes_shown = True
        self._bbox_shown = True
        self._axes = _Axes(self)

        self._initialized = False

    def create_vaos(self) -> None:
        """Bind VAOs to define vertex data."""
        self._vao_gridlines, self._vao_bounding_box = glGenVertexArrays(2)
        vbo = glGenBuffers(5)

        vertices, colors = self._get_gridlines()
        self._count_gridlines = vertices.size // 3
        glBindVertexArray(self._vao_gridlines)

        # gridlines
        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        # ---

        points, indices = self._get_bounding_box()
        self._count_bounding_box = indices.length
        glBindVertexArray(self._vao_bounding_box)

        # bounding box
        glBindBuffer(GL_ARRAY_BUFFER, vbo[2])
        glBufferData(GL_ARRAY_BUFFER, points.nbytes, points, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[3])
        glBufferData(GL_ARRAY_BUFFER, points.nbytes, points, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo[4])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices.ptr, GL_STATIC_DRAW)

        self._axes.create_vaos()

        glBindVertexArray(0)
        glDeleteBuffers(5, vbo)

    def init(self) -> bool:
        """Initialize for rendering.

        Returns:
            True if initialized without error, False otherwise.
        """
        if self._initialized:
            return True

        self.create_vaos()

        self._initialized = True
        return True

    def render(self) -> None:
        """Render chamber to canvas."""
        if not self.init():
            return

        glDisable(GL_LINE_SMOOTH)

        proj = self.parent.projection_matrix
        modelview = self.parent.modelview_matrix

        glUseProgram(self.parent.shaders['default'])
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(modelview))

        if self._grid_shown:
            self._render_gridlines()

        if self._axes_shown:
            self._render_axes()

        if self._bbox_shown:
            self._render_bounding_box()

        glBindVertexArray(0)
        glUseProgram(0)
        glEnable(GL_LINE_SMOOTH)

    def _get_gridlines(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return vertices and colors to draw gridlines using GL_LINES.

        Returns:
            An np.ndarray for vertices, and an np.ndarray for color values.
        """
        x = self._build_dimensions[0] - self._build_dimensions[3], self._build_dimensions[3]
        y = self._build_dimensions[1] - self._build_dimensions[4], self._build_dimensions[4]
        step = self._every / self._subdivisions

        def darken(arr):
            arr[self._subdivisions-1::self._subdivisions] = self.col_dark
            arr[-1] = self.col_border
            return arr

        if self._axes_shown:
            axes_verts = np.array([])
            axes_colors = np.array([])
        else:
            axes_verts = np.array([
                x[0], 0.0, 0.0, -x[1], 0.0, 0.0,
                0.0, y[0], 0.0, 0.0, -y[1], 0.0])
            axes_colors = np.array([self.col_dark]).repeat(12)

        # gridlines parallel to x axis
        i = np.append(np.arange(-step, -y[1], -step), -y[1])
        j = np.append(np.arange(step, y[0], step), y[0])
        k = np.concatenate([i, j])
        x_verts = np.zeros(k.size * 6)
        x_verts[1::3] = k.repeat(2)
        x_verts[0::6] = -x[1]
        x_verts[3::6] = x[0]
        x_colors = np.concatenate([
            darken(np.full(i.size, self.col_light)),
            darken(np.full(j.size, self.col_light))]).repeat(6)

        # gridlines parallel to y axis
        i = np.append(np.arange(-step, -x[1], -step), -x[1])
        j = np.append(np.arange(step, x[0], step), x[0])
        k = np.concatenate([i, j])
        y_verts = np.zeros(k.size * 6)
        y_verts[0::3] = k.repeat(2)
        y_verts[1::6] = -y[1]
        y_verts[4::6] = y[0]
        y_colors = np.concatenate([
            darken(np.full(i.size, self.col_light)),
            darken(np.full(j.size, self.col_light))]).repeat(6)

        verts = np.concatenate([axes_verts, x_verts, y_verts]).astype(np.float32)
        colors = np.concatenate([axes_colors, x_colors, y_colors]).astype(np.float32)
        return verts, colors

    def _get_bounding_box(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return vertices and indices to draw bounding box using GL_LINES.

        Returns:
            An np.ndarray for vertices, and an np.ndarray for color values.
        """
        x = self._build_dimensions[0] - self._build_dimensions[3], self._build_dimensions[3]
        y = self._build_dimensions[1] - self._build_dimensions[4], self._build_dimensions[4]
        z = self._build_dimensions[2] - self._build_dimensions[5], self._build_dimensions[5]

        # 8 corners
        points = np.array([
            x[0], y[0], z[0],    self.col_dark, self.col_dark, self.col_dark,
            x[0], -y[1], z[0],   self.col_dark, self.col_dark, self.col_dark,
            x[0], -y[1], -z[1],  self.col_dark, self.col_dark, self.col_dark,
            x[0], y[0], -z[1],   self.col_dark, self.col_dark, self.col_dark,
            -x[1], y[0], -z[1],  self.col_dark, self.col_dark, self.col_dark,
            -x[1], y[0], z[0],   self.col_dark, self.col_dark, self.col_dark,
            -x[1], -y[1], z[0],  self.col_dark, self.col_dark, self.col_dark,
            -x[1], -y[1], -z[1], self.col_dark, self.col_dark, self.col_dark,
        ], dtype=np.float32)

        # 12 edges
        indices = glm.array.from_numbers(ctypes.c_uint,
            0, 1, 1, 2, 2, 3, 3, 0,
            0, 5, 1, 6, 2, 7, 3, 4,
            4, 5, 5, 6, 6, 7, 7, 4,
        )

        return points, indices

    def _render_gridlines(self) -> None:
        """Render gridlines."""
        if self._vao_gridlines is None:
            return

        glBindVertexArray(self._vao_gridlines)
        glDrawArrays(GL_LINES, 0, self._count_gridlines)

    def _render_bounding_box(self) -> None:
        """Render bounding box."""
        if self._vao_bounding_box is None:
            return

        glBindVertexArray(self._vao_bounding_box)
        glDrawElements(GL_LINES, self._count_bounding_box, GL_UNSIGNED_INT, ctypes.c_void_p(0))

    def _render_axes(self) -> None:
        """Render axes if enabled."""
        if self._axes is None:
            return

        self._axes.render()

    # --------------------------------------------------------------------------
    # Accessor methods
    # --------------------------------------------------------------------------

    @property
    def build_dimensions(self) -> List[int]:
        return self._build_dimensions

    @build_dimensions.setter
    def build_dimensions(self, value: List[int]) -> None:
        self._build_dimensions = value
        self._initialized = False

    @property
    def grid_shown(self) -> bool:
        return self._grid_shown

    @grid_shown.setter
    def grid_shown(self, value: bool) -> None:
        self._grid_shown = value
        self.parent.dirty = True

    @property
    def axes_shown(self) -> bool:
        return self._axes_shown

    @axes_shown.setter
    def axes_shown(self, value: bool) -> None:
        self._axes_shown = value
        self.create_vaos()
        self.parent.dirty = True

    @property
    def bbox_shown(self) -> bool:
        return self._bbox_shown

    @bbox_shown.setter
    def bbox_shown(self, value: bool) -> None:
        self._bbox_shown = value
        self.parent.dirty = True
