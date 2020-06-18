#!/usr/bin/env python3
"""Helper math functions to implement arcball rotation."""

import math

from OpenGL.GL import *
from OpenGL.GLU import *


def trackball(p1x, p1y, p2x, p2y, r):
    if p1x == p2x and p1y == p2y:
        return [0.0, 0.0, 0.0, 1.0]

    v1 = [p1x, p1y, sphere_coords(p1x, p1y, r)]
    v2 = [p2x, p2y, sphere_coords(p2x, p2y, r)]
    # rot_axis = cross(v2, v1)
    rot_axis = cross(v1, v2)

    d = map(lambda x, y: x - y, v1, v2)
    t = math.sqrt(sum(x*x for x in d)) / (2.0*r)

    if t > 1.0:
        t = 1.0
    if t < -1.0:
        t = -1.0
    phi = 2.0 * math.asin(t)
    # phi = math.acos(t)

    return axis_to_quat(rot_axis, phi)


def cross(v1, v2):
    """Find the cross product between two vectors."""
    return [v1[1]*v2[2] - v1[2]*v2[1],
            v1[2]*v2[0] - v1[0]*v2[2],
            v1[0]*v2[1] - v1[1]*v2[0]]


def axis_to_quat(a, phi):
    lena = math.sqrt(sum(x*x for x in a))
    q = [x*(1 / lena) for x in a]
    q = [x*math.sin(phi / 2.0) for x in q]
    q.append(math.cos(phi / 2.0))
    return q


def quat_to_rotmatrix(q):
    """Convert from a quaternion to a rotation matrix.
    x: q[0], y: q[1], z: q[2], w: q[3]
    """
    m = (GLdouble*16)()
    m[0] = 1.0 - 2.0*q[1]*q[1] - 2.0*q[2]*q[2]
    m[1] = 2.0*q[0]*q[1] - 2.0*q[2]*q[3]
    m[2] = 2.0*q[2]*q[0] + 2.0*q[1]*q[3]
    m[3] = 0.0

    m[4] = 2.0*q[0]*q[1] + 2.0*q[2]*q[3]
    m[5] = 1.0 - 2.0*q[2]*q[2] - 2.0*q[0]*q[0]
    m[6] = 2.0*q[1]*q[2] - 2.0*q[0]*q[3]
    m[7] = 0.0

    m[8] = 2.0*q[2]*q[0] - 2.0*q[1]*q[3]
    m[9] = 2.0*q[1]*q[2] + 2.0*q[0]*q[3]
    m[10] = 1.0 - 2.0*q[1]*q[1] - 2.0*q[0]*q[0]
    m[11] = 0.0

    m[12] = 0.0
    m[13] = 0.0
    m[14] = 0.0
    m[15] = 1.0
    return m


def sphere_coords(x, y, r):
    """Find the intersection from screen coords to the arcball sphere."""
    d2 = x*x + y*y
    r2 = r * r
    if (math.sqrt(d2) <= r * 0.70710678118654752440):
        return math.sqrt(r2 - d2)
    else:
        return r2 * 0.5 / math.sqrt(d2)


def mul_quat(q1, rq):
    """Multiply two quaternions."""
    return [q1[3]*rq[0] + q1[0]*rq[3] + q1[1]*rq[2] - q1[2]*rq[1],  # 1
            q1[3]*rq[1] + q1[1]*rq[3] + q1[2]*rq[0] - q1[0]*rq[2],  # i
            q1[3]*rq[2] + q1[2]*rq[3] + q1[0]*rq[1] - q1[1]*rq[0],  # j
            q1[3]*rq[3] - q1[0]*rq[0] - q1[1]*rq[1] - q1[2]*rq[2]]  # k
