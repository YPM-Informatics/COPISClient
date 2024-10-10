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

"""COPIS Application File I/O & storage operations."""

from ast import Store
import os
import io

import json
import shutil
import errno

from configparser import ConfigParser
from pathlib import Path
from typing import Any, Optional
#from appdirs import user_data_dir
from platformdirs import site_data_path, user_data_dir, site_data_dir

def get_root() -> str:
     """Returns root directory."""
     root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
     return root

# def get_ini_path() -> str:
#     """Returns the COPIS configuration file path."""
#     root_dir = get_root()
#     ini_path = os.path.join(root_dir, 'copis.ini')

#     if not os.path.exists(ini_path):
#         ini_path = os.path.join(resolve_app_data_dir(), 'copis.ini')
#         if not os.path.exists(ini_path):
#             legacy_ini_path = os.path.join(resolve_user_data_dir(), 'copis.ini')
#             if os.path.exists(legacy_ini_path):
#                 shutil.move(legacy_ini_path, ini_path) #move ini file from user folder to app data folder
#             else:    
#                 sample_ini_path = (os.path.join(get_root(),'ex','ex.ini'))
#                 shutil.copyfile(sample_ini_path, ini_path)
#     if not os.path.exists(ini_path):
#         raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), ini_path)

#     return ini_path

# def resolve_user_data_dir() -> str:
#     """Resolves and returns the user data path."""
    
#     data_dir = user_data_dir('copis','copis')
#     legacy = os.path.split(user_data_dir('copis', roaming=True))[0]
#     legacy2 = os.path.split(user_data_dir('copis'))[0]

#     if os.path.exists(legacy) and not os.path.exists(data_dir):
#         return legacy

#     if os.path.exists(legacy2) and not os.path.exists(data_dir):
#         return legacy2

#     if not os.path.exists(data_dir):
#         os.makedirs(data_dir)

#     return data_dir

# def resolve_app_data_dir() -> str:
#     """Resolves and returns the user data path."""
    
#     data_dir = site_data_path('copis','copis')
#     if not os.path.exists(data_dir):
#         os.makedirs(data_dir)
#     return data_dir


# def get_file_path(cfg_section :str, cfg_option :str, default_fname = None, src_copis_subfolder = '', allow_create_from_src=False) -> str:
#     """Returns a file path if its configured, or a default one if it's provided.""" 
#     #parser = load_config()
#     parser = ConfigParser()
#     parser.read(get_ini_path())
#     file_path = ""

#     if parser.has_option(cfg_section, cfg_option):
#         file_path = parser[cfg_section][cfg_option]

#         if not os.path.exists(file_path): # Likely referencing a relative path from a different working directory.
#             file_path1 = os.path.join(get_root(), file_path)

#             if os.path.exists(file_path1):
#                 file_path = file_path1
#     elif default_fname is not None: # Path is not referenced in config so we look for default file in data directory. If it doesn't exist we copy defaults from source directory.
#         file_path = os.path.join(resolve_user_data_dir(), default_fname)

#         if not os.path.exists(file_path) and allow_create_from_src:
#             sample_path = (os.path.join(get_root(),src_copis_subfolder, default_fname))
#             shutil.copyfile(sample_path,file_path)

#     return file_path

def if_not_exists_create(path:str) -> None:
    """Ensures a path exists."""
    if not os.path.exists(path):
        os.makedirs(path)

def find_path(filename: str='') -> str:
    """Finds the given file name's full path relative to the COPIS root folder."""
    root_dir = get_root()
    paths = list(Path(root_dir).rglob(filename))
    return str(paths[0]) if len(paths) > 0 else ''

def find_proxy(file_name: str='') -> str:
    """Finds the given proxy file name's full path relative to the COPIS root folder."""
    root_dir = get_root()
    return find_path(os.path.join(root_dir, file_name))


def save_json(filename: str, obj: dict) -> None:
    """Saves a JSON object to file."""
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(obj, file, indent='\t')


def save_json_2(file_dir: str, file_name: str, obj: dict) -> None:
    """Saves a JSON object to file; with a path join."""
    filename = os.path.join(file_dir, file_name)
    save_json(filename, obj)


def load_json(filename: str) -> Any:
    """Loads a JSON object from file."""
    with open(filename, 'r', encoding='utf-8') as file:
        obj = json.load(file)

    return obj


def load_json_2(file_dir: str, file_name: str) -> Any:
    """Loads a JSON object from file; with a path join."""
    filename = os.path.join(file_dir, file_name)

    return load_json(filename)

def save_data(filename: str, data: str) -> None:
    """Saves some string data to file."""
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(data)


def load_data(filename: str) -> str:
    """Loads some string data from file."""
    with open(filename, 'r', encoding='utf-8') as file:
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


