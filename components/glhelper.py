#!/usr/bin/env python3
"""Helper functions for quaternion math and arcball rotation.
TODO: Give attribution to Printrun
"""

import math
import numpy as np


def arcball(p1x, p1y, p2x, p2y, r):
    """Update arcball rotation."""
    last = sphere_coords(p1x, p1y, r)
    cur = sphere_coords(p2x, p2y, r)
    rot_axis = np.cross(cur, last)

    # calculate angle between last and cur
    d = map(lambda x, y: x - y, last, cur)
    t = math.sqrt(sum(x*x for x in d)) / (2.0*r)
    if t > 1.0:
        t = 1.0
    if t < -1.0:
        t = -1.0
    phi = 2.0 * math.asin(t)

    return vector_to_quat(rot_axis, phi)


def sphere_coords(x, y, r):
    """Compute the intersection from screen coords to the arcball sphere."""
    d2 = x*x + y*y
    r2 = r * r
    if math.sqrt(d2) <= r * 0.70710678118654752440:
        # use pythagorean theorem to compute point on sphere
        return [x, y, math.sqrt(r2 - d2)]
    # if out of bounds, find the nearest point
    return np.array([x, y, r2 * 0.5 / math.sqrt(d2)])


def vector_to_quat(axis, angle):
    """Convert rotation vector into a quaternion given."""
    axis_len = math.sqrt(sum(x*x for x in axis))
    q = [x*(1 / axis_len) for x in axis]
    q = [x*math.sin(angle / 2.0) for x in q]
    q.append(math.cos(angle / 2.0))
    return [q[3], q[0], q[1], q[2]]


def quat_to_matrix(quat):
    """Convert quaternion into a 4x4 rotation matrix.
    """
    w, x, y, z = quat
    return np.array([
        1.0 - 2.0*y*y - 2.0*z*z, 2.0*x*y - 2.0*w*z, 2.0*x*z + 2.0*w*y, 0.0,
        2.0*x*y + 2.0*w*z, 1.0 - 2.0*x*x - 2.0*z*z, 2.0*y*z - 2.0*w*x, 0.0,
        2.0*x*z - 2.0*w*y, 2.0*y*z + 2.0*w*x, 1.0 - 2.0*x*x - 2.0*y*y, 0.0,
        0.0, 0.0, 0.0, 1.0])


def mul_quat(quat1, quat2):
    """Compute the product of two quaternions."""
    w1, x1, y1, z1 = quat1
    w2, x2, y2, z2 = quat2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2])
