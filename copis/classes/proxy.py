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
from dataclasses import dataclass
from itertools import count

from glm import mat4, vec3
import glm
import pywavefront

from copis.mathutils import orthonormal_basis_of
from copis.helpers import find_path
from . import BoundingBox


@dataclass
class Object3D(ABC):
    """Abstract base class for 3D proxy objects."""

    _ids = count(0)

    def __init__(self):
        self._object_id = next(self._ids)

    def __new__(cls, *args, **kwargs):
        if cls == Object3D or cls.__bases__[0] == Object3D:
            raise TypeError("Cannot instantiate abstract class.")
        return super().__new__(cls)

    @property
    def object_id(self) -> int:
        """Return id of object."""
        return self._object_id

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


@dataclass
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
        self.rot_matrix: mat4 = glm.orientation(vec3(0.0, 0.0, 1.0), self.normal)

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
            self._bbox.vec3_extend(v @ self.rot_matrix)

    def bbox_intersect(self, bbox: BoundingBox) -> bool:
        return self._bbox.bbox_intersect(bbox)

    def vec3_intersect(self, v: vec3) -> bool:
        return self._bbox.vec3_intersect(v)

    @property
    def bbox(self) -> BoundingBox:
        return self._bbox


@dataclass
class AABBOject3D(Object3D):
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


@dataclass
class OBJOject3D(Object3D):
    """.obj object. TODO"""

    def __init__(self, filename: str):
        super().__init__()
        obj = pywavefront.Wavefront(find_path('filename'), create_materials=True)
        for _, _ in obj.materials.items():
            pass

        self._bbox = BoundingBox()

    def bbox_intersect(self, bbox: BoundingBox) -> bool:
        return self._bbox.bbox_intersect(bbox)

    def vec3_intersect(self, v: vec3) -> bool:
        return self._bbox.vec3_intersect(v)

    @property
    def bbox(self) -> BoundingBox:
        return self._bbox
