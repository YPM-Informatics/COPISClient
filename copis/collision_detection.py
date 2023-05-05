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

"""Collision detection module."""

import math

from typing import List
from dataclasses import dataclass

from copis.models.geometries import Point3
from copis.models.machine import Device
from copis.project import Project


def collision_eval_cam2cam_path() -> List[dict]:
    """Evaluates 2 cameras' paths and returns poses where collisions are likely to occur."""
    collisions = []
    proj = Project()

    if proj.is_initialized:
        for i in range(0, len(proj.move_sets) -1):
            for k, a in enumerate(proj.devices):
                a_start = proj.last_pose_by_dev_id(i, a.d_id)

                if a_start is not None:
                    a_end = proj.pose_by_dev_id(i + 1, a.d_id)

                    if a_end is None:
                        a_end = a_start

                    for j in range(k + 1, len(proj.devices)):
                        b = proj.devices[j]
                        b_start = proj.last_pose_by_dev_id(i, b.d_id)

                        if b_start is not None:
                            b_end = proj.pose_by_dev_id(i + 1, b.d_id)

                            if b_end is None:
                                b_end = b_start

                            if _is_collision_between_moving_cams(a, a_start, a_end, b, b_start, b_end):
                                collisions.append({'ps_idx': i + 1, 'cams': (a.d_id, b.d_id)})
    return collisions


def collision_eval_cam2proxy_path() -> List[dict]:
    """Evaluates a camera's path around a proxy object and returns poses where collisions are likely to occur."""
    collisions = []
    proj = Project()

    if proj.is_initialized:
        for i in range(0, len(proj.move_sets) -1):
            for dvc in proj.devices:
                dvc_start = proj.last_pose_by_dev_id(i, dvc.d_id)

                if dvc_start is not None:
                    dvc_end = proj.pose_by_dev_id(i + 1, dvc.d_id)

                    if dvc_end is None:
                        dvc_end = dvc_start

                    for proxy in proj.proxies:
                        if _is_collision_between_proxy_cam_move(dvc, dvc_start, dvc_end, proxy.bbox):
                            collisions.append({'ps_idx': i + 1,'cams': (dvc.d_id, -1)})
    return collisions


def collision_eval_cam2proxy_start() -> List[dict]:
    """Evaluates a camera's move to its first pose around a proxy object and returns poses where collisions are likely to occur."""
    collisions = []
    proj = Project()

    if proj.is_initialized:
        if len(proj.move_sets) > 0:
            for device in proj.devices:
                first_pose = proj.first_pose_by_dev_id(0, device.d_id)

                if first_pose is not None:
                    for proxy in proj.proxies:
                        if _is_collision_between_proxy_cam_move(device, device.position.to_point3(), first_pose, proxy.bbox):
                            collisions.append({'ps_idx': -1,'cams': (-1, -1)})
    return collisions


def collision_eval_cam2cam_start() -> List[dict]:
    """Evaluates 2 cameras' move to their first poses and returns poses where collisions are likely to occur."""
    collisions = []
    proj = Project()

    if proj.is_initialized:
        if len(proj.move_sets) > 0:
            for k, a in enumerate(proj.devices):
                first_pose_a = proj.first_pose_by_dev_id(0, a.d_id)

                if first_pose_a is not None:
                    for j in range(k + 1, len(proj.devices)):
                        b = proj.devices[j]
                        first_pose_b = proj.first_pose_by_dev_id(0, b.d_id)

                        if first_pose_b is not None:
                            if _is_collision_between_moving_cams(a, a.position.to_point3(), first_pose_a, b, b.position.to_point3(), first_pose_b):
                                collisions.append({'ps_idx': -1, 'cams': (a.d_id, b.d_id)})
    return collisions


@dataclass
class Sphere:
    """Object representing a sphere with center point and a radius."""
    center:Point3
    radius:float


@dataclass
class Aab:
    """Object representing an axis-aligned box."""
    lower: Point3
    upper: Point3


class CamBounds:
    """Object representing a series of bounding 3d geometries representing the head, body and gantry."""
    def __init__(self, device:Device, pos:Point3):
        head_radius = device.head_radius #200
        body_width = device.z_body_dims.width #100
        body_depth = device.z_body_dims.depth #40
        body_height= device.z_body_dims.height * device.gantry_orientation #740 * chamber_pos # starting point is center of head
        gantry_width = device.gantry_dims.width #1000
        gantry_depth = device.gantry_dims.depth #125
        gantry_height = device.gantry_dims.height #110
        max_z_travel = 300

        self.head = Sphere(pos, head_radius)
        l_body = Point3(pos.x - body_width / 2, pos.y - body_depth / 2, pos.z)
        u_body = Point3(pos.x + body_width / 2, pos.y + body_depth / 2, pos.z + body_height)
        self.body = Aab(l_body, u_body)
        l_gantry = Point3(pos.x - gantry_width / 2, pos.y - gantry_depth / 2, max_z_travel)
        u_gantry = Point3(pos.x + gantry_width / 2, pos.y + gantry_depth / 2, pos.z + max_z_travel - gantry_height)
        self.gantry = Aab(l_gantry, u_gantry)


def _is_collision_between_sphere(sphere1:Sphere, sphere2:Sphere):
    return math.dist(sphere1.center, sphere2.center) < (sphere1.radius + sphere2.radius)


def _is_collision_between_aab(box1:Aab, box2:Aab):
    return (box1.lower.x <= box2.upper.x) and (box1.upper.x >= box2.lower.x) \
    and (box1.lower.y <= box2.upper.y) and (box1.upper.y >= box2.lower.y) \
    and (box1.lower.z <= box2.upper.z) and (box1.upper.z >= box2.lower.z)


def _is_point_inside_aab(point:Point3, box:Aab):
    return (point.x >= box.lower.x) and (point.x <= box.upper.x) and (point.y >= box.lower.y) and (point.y <= box.upper.y) and (point.z >= box.lower.z) and (point.z <= box.upper.z)


def _is_point_inside_sphere(point:Point3, sphere:Sphere):
    return math.dist(point, sphere.center) < sphere.radius


def _is_collision_between_aab_sphere(box:Aab, sphere:Sphere):
    x = max(box.lower.x, min(sphere.center.x,box.upper.x))
    y = max(box.lower.y, min(sphere.center.y,box.upper.y))
    z = max(box.lower.z, min(sphere.center.z,box.upper.z))

    return _is_point_inside_sphere(Point3(x,y,z), sphere)


def _is_collision_between_cam_bounds(bounds_a:CamBounds, bounds_b:CamBounds):
    # Note: gantry only needs to be checked against other gantries since they can't collide with anything else.
    # Head_a to all_b
    if _is_collision_between_sphere(bounds_a.head, bounds_b.head):
        return True
    if _is_collision_between_aab_sphere(bounds_b.body, bounds_a.head):
        return True
    if _is_collision_between_aab_sphere(bounds_b.gantry, bounds_a.head):
        return True
    # Body_a to body_b and gantry_b.
    if _is_collision_between_aab(bounds_a.body, bounds_b.body):
        return True
    if _is_collision_between_aab(bounds_a.body, bounds_b.gantry):
        return True
    # Gantry_a to gantry_b.
    if _is_collision_between_aab(bounds_a.gantry, bounds_b.gantry):
        return True
    # Head_b to body_a.
    if _is_collision_between_aab_sphere(bounds_a.body, bounds_b.head):
        return True
    return False


def _bresenham_3d(pt1:Point3, pt2:Point3):
    _p1 = Point3(*pt1)
    results : List[Point3] = []

    results.append(_p1)

    dx = abs(pt2.x - _p1.x)
    dy = abs(pt2.y - _p1.y)
    dz = abs(pt2.z - _p1.z)

    if pt2.x > _p1.x:
        xs = 1
    else:
        xs = -1
    if pt2.y > _p1.y:
        ys = 1
    else:
        ys = -1
    if pt2.z > _p1.z:
        zs = 1
    else:
        zs = -1

    # Lead axis is X-axis".
    if (dx >= dy and dx >= dz):
        e1 = 2 * dy - dx
        e2 = 2 * dz - dx

        while _p1.x != pt2.x:
            _p1.x += xs

            if e1>= 0:
                _p1.y += ys
                e1 -= 2 * dx

            if e2>= 0:
                _p1.z += zs
                e2 -= 2 * dx

            e1 += 2 * dy
            e2 += 2 * dz

            results.append(_p1)
    # Lead axis is Y-axis".
    elif dy >= dx and dy >= dz:
        e1 = 2 * dx - dy
        e2 = 2 * dz - dy

        while _p1.y != pt2.y:
            _p1.y += ys

            if e1 >= 0:
                _p1.x += xs
                e1 -= 2 * dy

            if e2 >= 0:
                _p1.z += zs
                e2 -= 2 * dy

            e1 += 2 * dx
            e2 += 2 * dz

            results.append(_p1)
    # Lead axis is Z-axis".
    else:
        e1 = 2 * dy - dz
        e2 = 2 * dx - dz

        while _p1.z != pt2.z:
            _p1.z += zs

            if e1 >= 0:
                _p1.y += ys
                e1 -= 2 * dz

            if e2 >= 0:
                _p1.x += xs
                _e2 -= 2 * dz #TODO [INQUIRY]: _e2 does not seem to be defined anywhere yet it is incremented here. What gives?

            e1 += 2 * dy
            e2 += 2 * dx

            results.append(_p1)
    return results


def _point_at_dist(pt1: Point3, pt2: Point3, dist: float):
    d1 = math.dist(pt1, pt2)

    if d1 == 0:
        return pt1

    n = dist / d1
    x = pt1.x + (pt2.x - pt1.x) * n
    y = pt1.y + (pt2.y - pt1.y) * n
    z = pt1.z + (pt2.z - pt1.z) * n

    return Point3(x, y, z)


def _gen_points_along_line(pt1: Point3, pt2: Point3, dist: float) -> List[Point3]:
    results = []
    results.append(Point3(*pt1))

    if pt1 == pt2:
        return results

    total_d = math.dist(pt1, pt2)
    cur_d = dist

    while cur_d < total_d - dist:
        results.append(_point_at_dist(pt1, pt2, cur_d))
        cur_d = cur_d + dist

    results.append(Point3(*pt2))

    return results


def _cam_bounds_along_line(device :Device, start_pos:Point3, end_pos:Point3, increment_dist:float) -> List[CamBounds]:
    results = []
    cam_pts = _gen_points_along_line(start_pos, end_pos, increment_dist)

    for p in cam_pts:
        results.append(CamBounds(device, p))

    return results


def _is_collision_between_moving_cams(cam1:Device, cam1_start_pos:Point3, cam1_end_pos:Point3, cam2:Device, cam2_start_pos:Point3, cam2_end_pos:Point3) -> bool:
    cb_list1 = _cam_bounds_along_line(cam1, cam1_start_pos, cam1_end_pos, 5)
    cb_list2 = _cam_bounds_along_line(cam2, cam2_start_pos, cam2_end_pos, 5)

    for cb1 in cb_list1:
        for cb2 in cb_list2:
            if _is_collision_between_cam_bounds(cb1, cb2):
                return True
    return False


def _is_collision_between_proxy_cam_move(cam :Device, cam_start_pos: Point3, cam_end_pos: Point3, proxy_aab :Aab):
    cb_list1 = _cam_bounds_along_line(cam, cam_start_pos, cam_end_pos, 3)
    for cb1 in cb_list1:
        if _is_collision_between_aab_sphere(proxy_aab, cb1.head):
            return True
    return False
