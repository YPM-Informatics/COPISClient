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

"""ViewCube class.

TODO: Start animation when snapping to view rather than instant
TODO: Add text labels to viewcube sides
"""

from typing import Tuple, Union

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

import glm
from enums import ViewCubePos, ViewCubeSize


class GLViewCube:
    """Manage a ViewCube object in a GLCanvas.

    Args:
        parent: Pointer to a parent GLCanvas.
        position: Optional; An enums.ViewCubePos constant representing which
            corner of the viewport the ViewCube should render in. Defaults to
            ViewCubePos.TOP_RIGHT.
        size: Optional; An enums.ViewCubeSize constant representing the size in
            pixels of the ViewCube render area. Defaults to ViewCubeSize.MEDIUM.

    Attributes:
        hover_id: An integer indicating which face of the ViewCube the mouse is
            hovering over.
        hovered: A boolean indicating if the mouse has hovered over a face of
            the ViewCube or not.
        selected: A boolean indicating if the mouse has selected a face of the
            ViewCube or not.
        position: See Args section.
        size: See Args section.
    """

    def __init__(self, parent,
                 position: Union[str, ViewCubePos] = ViewCubePos.TOP_RIGHT,
                 size: Union[int, ViewCubeSize] = ViewCubeSize.MEDIUM) -> None:
        """Inits GLViewCube with constructors."""
        self.parent = parent
        self._position = position if position in ViewCubePos else ViewCubePos.TOP_RIGHT
        self._size = size if size in ViewCubeSize else ViewCubeSize.MEDIUM

        self._vao = None
        self._vao_picking = None
        self._vao_outline = None

        self._hover_id = -1
        self._hovered = False
        self._selected = False
        self._initialized = False

    def create_vaos(self) -> None:
        """Bind VAOs to define vertex data."""
        self._vao, self._vao_picking, self._vao_outline = glGenVertexArrays(3)
        vbo = glGenBuffers(6)

        vertices = np.array([
            1.0, 1.0, 1.0, 0.7, 0.7, 0.7,
            1.0, -1.0, 1.0, 0.5, 0.5, 0.5,
            1.0, -1.0, -1.0, 0.5, 0.5, 0.5,
            1.0, 1.0, -1.0, 0.7, 0.7, 0.7,
            -1.0, 1.0, -1.0, 0.7, 0.7, 0.7,
            -1.0, 1.0, 1.0, 0.7, 0.7, 0.7,
            -1.0, -1.0, 1.0, 0.5, 0.5, 0.5,
            -1.0, -1.0, -1.0, 0.5, 0.5, 0.5,
        ], dtype=np.float32)
        indices = np.array([
            0, 1, 2, 2, 3, 0,
            0, 3, 4, 4, 5, 0,
            0, 5, 6, 6, 1, 0,
            1, 6, 7, 7, 2, 1,
            7, 4, 3, 3, 2, 7,
            4, 7, 6, 6, 5, 4,
        ], dtype=np.uint16)
        glBindVertexArray(self._vao)
        # standard viewcube

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

        # ---

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
            1.0, -1.0, -1.0,    # 2
        ], dtype=np.float32)
        colors = np.zeros(72, dtype=np.float32)
        colors[::3] = np.arange(6).repeat(4) / 255.0
        glBindVertexArray(self._vao_picking)
        # viewcube for picking

        glBindBuffer(GL_ARRAY_BUFFER, vbo[3])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[4])
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        # ---

        colors_border = np.tile(np.array([0.0000, 0.4088, 0.9486], dtype=np.float32), 24)
        glBindVertexArray(self._vao_outline)
        # outlined face of viewcube

        glBindBuffer(GL_ARRAY_BUFFER, vbo[3])
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[5])
        glBufferData(GL_ARRAY_BUFFER, colors_border.nbytes, colors_border, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        # ---

        glBindVertexArray(0)
        glDeleteBuffers(6, vbo)

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
        """Render ViewCube to canvas."""
        if not self.init():
            return

        glViewport(*self.get_viewport())

        proj = glm.ortho(-2.3, 2.3, -2.3, 2.3, -2.3, 2.3)
        modelview = glm.mat4_cast(self.parent.rot_quat)

        glUseProgram(self.parent.get_shader_program())
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(modelview))

        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, 36, GL_UNSIGNED_SHORT, ctypes.c_void_p(0))

        self._render_highlighted()

        glBindVertexArray(0)
        glUseProgram(0)

    def render_for_picking(self) -> None:
        """Render ViewCube for picking pass."""
        if not self.init():
            return

        glViewport(*self.get_viewport())

        proj = glm.ortho(-2.3, 2.3, -2.3, 2.3, -2.3, 2.3)
        modelview = glm.mat4_cast(self.parent.rot_quat)

        glUseProgram(self.parent.get_shader_program())
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(modelview))
        glBindVertexArray(self._vao_picking)
        glDrawArrays(GL_QUADS, 0, 24)
        glBindVertexArray(0)
        glUseProgram(0)

    def _render_highlighted(self) -> None:
        """Render cube outline on face that is hovered."""
        if not self._hovered:
            return

        glDisable(GL_DEPTH_TEST)
        glLineWidth(2.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        glBindVertexArray(self._vao_outline)
        glDrawArrays(GL_QUADS, self._hover_id * 4, 4)

        glEnable(GL_DEPTH_TEST)
        glLineWidth(1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def get_viewport(self) -> Tuple[int, int, int, int]:
        """Return (x, y, width, height) to set viewport according to position.
        """
        canvas_size = self.parent.get_canvas_size()
        width, height = canvas_size.width, canvas_size.height
        if self._position == ViewCubePos.TOP_LEFT:
            corner = (0, height - self._size)
        elif self._position == ViewCubePos.TOP_RIGHT:
            corner = (width - self._size, height - self._size)
        elif self._position == ViewCubePos.BOTTOM_LEFT:
            corner = (0, 0)
        else: # self._position == ViewCubePos.BOTTOM_LEFT:
            corner = (width - self._size, 0)
        return corner[0], corner[1], self._size, self._size

    # --------------------------------------------------------------------------
    # Accessor methods
    # --------------------------------------------------------------------------

    @property
    def hover_id(self) -> int:
        """Return int corresponding to hovered face. -1 if not hovered.

        0: front, 1: top, 2: right, 3: bottom, 4: left, 5: back.
        """
        return self._hover_id

    @hover_id.setter
    def hover_id(self, value: int) -> None:
        """Set hover_id. Checks if value is a valid side."""
        self._hover_id = value
        if self._hover_id < 0 or self._hover_id > 5:
            self._hovered = False
        else:
            self._hovered = True

    @property
    def hovered(self) -> bool:
        return self._hovered

    @hovered.setter
    def hovered(self, value: bool) -> None:
        self._hovered = value

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool) -> None:
        self._selected = value

    @property
    def position(self) -> Union[str, ViewCubePos]:
        return self._position

    @position.setter
    def position(self, value: ViewCubePos) -> None:
        if value not in ViewCubePos:
            return
        self._position = value
        self._initialized = False

    @property
    def size(self) -> Union[int, ViewCubeSize]:
        return self._size

    @size.setter
    def size(self, value: ViewCubeSize) -> None:
        if value not in ViewCubeSize:
            return
        self._size = value
        self._initialized = False
