#!/usr/bin/env python3
"""Helper functions for quaternion math and arcball rotation.
TODO: Give attribution to Printrun
"""

import math
import numpy as np
from OpenGL.GL import (GL_VERTEX_ARRAY, GL_FLOAT, GL_LINE_STRIP,
    glEnableClientState, glVertexPointer, glDrawArrays, glDisableClientState)


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
    """Convert quaternion into a 4x4 rotation matrix."""
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


def rotate_to(v):
    """Compute normal basis vectors after a change of basis.
    Calculates rotation matrix such that R*(0,0,1) = v."""
    v = np.array(v)
    if not v.any():
        raise ValueError('zero magnitude vector')
    v = v / np.linalg.norm(v)
    x = np.array([1, 0, 0]) # x axis normal basis vector
    y = np.array([0, 1, 0]) # y axis normal basis vector

    # rotate such that that the basis vector for the z axis aligns with v
    if (v != np.array([0, 0, 1])).any():
        phi = math.acos(np.dot(v, np.array([0, 0, 1])))
        axis = np.cross(v, np.array([0, 0, 1]))
        rot = quat_to_matrix(vector_to_quat(axis.tolist(), phi)).reshape(4, 4)[:3, :3]
        x = rot.dot(x)
        y = rot.dot(y)
    return x, y, v


def draw_circle(p, n, r, sides=36):
    """Draw circle given point, normal vector, radius, and # sides."""
    a, b, n = rotate_to(n)
    tau = 6.28318530717958647692

    count = sides + 1
    vertices = np.empty(count * 3)
    for i in range(count):
        vertices[i*3] = p[0] + r*(a[0]*math.cos(i*tau/sides) + b[0]*math.sin(i*tau/sides))
        vertices[i*3 + 1] = p[1] + r*(a[1]*math.cos(i*tau/sides) + b[1]*math.sin(i*tau/sides))
        vertices[i*3 + 2] = p[2] + r*(a[2]*math.cos(i*tau/sides) + b[2]*math.sin(i*tau/sides))

    # draw vertices
    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, vertices)
    glDrawArrays(GL_LINE_STRIP, 0, count)
    glDisableClientState(GL_VERTEX_ARRAY)


def draw_helix(p, n, r, pitch=1, turns=1.0, sides=36):
    """Draw helix given point, normal vector, radius, pitch, # turns, and # sides."""
    a, b, n = rotate_to(n)
    tau = 6.28318530717958647692

    count = int(sides * turns) + 1
    vertices = np.empty(count * 3)
    for i in range(count):
        vertices[i*3] = p[0] + n[0]*(i*pitch/sides) + r*(a[0]*math.cos(i*tau/sides) + b[0]*math.sin(i*tau/sides))
        vertices[i*3 + 1] = p[1] + n[1]*(i*pitch/sides) + r*(a[1]*math.cos(i*tau/sides) + b[1]*math.sin(i*tau/sides))
        vertices[i*3 + 2] = p[2] + n[2]*(i*pitch/sides) + r*(a[2]*math.cos(i*tau/sides) + b[2]*math.sin(i*tau/sides))

    # draw vertices
    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, vertices)
    glDrawArrays(GL_LINE_STRIP, 0, count)
    glDisableClientState(GL_VERTEX_ARRAY)
