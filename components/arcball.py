#!/usr/bin/env python3
"""Helper math functions to implement arcball rotation.
TODO: Give attribution to Printrun
"""

import math
from OpenGL.GL import GLfloat


def arcball(p1x, p1y, p2x, p2y, r):
    """Update arcball rotation."""
    last = sphere_coords(p1x, p1y, r)
    cur = sphere_coords(p2x, p2y, r)
    rot_axis = cross(cur, last)

    # calculate angle between last and cur
    d = map(lambda x, y: x - y, last, cur)
    t = math.sqrt(sum(x*x for x in d)) / (2.0*r)
    if t > 1.0:
        t = 1.0
    if t < -1.0:
        t = -1.0
    phi = 2.0 * math.asin(t)

    return axis_to_quat(rot_axis, phi)


def dot(a, b):
    """Compute the dot product of two vectors."""
    return sum([i*j for (i, j) in zip(a, b)])


def cross(a, b):
    """Compute the cross product of two vectors."""
    return [a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0]]


def axis_to_quat(axis, angle):
    """Compute the quaternion given rotation axis and angle."""
    axis_len = math.sqrt(sum(x*x for x in axis))
    q = [x*(1 / axis_len) for x in axis]
    q = [x*math.sin(angle / 2.0) for x in q]
    q.append(math.cos(angle / 2.0))
    return q


def quat_to_mat(q):
    """Convert the quaternion into a rotation matrix.
    x: q[0], y: q[1], z: q[2], w: q[3]
    """
    m = (GLfloat*16)()
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
    """Compute the intersection from screen coords to the arcball sphere."""
    d2 = x*x + y*y
    r2 = r * r
    if math.sqrt(d2) <= r * 0.70710678118654752440:
        # use pythagorean theorem to compute point on sphere
        return [x, y, math.sqrt(r2 - d2)]
    # if out of bounds, find the nearest point
    return [x, y, r2 * 0.5 / math.sqrt(d2)]


def mul_quat(a, b):
    """Compute the product of two quaternions."""
    return [a[3]*b[0] + a[0]*b[3] + a[1]*b[2] - a[2]*b[1], # 1
            a[3]*b[1] + a[1]*b[3] + a[2]*b[0] - a[0]*b[2], # i
            a[3]*b[2] + a[2]*b[3] + a[0]*b[1] - a[1]*b[0], # j
            a[3]*b[3] - a[0]*b[0] - a[1]*b[1] - a[2]*b[2]] # k
