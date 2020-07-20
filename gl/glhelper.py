#!/usr/bin/env python3
"""Helper functions for quaternion math, arcball rotation, and paths.
TODO: Give attribution to Printrun
"""

import math
import functools
import numpy as np
from OpenGL.GL import (GL_VERTEX_ARRAY, GL_FLOAT, GL_LINE_STRIP,
                       glEnableClientState, glVertexPointer,
                       glDrawArrays, glDisableClientState)


def arcball(p1x, p1y, p2x, p2y, r):
    """Update arcball rotation."""
    last = sphere_coords(p1x, p1y, r)
    cur = sphere_coords(p2x, p2y, r)
    rot_axis = np.cross(cur, last)

    # calculate angle between last and cur
    d = map(lambda x, y: x - y, last, cur)
    t = math.sqrt(sum(x*x for x in d)) / (2.0 * r)
    if t > 1.0:
        t = 1.0
    if t < -1.0:
        t = -1.0
    phi = 2.0 * math.asin(t)

    return axis_to_quat(rot_axis, phi)


def sphere_coords(x, y, r):
    """Compute the intersection from screen coords to the arcball sphere."""
    d2 = x*x + y*y
    r2 = r * r
    # https://www.khronos.org/opengl/wiki/Object_Mouse_Trackball#Of_mice_and_manipulation
    # combines a sphere and a hyperbolic sheet for smooth transitions
    if math.sqrt(d2) <= r * 0.70710678118654752440:
        return [x, y, math.sqrt(r2 - d2)]
    return [x, y, r2 * 0.5 / math.sqrt(d2)]


def axis_to_quat(axis, angle):
    """Convert rotation vector into a quaternion given."""
    mag = math.sqrt(sum(x * x for x in axis))
    q = [x * (1 / mag) for x in axis]
    q = [x * math.sin(angle / 2.0) for x in q]
    q.append(math.cos(angle / 2.0))
    return q


def quat_to_matrix4(quat):
    """Convert quaternion into a 4x4 rotation matrix."""
    x, y, z, w = quat
    xx2 = 2.0 * x * x
    yy2 = 2.0 * y * y
    zz2 = 2.0 * z * z
    wx2 = 2.0 * w * x
    wy2 = 2.0 * w * y
    wz2 = 2.0 * w * z
    xy2 = 2.0 * x * y
    xz2 = 2.0 * x * z
    yz2 = 2.0 * y * z
    return np.array([
        1.0 - yy2 - zz2, xy2 - wz2, xz2 + wy2, 0.0,
        xy2 + wz2, 1.0 - xx2 - zz2, yz2 - wx2, 0.0,
        xz2 - wy2, yz2 + wx2, 1.0 - xx2 - yy2, 0.0,
        0.0, 0.0, 0.0, 1.0])


def quat_to_matrix3(quat):
    """Convert quaternion into a 3x3 rotation matrix."""
    x, y, z, w = quat
    xx2 = 2.0 * x * x
    yy2 = 2.0 * y * y
    zz2 = 2.0 * z * z
    wx2 = 2.0 * w * x
    wy2 = 2.0 * w * y
    wz2 = 2.0 * w * z
    xy2 = 2.0 * x * y
    xz2 = 2.0 * x * z
    yz2 = 2.0 * y * z
    return np.array([
        [1.0 - yy2 - zz2, xy2 - wz2, xz2 + wy2],
        [xy2 + wz2, 1.0 - xx2 - zz2, yz2 - wx2],
        [xz2 - wy2, yz2 + wx2, 1.0 - xx2 - yy2]])


def mul_quat(quat1, quat2):
    """Compute the product of two quaternions."""
    x1, y1, z1, w1 = quat1
    x2, y2, z2, w2 = quat2
    return [
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]


def rotate_basis(v0, v1, v2):
    """Compute normal basis vectors after a change of basis.
    Calculates rotation matrix such that R*(0,0,1) = v."""
    v = np.array([v0, v1, v2])
    if not v.any():
        raise ValueError('zero magnitude vector')
    v = v / math.sqrt(v0*v0 + v1*v1 + v2*v2)
    x = np.array([1, 0, 0]) # x axis normal basis vector
    z = np.array([0, 0, 1]) # z axis normal basis vector

    # rotate such that that the basis vector for the y axis (up) aligns with v
    if (v != np.array([0, 0, 1])).any():
        phi = math.acos(v[1])                   # np.dot(v, [0, 1, 0])
        axis = (v[2], 0.0, -v[0])               # np.cross([0, 1, 0], v)
        rot = quat_to_matrix3(axis_to_quat(axis, phi))
        x = [rot[0][0], rot[1][0], rot[2][0]]   # rot.dot(x)
        z = [rot[0][2], rot[1][2], rot[2][2]]   # rot.dot(z)
    return x, v, z


def draw_circle(*args):
    """Wrapper function to draw circle."""
    draw_circle_memoized(*args)


def draw_helix(*args):
    """Wrapper function to draw helix."""
    draw_helix_memoized(*args)


def draw_circle_memoized(p, n, r, sides=64):
    """Draw circle given point, normal vector, radius, and # sides.
    Uses the function compute_circle to generate points.
    """
    vertices, count = compute_circle(*p, *n, r, sides)

    # draw vertices
    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, vertices)
    glDrawArrays(GL_LINE_STRIP, 0, count)
    glDisableClientState(GL_VERTEX_ARRAY)


def draw_helix_memoized(p, n, r, pitch=1, turns=1.0, sides=64):
    """Draw helix given point, normal vector, radius, pitch, # turns, and # sides.
    Uses the function compute_helix to generate points.
    """
    vertices, count = compute_helix(*p, *n, r, pitch, turns, sides)

    # draw vertices
    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, vertices)
    glDrawArrays(GL_LINE_STRIP, 0, count)
    glDisableClientState(GL_VERTEX_ARRAY)


def compute_circle(p0, p1, p2, n0, n1, n2, r, sides):
    """Compute vertices of circle given point, normal vector, radius, and # sides.
    Uses an approximation method to compute vertices versus many trig calls.
    """
    a, _, n = rotate_basis(n0, n1, n2)
    theta = 6.28318530717958647692 / sides
    tangential_factor = math.tan(theta)
    radial_factor = math.cos(theta)

    x, y, z = r * a[0], r * a[1], r * a[2]
    count = sides + 1
    vertices = np.empty(count * 3)
    for i in range(count):
        vertices[i*3] = x + p0
        vertices[i*3 + 1] = y + p1
        vertices[i*3 + 2] = z + p2
        tx = (y*n[2] - z*n[1]) * tangential_factor
        ty = (z*n[0] - x*n[2]) * tangential_factor
        tz = (x*n[1] - y*n[0]) * tangential_factor
        x = (x + tx) * radial_factor
        y = (y + ty) * radial_factor
        z = (z + tz) * radial_factor
    return vertices, count


def compute_helix(p0, p1, p2, n0, n1, n2, r, pitch, turns, sides):
    """Compute vertices of helix given point, normal vector, radius, pitch, # turns, and # sides.
    Uses an approximation method to compute vertices versus many trig calls.
    """
    a, _, n = rotate_basis(n0, n1, n2)
    theta = 6.28318530717958647692 / sides
    tangential_factor = math.tan(theta)
    radial_factor = math.cos(theta)

    x, y, z = r * a[0], r * a[1], r * a[2]
    d0, d1, d2 = n[0]*pitch / sides, n[1]*pitch / sides, n[2]*pitch / sides
    count = int(sides * turns) + 1
    vertices = np.empty(count * 3)
    for i in range(count):
        vertices[i*3] = x + p0 + d0*i
        vertices[i*3 + 1] = y + p1 + d1*i
        vertices[i*3 + 2] = z + p2 + d2*i
        tx = (y*n[2] - z*n[1]) * tangential_factor
        ty = (z*n[0] - x*n[2]) * tangential_factor
        tz = (x*n[1] - y*n[0]) * tangential_factor
        x = (x + tx) * radial_factor
        y = (y + ty) * radial_factor
        z = (z + tz) * radial_factor
    return vertices, count


def draw_circle_trig(p, n, r, sides=36):
    """Draw circle given point, normal vector, radius, and # sides."""
    a, b, n = rotate_basis(*n)
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


def draw_helix_trig(p, n, r, pitch=1, turns=1.0, sides=36):
    """Draw helix given point, normal vector, radius, pitch, # turns, and # sides."""
    a, b, n = rotate_basis(*n)
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
