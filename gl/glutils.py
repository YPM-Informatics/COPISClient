#!/usr/bin/env python3
"""Helper functions for quaternion math, arcball rotation, and paths.
TODO: Give attribution to Printrun
"""

from math import acos, asin, cos, sin, sqrt, tan
from typing import List, Optional, Tuple

import numpy as np

import glm


def arcball(
    p1x: float, p1y: float, p2x: float, p2y: float, r: float) -> glm.quat:
    """Return updated quaternion after arcball rotation.

    Args:
        p1x: Previous screen x-coordinate, normalized.
        p1y: Previous screen y-coordinate, normalized.
        p2x: Current screen x-coordinate, normalized.
        p2y: Current screen y-coordinate, normalized.
        r: Radius of arcball.
    """
    p1 = glm.vec3(p1x, p1y, project_to_sphere(r, p1x, p1y))
    p2 = glm.vec3(p2x, p2y, project_to_sphere(r, p2x, p2y))
    axis = glm.normalize(glm.cross(p1, p2))

    # calculate angle between p1 and p2
    d = map(lambda x, y: x - y, p1, p2)
    t = sqrt(sum(x * x for x in d)) / (2.0 * r)
    if t > 1.0:
        t = 1.0
    if t < -1.0:
        t = -1.0
    phi = 2.0 * asin(t)

    return glm.angleAxis(phi, axis)

def project_to_sphere(r: float, x: float, y: float) -> float:
    """Return intersection position from screen coords to the arcball.

    See https://www.khronos.org/opengl/wiki/Object_Mouse_Trackball for how
    points outside the arcball are handled.

    Args:
        r: A float for radius.
        x: Screen x-coordinate, normalized.
        y: Screen y-coordinate, normalized.
    """
    d = sqrt(x * x + y * y)

    # combines a sphere and a hyperbolic sheet for smooth transitions
    if d < r * 0.70710678118654752440:
        return sqrt(r * r - d * d)
    t = r / 1.41421356237309504880
    return t * t / d


def rotate_basis_to(v: glm.vec3) -> Tuple[glm.vec3, glm.vec3, glm.vec3]:
    """Return normal basis vectors such that R * <0,0,1> = v.

    Args:
        v: A glm.vec3 to rotate to. Does not need to be normalized.

    Raises:
        ValueError: If vector provided is zero.
    """
    if not glm.equal(v, glm.vec3()):
        raise ValueError('zero magnitude vector')
    v = v / glm.length(v)
    x = glm.vec3(1, 0, 0) # x axis normal basis vector
    z = glm.vec3(0, 0, 1) # z axis normal basis vector

    # rotate such that that the basis vector for the y axis (up) aligns with v
    if not glm.equal(v, glm.vec3(0, 1, 0)):
        phi = acos(v.x)                         # glm.dot(v, glm.vec3(0, 1, 0))
        axis = glm.vec3(v.z, 0.0, -v.x)         # glm.cross(glm.vec3(0, 1, 0), v)
        rot = glm.mat3_cast(glm.angleAxis(phi, axis))
        x = glm.dot(rot, x)
        z = glm.dot(rot, z)
    return x, v, z


def get_circle(p: glm.vec3,
               n: glm.vec3,
               r: float,
               sides: Optional[int] = 36) -> Tuple[np.ndarray, int]:
    """Create circle vertices given point, normal vector, radius, and # sides.

    Uses an approximation method to compute vertices versus many trig calls.
    """
    a, _, n = rotate_basis_to(n)
    theta = 6.28318530717958647692 / sides
    tangential_factor = tan(theta)
    radial_factor = cos(theta)

    x, y, z = a * r
    count = sides + 1
    vertices = np.empty(count * 3)
    for i in range(count):
        vertices[i * 3] = x + p.x
        vertices[i * 3 + 1] = y + p.y
        vertices[i * 3 + 2] = z + p.z
        tx = (y * n.z - z * n.y) * tangential_factor
        ty = (z * n.x - x * n.z) * tangential_factor
        tz = (x * n.y - y * n.x) * tangential_factor
        x = (x + tx) * radial_factor
        y = (y + ty) * radial_factor
        z = (z + tz) * radial_factor
    return vertices, count


def get_helix(p: glm.vec3,
              n: glm.vec3,
              r: float,
              pitch: Optional[int] = 1,
              turns: Optional[float] = 1.0,
              sides: Optional[int] = 36) -> Tuple[np.ndarray, int]:
    """Create helix vertices given point, normal vector, radius, pitch, # turns, and # sides.

    Uses an approximation method rather than trig functions.
    """
    a, _, n = rotate_basis_to(n)
    theta = 6.28318530717958647692 / sides
    tangential_factor = tan(theta)
    radial_factor = cos(theta)

    x, y, z = a * r
    d = n * pitch / sides
    count = int(sides * turns) + 1
    vertices = np.empty(count * 3)
    for i in range(count):
        vertices[i * 3] = x + p.x + d.x * i
        vertices[i * 3 + 1] = y + p.y + d.y * i
        vertices[i * 3 + 2] = z + p.z + d.z * i
        tx = (y * n.z - z * n.y) * tangential_factor
        ty = (z * n.x - x * n.z) * tangential_factor
        tz = (x * n.y - y * n.x) * tangential_factor
        x = (x + tx) * radial_factor
        y = (y + ty) * radial_factor
        z = (z + tz) * radial_factor
    return vertices, count


def get_circle_trig(p, n, r, sides=36):
    a, b, n = rotate_basis_to(glm.vec3(*n))
    tau = 6.28318530717958647692

    count = sides + 1
    vertices = np.empty(count * 3)
    for i in range(count):
        vertices[i*3] = p[0] + r*(a[0]*cos(i*tau/sides) + b[0]*sin(i*tau/sides))
        vertices[i*3 + 1] = p[1] + r*(a[1]*cos(i*tau/sides) + b[1]*sin(i*tau/sides))
        vertices[i*3 + 2] = p[2] + r*(a[2]*cos(i*tau/sides) + b[2]*sin(i*tau/sides))
    return vertices, count


def get_helix_trig(p, n, r, pitch=1, turns=1.0, sides=36):
    a, b, n = rotate_basis_to(glm.vec3(*n))
    tau = 6.28318530717958647692

    count = int(sides * turns) + 1
    vertices = np.empty(count * 3)
    for i in range(count):
        vertices[i*3] = p[0] + n[0]*(i*pitch/sides) + r*(a[0]*cos(i*tau/sides) + b[0]*sin(i*tau/sides))
        vertices[i*3 + 1] = p[1] + n[1]*(i*pitch/sides) + r*(a[1]*cos(i*tau/sides) + b[1]*sin(i*tau/sides))
        vertices[i*3 + 2] = p[2] + n[2]*(i*pitch/sides) + r*(a[2]*cos(i*tau/sides) + b[2]*sin(i*tau/sides))
    return vertices, count
