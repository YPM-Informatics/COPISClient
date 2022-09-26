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

"""COPIS Application Data storage facility."""

import os
import io
import pickle
import json
import shutil
import errno

from configparser import ConfigParser
from pathlib import Path
from typing import Any, Optional
from appdirs import user_data_dir

#    """ COPIS File I/O & storage operations."""

def get_root() ->str:
     root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
     return root

def get_ini_path() -> str:
    root_dir = get_root()
    p = os.path.join(root_dir, 'copis.ini')
    if not os.path.exists(p):
        p = os.path.join(resolve_data_dir(), 'copis.ini')
        if not os.path.exists(p):
            s = (os.path.join(get_root(),'ex','ex.ini'))
            shutil.copyfile(s,p)
    if not os.path.exists(p):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), p)
    return p

def resolve_data_dir() ->str:
    data_dir = user_data_dir('copis','copis')
    legacy = os.path.split(user_data_dir('copis', roaming=True))[0]
    legacy2 = os.path.split(user_data_dir('copis'))[0]
    if os.path.exists(legacy) and not os.path.exists(data_dir):
        return legacy
    elif os.path.exists(legacy2) and not os.path.exists(data_dir):
        return legacy2
    else:
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return data_dir

    
def get_profile_path() -> str:
    parser = load_config()
    if (parser.has_option('Project', 'profile_path')):
        p = parser['Project']['profile_path']
        if not os.path.exists(p): #likely referencing a relative path from a different working directory
            p2 = os.path.join(get_root(), p)
            if os.path.exists(p2):
                p = p2
    else:
        p = os.path.join(resolve_data_dir(),'default_profile.json')
        if not os.path.exists(p):
            s = (os.path.join(get_root(),'profiles','default_profile.json'))
            shutil.copyfile(s,p)  
    if not os.path.exists(p): #likely referencing a relative path from a different working directory
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), p)
    return p


def get_proxy_path() -> str:
    parser = load_config()
    if (parser.has_option('Project', 'default_proxy_path')):
        p = parser['Project']['default_proxy_path']
        if not os.path.exists(p): #likely referencing a relative path from a different working directory
            p2 = os.path.join(get_root(), p)
            if os.path.exists(p2):
                p = p2
    else:
        p = os.path.join(resolve_data_dir(),'handsome_dan.obj')
        if not os.path.exists(p):
            s = (os.path.join(get_root(),'proxies','handsome_dan.obj'))
            shutil.copyfile(s,p)
    if not os.path.exists(p): #likely referencing a relative path from a different working directory
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), p)
    return p

def save_config_parser(parser: ConfigParser) -> None:
    """Saves a configuration object to file."""
    with open(get_ini_path(), 'w') as file:
        parser.write(file)

def load_config() -> Optional[ConfigParser]:
    """Loads a configuration object from file."""
    if os.path.exists(get_ini_path()):
        parser = ConfigParser()
        parser.read(get_ini_path())
        return parser
    return None

def save_config(config) -> None:
    """Saves a configuration object to file, via its settings object."""
    p = load_config()
    parser = ConfigParser()
    parser.read_dict(config.as_dict())
    p.update(parser)
    save_config_parser(p)

def find_path( filename: str='') -> str:
    """Finds the given file name's full path relative to the COPIS root folder."""
    root_dir = get_root()
    paths = list(Path(root_dir).rglob(filename))
    return str(paths[0]) if len(paths) > 0 else ''

def find_proxy(file_name: str='') -> str:
    """Finds the given proxy file name's full path relative to the COPIS root folder."""
    root_dir = get_root()
    return self.find_path(os.path.join(root_dir, file_name))


def save_json(filename: str, obj: dict) -> None:
    """Saves a JSON object to file."""
    with open(filename, 'w') as file:
        json.dump(obj, file, indent='\t')


def save_json_2(file_dir: str, file_name: str, obj: dict) -> None:
    """Saves a JSON object to file; with a path join."""
    filename = os.path.join(file_dir, file_name)
    save_json(filename, obj)


def load_json(filename: str) -> Any:
    """Loads a JSON object from file."""
    with open(filename, 'r') as file:
        obj = json.load(file)

    return obj


def load_json_2(file_dir: str, file_name: str) -> Any:
    """Loads a JSON object from file; with a path join."""
    filename = os.path.join(file_dir, file_name)

    return load_json(filename)

def save_data(filename: str, data: str) -> None:
    """Saves some string data to file."""
    with open(filename, 'w') as file:
        file.write(data)


def load_data(filename: str) -> str:
    """Loads some string data from file."""
    with open(filename, 'r') as file:
        data = file.read()

    return data


def get_directory(filename: str) -> str:
    """Extracts and returns a paths directory."""
    return os.path.dirname(filename)


def get_file_base_name_no_ext(filename: str) -> str:
    """Extracts and returns a file name without extension out of a path."""
    return os.path.splitext(get_file_base_name(filename))[0]


def get_file_base_name(filename: str) -> str:
    """Extracts and returns a file name with extension out of a path."""
    return os.path.basename(filename)


def path_exists(filename: str) -> bool:
    """Checks whether the given path exists."""
    return os.path.exists(filename)


def path_exists_2(file_dir: str, file_name: str) -> bool:
    """Checks whether the given path exists; with a path join."""
    filename = os.path.join(file_dir, file_name)

    return path_exists(filename)

def delete_path(filename: str) -> None:
    """Deletes the given path."""
    if path_exists(filename):
        os.remove(filename)

class _RemoduleUnpickler(pickle.Unpickler):
    """Extends the pickle unpickler so that we can provided the correct module
    when unpickling an object pickled with an outdated version of the module."""
    def find_class(self, module, name):
        renamed_module = module
        if module == "copis.enums":
            renamed_module = "copis.globals"

        return super(_RemoduleUnpickler, self).find_class(renamed_module, name)


def save_pickle(filename: str, obj: object) -> None:
    """Saves a pickled object to file."""
    with open(filename, 'wb') as file:
        pickle.dump(obj, file)

def load_pickle(filename: str, obj: object) -> object:
    """Loads a pickled object from file."""
    with open(filename, 'rb') as file:
        obj = _pickle_remodule_load(file) # pickle.load(file)

    return obj

def _pickle_remodule_load(file_obj):
    return _RemoduleUnpickler(file_obj).load()

def _pickle_remodule_loads(pickled_bytes):
    file_obj = io.BytesIO(pickled_bytes)
    return _pickle_remodule_loads(file_obj)
