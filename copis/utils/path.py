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

"""Imaging path management functions."""

import operator as op

from collections import defaultdict
from itertools import groupby
from typing import List

from copis.helpers import get_heading, interleave_lists, sanitize_number, sanitize_point
from copis.models.actions import ShutterReleaseAction
from copis.models.geometries import Point3, Point5
from copis.models.path import Move, MoveTypes, Pose


def build_path(devices: dict, vertices: dict, target: Point3) -> List[List[Move]]:
    """Returns a COPIS imaging path as a list of lists of moves.
        Args:
            devices: a collection of devices keyed by their id.
            vertices: a collection of Point3 vertices grouped by device id.
            target: a 3D point representing the target of imaging.
    """
    keyed_moves = defaultdict(list)

    # Extend all arrays with their last items, up to the longest array's length.
    # We do this to ensure each move set has a move from each device, even if a device
    # does not move in a particular set.
    max_len = max(map(len, vertices.values()))

    for col in vertices.values():
        if len(col) < max_len:
            col.extend([col[-1]] * (max_len - len(col)))

    for dvc_id in devices:
        last_pose = None

        for vtx in vertices[dvc_id]:
            pan, tilt = get_heading(vtx, target)
            start_pose = last_pose
            end_pose = Pose(Point5(*sanitize_point(vtx), sanitize_number(pan), sanitize_number(tilt)), [ShutterReleaseAction(1500)])

            keyed_moves[dvc_id].append(Move(MoveTypes.LINEAR, start_pose, end_pose, device=devices[dvc_id]))

            last_pose = end_pose

    interleaved = interleave_lists(*list(keyed_moves.values()), keep_def_fill_val=True)
    lists = [interleaved[i:i+len(devices)] for i in range(0, len(interleaved), len(devices))]

    return [[m for m in l if m is not None] for l in lists]


def interleave_moves(moves: List[Move]) -> List[List[Move]]:
    """Returns an interleaved COPIS imaging path as a list of lists of moves.
        Args:
            moves: a collection of moves.
    """
    keyed_moves = groupby(sorted(moves, key=op.attrgetter('device.d_id')), op.attrgetter('device.d_id'))
    groups = [list(g) for _, g in keyed_moves]
    interleaved = interleave_lists(*groups, keep_def_fill_val=True)
    set_size = len(groups)
    lists = [interleaved[i:i+set_size] for i in range(0, len(interleaved), set_size)]

    return [[m for m in l if m is not None] for l in lists]
