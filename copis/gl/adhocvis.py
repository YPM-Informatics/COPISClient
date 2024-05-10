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

"""GLAdHocMeshes class.

TODO: on ntf_o_list_changed, update only vao's which have been modified, not everything
"""

from dataclasses import dataclass

from typing import List

from glm import vec3, vec4
import glm

from OpenGL.GL import (
    GL_FILL, GL_FLOAT, GL_FALSE, GL_ARRAY_BUFFER, GL_LINES, GL_STATIC_DRAW,GL_FRONT_AND_BACK, GL_LINE,
    GL_UNSIGNED_INT, GL_TRIANGLES, GL_QUADS, GL_ELEMENT_ARRAY_BUFFER,GL_LINE_SMOOTH,
    glGenVertexArrays, glDrawElements, glGenBuffers, glUniform4fv,
    glUniformMatrix4fv,
    glBindVertexArray, glBindBuffer, glBufferData, glEnableVertexAttribArray, glPolygonMode,
    glVertexAttribPointer, glUniform1i, glUseProgram, glDisable, glEnable, glFrontFace)

from OpenGL.GLU import ctypes

from copis.classes import CylinderObject3D, OBJObject3D, AABoxObject3D
from copis.gl.glutils import get_cylinder_vertices, get_aabb_vertices
from copis.globals import MAX_ID


@dataclass
class AdHocObj3D():
    """Object mesh."""
    color: glm.vec4
    count: int
    vao: ctypes.c_void_p
    object_id: int
    selected: bool

@dataclass
class AdHocBBox():
    """Object mesh."""
    lower: vec3
    upper: vec3

class GLAdHocs:
    """Manage proxy object rendering in a GLCanvas."""

    def __init__(self, parent):
        """Initialize GLActionVis with constructors."""
        self.parent = parent
        self.core = self.parent.core
        self._initialized = False

        self._meshes: List[AdHocObj3D] = []
        #self._bboxes: List[AdHocBBox] = []

    def init(self) -> bool:
        """Initialize for rendering."""
        if self._initialized:
            return True
        self.update_objects()
        
        self._initialized = True
        return True

                            
    def update_objects(self) -> None:
        """Update proxy objects when object list changes.

        Called from GLCanvas upon ntf_o_list_changed signal.
        """
        self._meshes.clear()

        for obj_id, object3d in enumerate(self.core.project.adhocs):
            #object3d = (AABoxObject3D(bbox.lower, bbox.upper))
            vertices: glm.array = None
            normals: glm.array = None
            indices: glm.array = None
            vertices, normals, indices = get_aabb_vertices(object3d)
            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)
            vbo = glGenBuffers(3)
            # vertices
            glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)

            # normals
            glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
            glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals.ptr, GL_STATIC_DRAW)
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(1)

            # indices
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo[2])
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices.ptr, GL_STATIC_DRAW)
        
            self._meshes.append(AdHocObj3D(color=vec4(0.1, 0.8, 0.8, 0.15), count=indices.length * 3, vao=vao, object_id=obj_id, selected=False))
            glBindVertexArray(0)

    def render(self) -> None:
        """Render proxy objects to canvas with a diffuse shader."""
        if not self.init():
            return
        #glDisable(GL_LINE_SMOOTH)
        proj = self.parent.projection_matrix
        view = self.parent.modelview_matrix
        
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glUseProgram(self.parent.shaders['diffuse'])
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))

        for mesh in self._meshes:
            glBindVertexArray(mesh.vao)
            glUniform4fv(2, 1, glm.value_ptr(mesh.color))
            glUniform1i(3, int(mesh.selected))
            glDrawElements(GL_TRIANGLES, mesh.count, GL_UNSIGNED_INT, ctypes.c_void_p(0))

        glBindVertexArray(0)
        glUseProgram(0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        #glEnable(GL_LINE_SMOOTH)

    def render_for_picking(self) -> None:
        """Render proxy objects for picking pass."""
        print("rfp")
        if not self.init():
           return
        proj = self.parent.projection_matrix
        view = self.parent.modelview_matrix
        
        glUseProgram(self.parent.shaders['solid'])
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))
        
        for mesh in self._meshes:
           glBindVertexArray(mesh.vao)
           glUniform1i(2, MAX_ID - mesh.object_id)
           glDrawElements(GL_TRIANGLES, mesh.count, GL_UNSIGNED_INT, ctypes.c_void_p(0))
        
        glBindVertexArray(0)
        glUseProgram(0)
        
        glBindVertexArray(0)
        glUseProgram(0)

    @property
    def objects(self) -> List[AdHocObj3D]:
        """List of meshes."""
        return self._meshes

