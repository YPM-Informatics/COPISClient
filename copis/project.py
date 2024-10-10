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

"""COPIS Application project manager."""

import os
import json
from importlib import import_module
from typing import Any, Dict, Iterable, List, Tuple
from pydispatch import dispatcher
from itertools import groupby
from glm import vec3

from copis.classes import (BoundingBox, Device, Action, Pose, MonitoredList, Object3D, OBJObject3D)

from copis.globals import Point5
from copis.command_processor import deserialize_command
from copis.helpers import collapse_whitespaces, interleave_lists
from copis.pathutils import build_pose_sets
import copis.store as store

import wx
from copis.gui.wxutils import show_prompt_dialog, show_msg_dialog

class Project():
    """A singleton that manages COPIS project operations."""
    # Note: This is the Borg design pattern which ensures that all
    # instances of this class are actually using the same set of
    # instance data.  See
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66531
    __shared_state = None

    def __init__(self):
        if not Project.__shared_state:
            Project.__shared_state = self.__dict__
        else:
            self.__dict__ = Project.__shared_state
        if not hasattr(self, '_is_initialized'):
            self._is_initialized = False
        #if not hasattr(self, '_profile_path'):
        #    self._profile_path = None
        #if not hasattr(self, '_default_proxy_path'):
        #    self._default_proxy_path = None
        if not hasattr(self, '_path'):
            self._path = None
        if not hasattr(self, '_profile'):
            self._profile = None
        if not hasattr(self, '_is_dirty'):
            self._is_dirty = False
        if not hasattr(self, '_devices'):
            self._devices = None
        if not hasattr(self, '_proxies'):
            self._proxies = None
        if not hasattr(self, '_adhocs'):     #NR
            self._adhocs = None              
        if not hasattr(self, '_pose_sets'):
            self._pose_sets = None
        if not hasattr(self, '_core'):
            self._core = None
        if not hasattr(self, '_options'):
            self._options = {}
        # Bind listeners.
        dispatcher.connect(self._set_is_dirty, signal='ntf_a_list_changed')
        dispatcher.connect(self._set_is_dirty, signal='ntf_d_list_changed')
        dispatcher.connect(self._set_is_dirty, signal='ntf_o_list_changed')
        dispatcher.connect(self._set_is_dirty, signal='ntf_adhocs_list_changed') #NR
    
    @property
    def profile_path(self) -> str:
        """Returns the project's profile path."""
        return self._profile_path
    
    @property
    def path(self) -> str:
        """Returns the project's save path."""
        return self._path

    @property
    def devices(self) -> List[Device]:
        """Returns the list of configured devices."""
        return self._devices

    @property
    def proxies(self) -> List[Object3D]:
        """Returns the list of proxy objects."""
        return self._proxies
    
    @property  #NR
    def adhocs(self) -> List[Object3D]:              #NR
        """Returns (dict of lists [todo]) list of adhoc objects that can be displayed as needed."""     #NR
        return self._adhocs                          #NR

    @property
    def pose_sets(self) -> List[List[Pose]]:
        """Returns the pose set list."""
        return self._pose_sets

    @property
    def poses(self) ->List[Pose]:
        """Returns all poses in the pose set list."""
        p_sets = self._pose_sets
        if not p_sets:
            return []

        return[pose for p_set in p_sets for pose in p_set]

    @property
    def options(self) -> dict:
        """Returns the project's imaging options."""
        return self._options

    @property
    def is_dirty(self) -> bool:
        """Returns whether the project is dirty."""
        return self._is_dirty

    @property
    def homing_sequence(self) -> List[str]:
        """Parses and returns the profile homing sequence."""
        def is_step_valid(step: str):
            # remove comments (js, python and ini style) and empty lines.
            if step.startswith(('//', '#', ';')):
                return False
            if step is None or (step is not None and len(step.strip()) <= 0):
                return False
            return True
        key = 'homing_sequence'
        seq = []
        if key in self._profile and self._profile[key]:
            seq = list(filter(is_step_valid, self._profile[key].split('\n')))
        return seq

    @property
    def homing_actions(self) -> List[Action]:
        """Turns the homing sequence into a list of actions."""
        if not self.homing_sequence or len(self.homing_sequence) == 0:
            return []
        return [deserialize_command(cmd) for cmd in self.homing_sequence]

    def _init(self):
        #self._profile_path =  store.get_profile_path()
        #self._default_proxy_path = store.get_proxy_path()
        self._is_initialized = True
        self._is_dirty = False

    def _set_is_dirty(self):
        self._toggle_is_dirty(True)

    def _unset_dirty_flag(self):
        self._toggle_is_dirty(False)

    def _toggle_is_dirty(self, value):
        self._is_dirty = value
        dispatcher.send('ntf_project_dirty_changed', is_project_dirty=self._is_dirty)

    def _init_devices(self):
        def parse_device(data):
            lower_corner = vec3(data['range_x'][0], data['range_y'][0], data['range_z'][0])
            upper_corner = vec3(data['range_x'][1], data['range_y'][1], data['range_z'][1])
             #if gantry style not present (as in older profiles files) we default to standard overhead gantry since all files before were overhead only
            if 'size' not in data:
                data['size'] = [350,250,200]
            if 'head_radius' not in data:
                data['head_radius'] = 200
            if 'body_dims' not in data:
                data['body_dims'] = [100, 40, 740]
            if 'gantry_dims' not in data:
                data['gantry_dims'] = [ 1000, 125, 100 ]
            if 'gantry_orientation' not in data:
                data['gantry_orientation'] = 1
            if 'serial_no' not in data:
                data['serial_no'] = ''
            if 'serial_no' not in data:
                data['serial_no'] = ''
            if 'edsdk_save_to_path' not in data: #eventually add global default in ini for all cams
                data['edsdk_save_to_path'] = os.path.join(store.get_root(), 'output') #for now default to program dir.
            if data['edsdk_save_to_path'] and not (data['edsdk_save_to_path']).isspace() and not os.path.exists(data['edsdk_save_to_path']):
                os.makedirs(data['edsdk_save_to_path'])
            return Device(
                data['id'],
                data['serial_no'],
                data['name'],
                data['type'],
                data['description'],
                Point5(*data['home_position']),
                BoundingBox(lower_corner, upper_corner),
                vec3(data['size']),
                data['port'],
                data['head_radius'],
                vec3(data['body_dims']),
                vec3(data['gantry_dims']),
                data['gantry_orientation'],
                data['edsdk_save_to_path']
            )
        key = 'devices'
        devices = []
        if key in self._profile and self._profile[key]:
            devices = [parse_device(d) for d in self._profile[key]]
        if self._devices is not None:               
            self._devices.clear(False)
            self._devices.extend(devices)
        else:
            self._devices: List[Device] = MonitoredList('ntf_d_list_changed', devices)

    def _init_proxies(self, proxies=None, default_proxy_path=None):
        
        if proxies is None and  default_proxy_path and os.path.exists(default_proxy_path):
            # Start with handsome dan :)
            # On init a new project is created with handsome dan as the proxy.
            handsome_dan = OBJObject3D(default_proxy_path, scale=vec3(20, 20, 20))
            proxies = [handsome_dan]
        if self._proxies is not None and proxies is not None:
            self._proxies.clear(False)
            self._proxies.extend(proxies)
        else:
            self._proxies: List[Object3D] = MonitoredList('ntf_o_list_changed', proxies)
            self._adhocs: List[Object3D] = MonitoredList('ntf_adhocs_list_changed')         #NR

    def _init_pose_sets(self, sets=None):
        if self._pose_sets is not None:
            self._pose_sets.clear(sets is None)
            if sets is not None:
                self._pose_sets.extend(sets)
        else:
            if sets:
                self._pose_sets = MonitoredList('ntf_a_list_changed', sets)
            else:
                self._pose_sets = MonitoredList('ntf_a_list_changed')
    
    def _append_pose_sets(self, sets=None):
        if self._pose_sets is not None:
            if sets is not None:
                self._pose_sets.extend(sets)
        else:
            if sets:
                self._pose_sets = MonitoredList('ntf_a_list_changed', sets)
            else:
                self._pose_sets = MonitoredList('ntf_a_list_changed')
                
    def update_imaging_option(self, name: str, value: Any) -> None:
        """Updates the value of the give option in the imaging options dictionary."""
        if name not in self._options or self._options[name] != value:
            self._options[name] = value
            self._set_is_dirty()

    def set_default_imaging_option(self, name: str, value: Any) -> None:
        """Sets the default value of the give option in the imaging options dictionary.
           Behaves like update_imaging_option except that it does not set the project as dirty."""
        if name not in self._options or self._options[name] != value:
            self._options[name] = value

    def pose_by_dev_id(self, pose_set_idx, device_id) ->Pose:
        """Returns a pose in a given pose set with device id.
           if no pose is present for that device in the pose set, None is returned."""
        if pose_set_idx < len(self._pose_sets):
            for pose in self._pose_sets[pose_set_idx]:
                if device_id == pose.position.device:
                    return pose
        return None

    def last_pose_by_dev_id(self, pose_set_idx, device_id):
        """Returns the last (highest index) pose and index accross all pose sets up to pose_set_idx for device id.
           if no pose is present for that device up to the pose set idx, None is returned.
        """
        if pose_set_idx < len(self._pose_sets):
            for i in range(pose_set_idx,-1,-1):
                for pose in self._pose_sets[i]:
                    if device_id == pose.position.device:
                        return pose
        return None

    def first_pose_by_dev_id(self, pose_set_idx, device_id) -> Pose:
        """Returns the first (lowest index) pose accross all pose sets up for device id, starting with pose_idx
           if no pose is present for that device, none is returned.
        """
        if pose_set_idx < len(self._pose_sets):
            for i in range(pose_set_idx, len(self._pose_sets)):
                for pose in self._pose_sets[i]:
                    if device_id == pose.position.device:
                        return pose
        return None

    def start(self, profile_path:str, default_proxy_path: str) -> None:
        """Starts a new project."""
        if not self._is_initialized:
            self._init()
        with open(profile_path, 'r', encoding='utf-8') as file:
            self._profile = json.load(file)
        #self._default_proxy_path = default_proxy_path
        #self._profile = store.load_json(store.get_profile_path())
        self._init_devices()
        self._init_proxies(default_proxy_path=default_proxy_path)
        self._init_pose_sets()
        self._path = None
        self._unset_dirty_flag()

    def open(self, path: str) -> Tuple:
        """Opens an existing project given it's path."""
        if not self._is_initialized:
            self._init()
        with open(path, 'r', encoding='utf-8') as file:
            proj_data = json.load(file)
        p_sets = list(map(_pose_from_json_map, proj_data['imaging_path']))
        proxies = []
        resp = None
        is_dirty = False
        for proxy in proj_data['proxies']:
            if proxy['is_path']:
                proxy_path = proxy['data']
                if not store.path_exists(proxy_path):
                    proxy_file_name = store.get_file_base_name(proxy_path)
                    def_proxy_file_name = store.get_file_base_name(self._default_proxy_path)
                    if proxy_file_name.lower() == def_proxy_file_name.lower():
                        proxy_path = self._default_proxy_path
                    else:
                        proxy_path = store.find_proxy(proxy_file_name)
                    is_dirty = True
                if proxy_path:
                    proxies.append(OBJObject3D(
                        proxy_path, scale=vec3(20, 20, 20)))
                else:
                    resp = f'Proxy path "{proxy_path or proxy["data"]}" does not exist'
            else:
                glob_key = proxy['data']['cls']
                if glob_key not in globals().keys():
                    mod = import_module(proxy['data']['module'])
                    globals()[glob_key] = getattr(mod, glob_key)
                # pylint: disable=eval-used
                proxies.append(eval(proxy['data']['repr']))
        #eventually move the UI check elsewhere
        #this is a critical check, otherwise it makes sharing paths among labs difficult.
        if self._profile != proj_data['profile']:
            choice = show_prompt_dialog('This project was made using a different machine profile, override existing?',"Profile Mismatch")
            if choice == wx.ID_YES:
                self._profile = proj_data['profile']
                self._init_devices()
        self._init_proxies(proxies=proxies)
        self._init_pose_sets(p_sets)
        #self._append_pose_sets(p_sets)
        if 'imaging_options' in proj_data:
            self._options = proj_data['imaging_options']
        self._path = path
        if is_dirty:
            self._set_is_dirty()
        else:
            self._unset_dirty_flag()
        return resp
    
    def append_poses_from_project_file(self, path: str) -> Tuple:
        """Appends poses from an existing project given it's path."""
        if not self._is_initialized:
            self._init()
        #proj_data = store.load_json(path)
        with open(path, 'r', encoding='utf-8') as file:
            proj_data = json.load(file)
        resp = None
        is_dirty = False
        if self._profile != proj_data['profile']:
            show_msg_dialog('This project was made using a different machine profile, unable to import poses.')
            return resp
        p_sets = list(map(_pose_from_json_map, proj_data['imaging_path']))
        self._append_pose_sets(p_sets)
        if is_dirty:
            self._set_is_dirty()
        else:
            self._unset_dirty_flag()
        return resp

    def save(self, path: str) -> None:
        """Saves the project to disk at the given path."""
        get_module = lambda i: '.'.join(i.split(".")[:2])
        
        proj_data = { 'imaging_path': self._pose_sets, 'imaging_options': self._options, 'profile': self._profile, 'proxies': []}
        for proxy in self._proxies:
            if hasattr(proxy, 'obj'):
                proxy_data = proxy.obj.file_name
                proxy_name = store.get_file_base_name_no_ext(proxy_data)
                is_path = True
            else:
                cls_name = type(proxy).__qualname__
                proxy_data = { 'module': get_module(type(proxy).__module__), 'cls': cls_name, 'repr': collapse_whitespaces(repr(proxy)) }
                proxy_name = cls_name.lower().split("object")[0]
                is_path = False
                count = 1
                while any(p['name'] == proxy_name for p in proj_data['proxies']):
                    proxy_name = f'{proxy_name.split("_")[0]}_{count}'
                    count = count + 1
            p_data = {'name': proxy_name, 'data': proxy_data, 'is_path': is_path }
            proj_data['proxies'].append(p_data)
        store.save_json(path, proj_data)
        self._path = path
        self._unset_dirty_flag()

    def add_pose(self, set_index: int, pose: Pose) -> int:
        """Adds a pose to a pose set in the pose set list.
            Returns the index of the added pose."""
        if self.can_add_pose(set_index, pose.position.device):
            pose_set = self._pose_sets[set_index].copy()
            pose_set.append(pose)
            pose_set.sort(key=lambda p: p.position.device)

            self._pose_sets[set_index] = pose_set

            return pose_set.index(pose)
        else:
            return -1

    def insert_pose(self, set_index: int, pose: Pose) -> int:
        """Inserts a pose to a pose set in the pose set list;
            even if a pose for the camera already exists in the set.
            In which case poses are shifted down to the end of the list
            or until a set without a pose for the camera is encountered.
            Returns the index of the inserted pose."""
        if not self.can_add_pose(set_index, pose.position.device):
            free_set_indices = [i for i, set_ in enumerate(self._pose_sets) if i > set_index \
                and not any(p.position.device == pose.position.device for p in set_)]

            if free_set_indices:
                free_set_index = free_set_indices[0]
            else:
                free_set_index = len(self._pose_sets)
                self.add_pose_set()

            for i in range(free_set_index - 1, set_index - 1, -1):
                shifted = next(filter(lambda p: p.position.device == pose.position.device,
                    self._pose_sets[i]))

                self._pose_sets[i].remove(shifted)
                self._pose_sets[i + 1].append(shifted)
                self._pose_sets[i + 1].sort(key=lambda p: p.position.device)

        pose_set = self._pose_sets[set_index].copy()
        pose_set.append(pose)
        pose_set.sort(key=lambda p: p.position.device)

        self._pose_sets[set_index] = pose_set

        return pose_set.index(pose)

    def add_pose_set(self) -> int:
        """Adds an empty pose set at the end of the pose set list.
            Returns the index of the added pose set."""
        set_index = len(self._pose_sets)
        self._pose_sets.append([])

        return set_index

    def insert_pose_set(self, index) -> int:
        """Inserts an empty pose set at the give index.
            Returns the index of the inserted pose set."""
        self._pose_sets.insert(index, [])

        return index

    def delete_pose(self, set_index: int, pose_index: int):
        """Removes a pose given pose set and pose indexes."""
        pose_set = self._pose_sets[set_index].copy()
        pose_set.pop(pose_index)

        self._pose_sets[set_index] = pose_set

    def delete_pose_set(self, set_index: int):
        """Removes a pose set given its index."""
        self._pose_sets.pop(set_index)

    def move_set(self, index: int, step: int) -> int:
        """Moves a pose set up or down by step amount.
            Returns the pose set's new index."""
        new_index = index + step

        if 0 <= new_index < len(self._pose_sets):
            sets = self._pose_sets.copy()
            pose_set = sets.pop(index)
            sets.insert(new_index, pose_set)

            self._pose_sets.clear(False)
            self._pose_sets.extend(sets)

            return new_index

        return index

    def reverse_pose_sets(self):
        """Reverses the order of the pose sets."""
        self._pose_sets.reverse()

    def reverse_poses(self, device_ids: List=None):
        """Reverses the order of the poses for the given devices.
            Applies to all devices if none provided."""
        get_device = lambda a: a.position.device

        if self.poses and len(self.poses):
            sorted_poses = sorted(self.poses, key=get_device)
            grouped = groupby(sorted_poses, get_device)
            groups = []
            sets_changed = False

            for key, group in grouped:
                group = list(group)

                if not device_ids or key in device_ids:
                    group.reverse()
                    sets_changed = True

                groups.append(group)

            if sets_changed:
                interleaved = interleave_lists(*groups)
                self._pose_sets.clear(False)
                self._pose_sets.extend(build_pose_sets(interleaved))

    def can_add_pose(self, set_index: int, device_id: int):
        """Returns a flag indicating where a pose with the specified device
            can be added to the pose."""
        if not self._pose_sets or set_index >= len(self._pose_sets):
            return False

        if not self._devices or not any(d.device_id == device_id for d in self._devices):
            return False

        pose_set = self._pose_sets[set_index]

        if len(pose_set) >= len(self._devices):
            return False

        if any(p.position.device == device_id for p in pose_set):
            return False

        return True

    def get_allowed_devices(self, set_index: int):
        """Returns the devices not already in the set."""
        if not self._pose_sets or set_index >= len(self._pose_sets):
            return []

        set_dvc_ids = [p.position.device for p in self._pose_sets[set_index]]

        return [d for d in self._devices if d.device_id not in set_dvc_ids]


def _pose_from_json_map(set_data: Iterable[Any]) -> Pose:
    """Parses an iterable of JSON result dictionaries into a Pose and returns it."""
    tupleify = lambda l: list(map(tuple, l))

    p_set = []

    for pose_data in set_data:
        position = Action(**pose_data[0])
        position.args = tupleify(position.args)

        payload = [Action(**a) for a in pose_data[1]]
        for action in payload:
            action.args = tupleify(action.args)

        p_set.append(Pose(position, payload))

    return p_set
