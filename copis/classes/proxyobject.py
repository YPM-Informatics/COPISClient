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

"""Provide the COPIS Proxy Class."""

from abc import ABC, abstractmethod
from itertools import count

from glm import vec3, vec4, mat4, u32vec3
import glm
import ctypes
import pywavefront

from copis.mathutils import orthonormal_basis_of
from copis.helpers import find_path
from . import BoundingBox


class Object3D(ABC):
    """Abstract base class for 3D proxy objects."""

    _ids = count(0)

    def __init__(self):
        self.object_id: int = next(self._ids)
        self.selected: bool = False

    @abstractmethod
    def bbox_intersect(self, bbox: BoundingBox) -> bool:
        """Return whether bbox intersects or not."""
        pass

    @abstractmethod
    def vec3_intersect(self, v: vec3) -> bool:
        """Return whether vec3 is inside or not."""
        pass

    @property
    @abstractmethod
    def bbox(self) -> BoundingBox:
        """Return bbox of object."""
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


class AABBObject3D(Object3D):
    """Axis-aligned box object."""

    def __init__(self, lower: vec3, upper: vec3):
        super().__init__()
        self.lower: vec3 = lower
        self.upper: vec3 = upper
        self._bbox = BoundingBox(self.lower, self.upper)

    def bbox_intersect(self, bbox: BoundingBox) -> bool:
        return self._bbox.bbox_intersect(bbox)

    def vec3_intersect(self, v: vec3) -> bool:
        return self._bbox.vec3_intersect(v)

    @property
    def bbox(self) -> BoundingBox:
        return self._bbox

    def __repr__(self) -> str:
        return 'AABBObject3D(' + \
               f'lower={repr(self.lower)}, ' + \
               f'upper={repr(self.upper)}, ' + \
               f'object_id={self.object_id}, ' + \
               f'bbox={self._bbox})'


class CylinderObject3D(Object3D):
    """Cylinder object."""

    def __init__(self, start: vec3, end: vec3, radius: float):
        super().__init__()
        self.start: vec3 = start
        self.end: vec3 = end
        self.radius: float = radius

        self.height: float = glm.distance(self.start, self.end)
        self.normal: vec3 = glm.normalize(self.end - self.start)

        self.b1: vec3
        self.b2: vec3
        self.b1, self.b2 = orthonormal_basis_of(self.normal)

        # calculate rotation matrix for cylinder
        self.trans_matrix: mat4 = glm.orientation(vec3(0.0, 0.0, 1.0), self.normal)

        # add translation to matrix
        self.trans_matrix[0][3] = start.x
        self.trans_matrix[1][3] = start.y
        self.trans_matrix[2][3] = start.z

        # get corners of OBB
        points = glm.array(
            vec3(self.radius, self.radius, 0.0),
            vec3(-self.radius, self.radius, 0.0),
            vec3(self.radius, -self.radius, 0.0),
            vec3(-self.radius, -self.radius, 0.0),
            vec3(self.radius, self.radius, self.height),
            vec3(-self.radius, self.radius, self.height),
            vec3(self.radius, -self.radius, self.height),
            vec3(-self.radius, -self.radius, self.height))

        # inflate OBB into AABB
        self._bbox = BoundingBox()
        for v in points:
            self._bbox.vec3_extend(vec3(vec4(v, 1.0) * self.trans_matrix))

    def bbox_intersect(self, bbox: BoundingBox) -> bool:
        return self._bbox.bbox_intersect(bbox)

    def vec3_intersect(self, v: vec3) -> bool:
        return self._bbox.vec3_intersect(v)

    @property
    def bbox(self) -> BoundingBox:
        return self._bbox

    def __repr__(self) -> str:
        return 'CylinderObject3D(' + \
               f'start={self.start}, ' + \
               f'end={self.end}, ' + \
               f'radius={self.radius}, ' + \
               f'object_id={self.object_id}, ' + \
               f'bbox={self._bbox})'


class OBJObject3D(Object3D):
    """.obj object. TODO"""

    def __init__(self, filename: str, scale: vec3 = vec3(1.0)):
        super().__init__()
        self._filename = filename
        self._wavefront_vertices: glm.array
        self.scale = scale

        self.vertices: glm.array
        self.normals: glm.array
        self.indices: glm.array

        self.obj = pywavefront.Wavefront(find_path(filename))
        for _, material in self.obj.materials.items():
            v = material.vertices
            v = [v[i:i + 8] for i in range(0, len(v), 8)]

            self.vertices = glm.array([vec3(chunk[5:8]) * scale for chunk in v])
            self.normals = glm.array([vec3(chunk[2:5]) for chunk in v])
            self.indices = glm.array([u32vec3(i*3, i*3+1, i*3+2) for i in range(len(self.vertices) // 3)])

            # only use first mesh
            break

        self._bbox = BoundingBox()

    def bbox_intersect(self, bbox: BoundingBox) -> bool:
        return self._bbox.bbox_intersect(bbox)

    def vec3_intersect(self, v: vec3) -> bool:
        return self._bbox.vec3_intersect(v)

    @property
    def bbox(self) -> BoundingBox:
        return self._bbox

    def __repr__(self) -> str:
        return 'OBJObject3D(' + \
               f'filename=\'{self._filename}\', ' + \
               f'object_id={self.object_id}, ' + \
               f'bbox={self._bbox})'
