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

"""Provides the COPIS path related data structures."""

import json
import copy

from enum import Enum
from itertools import groupby
from functools import partial

from models.actions import Action, ActionTypes, FocusAction, FocusStackAction, NoAction, PauseAction, ShutterReleaseAction
from models.geometries import BoundingBox, Point3, Point5
from models.machine import Device, DeviceGroup, DeviceSettings
from models.path import Move, MoveTypes, Pose

class JsonConvert:
    """Custom JSON converter."""

    @staticmethod
    def serialize_move_sets(move_set_list) -> str:
        """Returns a JSON formatted representation of a list of move sets.

        :param `move_set_list`: an iterable of iterables of :class:`models.path.Move` objects.

        """
        device_key = lambda d: d.d_id

        uniq_devices = []
        uniq_dvc_groups = []
        move_sets = copy.deepcopy(move_set_list)

        devices = [m.device for m_set in move_sets for m in m_set]

        for _, g in groupby(sorted(devices, key=device_key), device_key):
            uniq_devices.append(next(g))

        dvc_groups = [d.group for d in uniq_devices]

        for _, g in groupby(sorted(dvc_groups, key=id), id):
            uniq_dvc_groups.append(next(g))

        for d_group in uniq_dvc_groups:
            d_group.main_device = d_group.main_device.d_id if not isinstance(d_group.main_device, int) else d_group.main_device
            d_group.aux_devices = [d.d_id if not isinstance(d, int) else d for d in d_group.aux_devices]

        for m_set in move_sets:
            for m in m_set:
                m.device = m.device.d_id
                m.destination = m.end_pose

                del m.start_pose
                del m.end_pose


        for d in uniq_devices:
            d.group = uniq_dvc_groups.index(d.group)

        serialized = _to_json({
            'devices': uniq_devices,
            'device_groups' : uniq_dvc_groups,
            'move_sets': move_sets
        })

        return serialized


    @staticmethod
    def deserialize_move_sets(move_set_list_json) -> list:
        """Returns a list of move sets. JSON formatted representation of a .

        :param `move_set_list_json`: a JSON formatted string representation of a COPIS structured move set.

        """
        def get_dvc_by_id(col, dvc_id):
            return next(filter(lambda d: d.d_id == dvc_id, col))

        dict_data = json.loads(move_set_list_json)
        devices = list(map(_parse_device, dict_data['devices']))
        dvc_groups = list(map(_parse_device_group, dict_data['device_groups']))
        move_sets = list(map(_parse_move_set, dict_data['move_sets']))

        for dvc in devices:
            dvc.group = dvc_groups[dvc.group]

        for dvc_group in dvc_groups:
            dvc_group.main_device = get_dvc_by_id(devices, dvc_group.main_device)
            dvc_group.aux_devices = list(map(partial(get_dvc_by_id, devices) , dvc_group.aux_devices))

        for idx, move_set in enumerate(move_sets):
            for move in move_set:
                move.device = get_dvc_by_id(devices, move.device)

                if idx == 0:
                    move.start_pose = Pose(Point5(move.device.home_position))
                else:
                    prev_dvc_move = next(filter(lambda m, m1=move: m.device == m1.device, move_sets[idx - 1]), None)

                    while not prev_dvc_move and (idx - 1) >= 0:
                        prev_dvc_move = next(filter(lambda m, m1=move: m.device == m1.device, move_sets[idx - 1]), None)

                    move.start_pose = Pose(prev_dvc_move.end_pose.position if prev_dvc_move else move.device.home_position)

        return move_sets


def _get_clean_dict(obj):
    if isinstance(obj, Enum):
        return obj.name

    dic = dict(
        (k, v) for k, v in obj.__dict__.items() if v is not None
    )

    if isinstance(obj, Action):
        dic['type'] = obj.type.name
    return dic


def _to_json(obj):
    return json.dumps(obj, allow_nan=False, default=_get_clean_dict)


def _parse_device(data_dic):
    home_pos = Point5(**data_dic['home_position'])
    range_3d = BoundingBox(Point3(**data_dic['range_3d']['lower']), Point3(**data_dic['range_3d']['upper']))
    settings = DeviceSettings(**data_dic['settings'])

    data_dic.pop('home_position')
    data_dic.pop('range_3d')
    data_dic.pop('settings')

    device = Device(**data_dic)
    device.home_position = home_pos
    device.range_3d = range_3d
    device.settings = settings

    return device


def _parse_device_group(data_dic):
    return DeviceGroup(**data_dic)


def _parse_enum(enum_name):
    move_type_names = [m.name for m in MoveTypes]
    action_type_names = [a.name for a in ActionTypes]

    if enum_name in move_type_names:
        return MoveTypes[enum_name]
    if enum_name in action_type_names:
        return ActionTypes[enum_name]
    raise NotImplementedError(f'Enum named {enum_name} Could not be found.')


def _parse_action(data_dic):
    action_type = _parse_enum(data_dic['type'])

    data_dic.pop('type')

    if action_type == ActionTypes.FOCUS:
        return FocusAction(**data_dic)
    if action_type == ActionTypes.FOCUS_STACK:
        return FocusStackAction(**data_dic)
    if action_type == ActionTypes.NO_OP:
        return NoAction(**data_dic)
    if action_type == ActionTypes.PAUSE:
        return PauseAction(**data_dic)
    if action_type == ActionTypes.SHUTTER_RELEASE:
        return ShutterReleaseAction(**data_dic)
    raise NotImplementedError(f'Action type {action_type} not yet implemented.')


def _parse_move_set(data_dic_list):
    move_set = []

    for data_dict in data_dic_list:
        move_type = _parse_enum(data_dict['type'])
        waypoints = list((map(lambda p: Point5(**p), data_dict['waypoints']))) if 'waypoints' in data_dict.keys() else None
        destination = Pose(Point5(**data_dict['destination']['position']),
            list((map(_parse_action, data_dict['destination']['actions']))) if 'actions' in data_dict['destination'].keys() else None)

        data_dict.pop('type')

        if 'waypoints' in data_dict.keys():
            data_dict.pop('waypoints')
        data_dict.pop('destination')

        move = Move(**data_dict)
        move.type = move_type
        move.waypoints = waypoints
        move.end_pose = destination

        move_set.append(move)
    return move_set
