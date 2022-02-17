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
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""Helper functions for path generation."""

import math

from collections import defaultdict
from typing import List, Tuple
from itertools import groupby

import numpy as np
import glm
from glm import vec2, vec3

from copis.classes import Action, Object3D, Pose
from copis.globals import ActionType
from copis.helpers import (create_action_args, get_heading, interleave_lists,
    sanitize_number, sanitize_point)
from .mathutils import orthonormal_basis_of


_XY_COST = 1.0
_Z_COST = 10.0
_Z_BUFFER = 50.0


def create_circle(p: vec3,
                  n: vec3,
                  r: float,
                  sides: int = 36) -> Tuple[np.ndarray, int]:
    """Create circle vertices given point, normal vector, radius, and # sides.

    Uses an approximation method to compute vertices versus many trig calls.
    """
    b1, _ = orthonormal_basis_of(n)
    theta = math.tau / sides
    tangential_factor = math.tan(theta)
    radial_factor = math.cos(theta)

    x, y, z = b1 * r
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


def create_helix(p: vec3,
                 n: vec3,
                 r: float,
                 pitch: int = 1,
                 turns: float = 1.0,
                 sides: int = 36) -> Tuple[np.ndarray, int]:
    """Create helix vertices given point, normal vector, radius, pitch, # turns,
    and # sides.

    Uses an approximation method rather than trig functions.
    """
    b2, _ = orthonormal_basis_of(n)
    theta = math.tau / sides
    tangential_factor = math.tan(theta)
    radial_factor = math.cos(theta)

    x, y, z = b2 * r
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


def create_line(start: vec3,
                end: vec3,
                points: int = 2) -> Tuple[np.ndarray, int]:
    """Create line given start position, end position, and # points."""
    if points < 2:
        raise IndexError('number of points in line must be greater than 2')

    vertices = np.empty(points * 3)
    vertices[::3] = np.linspace(start.x, end.x, points)
    vertices[1::3] = np.linspace(start.y, end.y, points)
    vertices[2::3] = np.linspace(start.z, end.z, points)

    return vertices, points


def process_path(grouped_points, colliders, max_zs, lookat) -> defaultdict(list):
    """Processes imaging path to add all necessary adjustments."""
    # cost_ordered_points, clearance_indexes = _order_points(grouped_points, colliders, max_zs)

    # if all(len(points) == 0 for points in cost_ordered_points.values()):
    #     print('Error: All poses are within the proxy object.')

    poses = _build_poses(grouped_points, [], lookat)
    poses = interleave_poses(poses)
    return build_pose_sets(poses)

def interleave_poses(poses: List[Pose]) -> List[Pose]:
    """Rearranges poses to alternate by camera."""
    get_device = lambda a: a.position.device

    interleaved = poses

    if poses and len(poses):
        sorted_poses = sorted(poses, key=get_device)
        grouped = groupby(sorted_poses, get_device)
        groups = []

        for _, group in grouped:
            groups.append(list(group))

        interleaved = interleave_lists(*groups)

    return interleaved

def build_pose_sets(poses: List[Pose]) -> List[List[Pose]]:
    """Arranges a pose list into a pose set list.
        Each set contains at most one pose per device."""
    if not poses:
        return poses

    sets = []
    set_ = []

    for pose in poses:
        if set_ and any(p.position.device ==
            pose.position.device for p in set_):
            sets.append(set_)
            set_ = []

        set_.append(pose)

    if set_:
        sets.append(set_)

    return sets

def _build_poses(ordered_points, clearance_indexes, lookat):
    poses = []

    # pos_records = {}

    for device_id in ordered_points:
        for i, point in enumerate(ordered_points[device_id]):
            pan, tilt = get_heading(point, lookat)

            # Add action. skip feed rate for now.
            s_point = sanitize_point(point)
            s_pan = sanitize_number(pan)
            s_tilt = sanitize_number(tilt)
            # record = Point5(s_point.x, s_point.y, s_point.z, s_pan, s_tilt)

            # if device_id in pos_records.keys():
            #     last_record = pos_records[device_id]
            #     last_pan = rad_to_dd(last_record.p)
            #     next_pan = rad_to_dd(s_pan)

            #     # 200 is arbitrary.
            #     # this is a naive placeholder logic that'll be fleshed out later.
            #     dist = 200 - glm.distance(vec2(0, 0), vec2(last_record.x, last_record.y))

            #     if abs(next_pan - last_pan) > 180 and dist > 0:
            #         # Back off
            #         # The right formula for this is new_x = x + (dist * cos(pan)) &
            #         # new_y = y + (dist * cos(pan)). but since our pan angle is measured
            #         # relative to the positive y axis, we have to flip sine and cosine.
            #         next_record = Point5(s_point.x, s_point.y, s_point.z, s_pan, s_tilt)

            #         x1 = sanitize_number(last_record.x + (dist * math.sin(last_record.p)))
            #         y1 = sanitize_number(last_record.y + (dist * math.cos(last_record.p)))
            #         z1 = last_record.z

            #         x2 = sanitize_number(next_record.x + (dist * math.sin(next_record.p)))
            #         y2 = sanitize_number(next_record.y + (dist * math.cos(next_record.p)))
            #         z2 = next_record.z

            #         pt1 = Point5(x1, y1, z1, last_record.p, last_record.t)
            #         pt2 = Point5(x2, y2, z2, next_record.p, next_record.t)

            #         args1 = create_action_args([pt1.x, pt1.y, pt1.z, pt1.p, pt1.t])
            #         args2 = create_action_args([pt2.x, pt2.y, pt2.z, pt2.p, pt2.t])

            #         interlaced_actions.append(
            #             Pose(Action(ActionType.G1, device_id, len(args1), args1), []))
            #         interlaced_actions.append(
            #             Pose(Action(ActionType.G1, device_id, len(args2), args2), []))

            #         print_debug_msg(
            #             self.core.console, f'**** DEVICE: {device_id} IS ABOUT TO TURN!!! ****', True)
            #         print_debug_msg(
            #             self.core.console, f'last: {last_pan}, next: {next_pan}, diff: {next_pan - last_pan}, center distance: {dist}', True)

            #     pos_records[device_id] = record
            # else:
            #     pos_records.update({device_id: record})

            g_args = create_action_args([s_point.x, s_point.y, s_point.z, s_pan, s_tilt])
            payload = []

            if not clearance_indexes or i not in clearance_indexes[device_id]:
                c_args = create_action_args([1.5], 'S')
                payload = [Action(ActionType.C0, device_id, len(c_args), c_args)]

            poses.append(
                # TODO: allow user customization of poses at each point
                # https://github.com/YPM-Informatics/COPISClient/issues/102
                Pose(Action(ActionType.G1, device_id, len(g_args), g_args), payload, lookat.to_tuple())
            )

    return poses


def _order_points(grouped_points, colliders, max_zs):
        # greedily expand path from starting point
    cost_ordered_points = defaultdict(list)
    clearance_indexes = defaultdict(list)

    for device_id, points in grouped_points.items():
        clearance_indexes[device_id] = []

        # loop until all points used
        while points:
            # get best next point using cost function
            if len(cost_ordered_points[device_id]) > 0:
                curr_point = cost_ordered_points[device_id][-1]
            else:
                # choose starting point, currently the first one in the list
                # TODO: make starting point less arbitrary
                # Maybe start at closest point to each cams home position?
                curr_point = points[0]

            best_cost = math.inf
            best_index = -1

            for index, point in enumerate(points):
                point_cost = _point_cost(curr_point, point, colliders)

                if point_cost < best_cost:
                    best_cost = point_cost
                    best_index = index

            # stop if cost is infinite (intersect with objects)
            if best_cost == math.inf:
                break

            cost_ordered_points[device_id].append(points.pop(best_index))

            start = cost_ordered_points[device_id][-2] \
                if len(cost_ordered_points[device_id]) > 1 else cost_ordered_points[device_id][-1]
            end = cost_ordered_points[device_id][-1]

            if _line_cost(start, end, colliders) == math.inf:
                colliders_z = [c.bbox.upper.z for c in colliders]
                clearance_z = min(max(colliders_z) + _Z_BUFFER, max_zs[device_id])
                clearance_start = vec3(start.x, start.y, clearance_z)
                clearance_end = vec3(end.x, end.y, clearance_z)
                clearance_index = len(cost_ordered_points[device_id]) - 1

                cost_ordered_points[device_id].insert(clearance_index, clearance_end)
                cost_ordered_points[device_id].insert(clearance_index, clearance_start)

                clearance_indexes[device_id].extend([clearance_index, clearance_index + 1])

    return (cost_ordered_points, clearance_indexes)

def _point_cost(start: vec3, end: vec3, colliders: List[Object3D]) -> float:
    """Calculate cost of moving from start to end, for a point. Returns math.inf
    if movement will intersect a proxy object.
    """

    # intersect bad!
    for obj in colliders:
        if obj.vec3_intersect(end, 10.0):
            return math.inf

    return (
        # cost of movement along XY
        _XY_COST * glm.distance(vec2(start), vec2(end)) +
        # cost of movement along Z
        _Z_COST * abs(end.z - start.z))


def _line_cost(start: vec3, end: vec3, colliders: List[Object3D]) -> float:
    """Calculate cost of moving from start to end, for a line. Returns math.inf
    if movement will intersect a proxy object.
    """

    # intersect bad!
    for obj in colliders:
        if obj.bbox.line_segment_intersect(start, end):
            return math.inf

    return (
        # cost of movement along XY
        _XY_COST * glm.distance(vec2(start), vec2(end)) +
        # cost of movement along Z
        _Z_COST * abs(end.z - start.z))
