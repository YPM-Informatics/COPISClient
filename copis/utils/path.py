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

from collections import defaultdict
from typing import List

from copis.helpers import get_heading, interleave_lists, sanitize_number, sanitize_point
from copis.models.actions import ShutterReleaseAction
from copis.models.geometries import Point3, Point5
from copis.models.path import Move, MoveTypes, Pose


def build_path(device_info: dict, vertices: dict, target: Point3) -> List[List[Move]]:
    """Returns a COPIS imaging path as a list of lists of moves.
        Args:
            device_info: a collection of (Device, Point5) tuples - Where Point5 is the the device's last position - grouped by device id.
            vertices: a collection of Point3 vertices grouped by device id.
            target: a 3D point representing the target of imaging.
    """
    keyed_moves = defaultdict(list)

    for dvc_id, info in device_info.items():
        last_position = info[1]

        for vtx in vertices[dvc_id]:
            pan, tilt = get_heading(vtx, target)

            position = Point5(*sanitize_point(vtx), sanitize_number(pan), sanitize_number(tilt))
            start_pose = Pose(last_position)
            end_pose = Pose(position, [ShutterReleaseAction(1500)])

            keyed_moves[dvc_id].append(Move(MoveTypes.LINEAR, start_pose, end_pose, device=info[0]))

            last_position = position

    interleaved = interleave_lists(*list(keyed_moves.values()), keep_def_fill_val=True)
    set_size = len(device_info)
    lists = [interleaved[i:i+set_size] for i in range(0, len(interleaved), set_size)]
    return [[m for m in l if m is not None] for l in lists]
