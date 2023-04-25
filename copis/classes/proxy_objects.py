# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""Define proxy objects. Abstract base class is Object3D.

Classes:
    AABoxObject3D, CylinderObject3D, OBJObject3D.
"""

from abc import ABC, abstractmethod
from math import inf

from glm import vec3, vec4, mat4, u32vec3
import glm
import pywavefront

from copis.models.geometries import BoundingBox, Point3
from copis.mathutils import orthonormal_basis_of


class Object3D(ABC):
    """Abstract base class for 3D proxy objects."""

    def __init__(self):
        self.selected: bool = False

    @abstractmethod
    def is_point_inside(self, v: Point3, epsilon: float) -> bool:
        """Return whether vec3 is inside or not with a buffer (epsilon)."""
        raise NotImplementedError(f'You must implement the is_point_inside method in {self.__class__}.')

    @property
    @abstractmethod
    def bbox(self) -> BoundingBox:
        """Return bbox of object."""
        raise NotImplementedError(f'You must implement the bbox method in {self.__class__}.')

    @abstractmethod
    def __repr__(self) -> str:
        pass


class AABoxObject3D(Object3D):
    """Axis-aligned box object."""

    def __init__(self, lower: Point3, upper: Point3):
        super().__init__()
        self.lower: Point3 = lower
        self.upper: Point3 = upper
        self._bbox = BoundingBox(self.lower, self.upper)

    def is_point_inside(self, v: Point3, epsilon: float) -> bool:
        return self._bbox.is_point_inside(v, epsilon)

    @property
    def bbox(self) -> BoundingBox:
        return self._bbox

    def __repr__(self) -> str:
        return ('AABoxObject3D(' +
            f'lower={repr(self.lower)}, ' +
            f'upper={repr(self.upper)})')


class CylinderObject3D(Object3D):
    """Cylinder object."""

    def __init__(self, start: vec3, end: vec3, radius: float):
        super().__init__()
        self.start: vec3 = vec3(start)
        self.end: vec3 = vec3(end)
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

        # Inflate OBB into AABB.
        self._bbox = BoundingBox(Point3(*[inf] * 3), Point3(*[-inf] * 3))
        for v in points:
            self._bbox.extend_to_point(vec3(vec4(v, 1.0) * self.trans_matrix))

    def is_point_inside(self, v: Point3, epsilon: float) -> bool:
        return self._bbox.is_point_inside(v, epsilon)
        # TODO: rather than use the bbox, compute distance to cylinder

    @property
    def bbox(self) -> BoundingBox:
        return self._bbox

    def __repr__(self) -> str:
        return ('CylinderObject3D(' +
            f'start={self.start}, ' +
            f'end={self.end}, ' +
            f'radius={self.radius})')


class OBJObject3D(Object3D):
    """.obj object. TODO"""

    def __init__(self, filename: str, scale: Point3=Point3(1.0, 1.0, 1.0)):
        super().__init__()
        self._filename = filename

        self.vertices: glm.array
        self.normals: glm.array
        self.indices: glm.array

        self.obj = pywavefront.Wavefront(filename)
        for _, material in self.obj.materials.items():
            v = material.vertices
            v = [v[i:i + 8] for i in range(0, len(v), 8)]

            self.vertices = glm.array([(Point3(*chunk[5:8]) * scale).to_vec3() for chunk in v])
            self.normals = glm.array([Point3(*chunk[2:5]).to_vec3() for chunk in v])
            self.indices = \
                glm.array([u32vec3(i*3, i*3+1, i*3+2) for i in range(len(self.vertices) // 3)])

            # only use first mesh
            break

        # create bbox
        self._bbox = BoundingBox(Point3(*[inf] * 3), Point3(*[-inf] * 3))
        for v in self.vertices:
            self._bbox.extend_to_point(v)

    def is_point_inside(self, v: Point3, epsilon: float) -> bool:
        return self._bbox.is_point_inside(v, epsilon)

    @property
    def bbox(self) -> BoundingBox:
        return self._bbox

    def __repr__(self) -> str:
        return ('OBJObject3D(' +
            f'filename=\'{self._filename}\')')
