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
from configparser import ConfigParser
from pathlib import Path
from typing import Optional


class Store():
    """Handle application-wide data storage operations."""

    _PROJECT_FOLDER = 'copis'
    _CONFIG_FILE = 'COPIS.ini'

    def __init__(self) -> None:
        current = os.path.dirname(__file__)
        segments = current.split(os.sep)
        index = segments.index(Store._PROJECT_FOLDER)
        root_segments = segments[1:index]

        root = '\\' + os.path.join(*root_segments)
        app_data = '\\' + os.path.join(*os.environ['APPDATA'].split(os.sep)[1:])

        self._root_dir = root
        self._config_dir = os.path.join(app_data, Store._PROJECT_FOLDER.upper())
        self._config_path = os.path.join(self._config_dir, Store._CONFIG_FILE)

        if not os.path.exists(self._config_dir):
            os.makedirs(self._config_dir)

    def ensure_default_profile(self, name: str, data: str):
        """Ensures the default profile file exists and returns it path."""
        filename = os.path.join(self._config_dir, name)

        if not os.path.exists(filename):
            obj = json.loads(data)
            save_json(filename, obj)

        return filename

    def ensure_default_proxy(self, name: str, data: str):
        """Ensures the default proxy file exists and returns it path."""
        filename = os.path.join(self._config_dir, name)

        if not os.path.exists(filename):
            save_data(filename, data)

        return filename

    def save_config_parser(self, parser: ConfigParser) -> None:
        """Saves a configuration object to file."""
        with open(self._config_path, 'w') as file:
            parser.write(file)

    def save_config(self, config) -> None:
        """Saves a configuration object to file, via its settings object."""
        parser = ConfigParser()
        parser.read_dict(config.as_dict())

        self.save_config_parser(parser)

    def load_config(self) -> Optional[ConfigParser]:
        """Loads a configuration object from file."""
        if os.path.exists(self._config_path):
            parser = ConfigParser()
            parser.read(self._config_path)
            return parser

        return None

    def find_path(self, filename: str='') -> str:
        """Finds the given file names full path relative to the COPIS root folder."""
        paths = list(Path(self._root_dir).rglob(filename))
        return str(paths[0]) if len(paths) > 0 else ''


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


def save_json(filename: str, obj: object) -> None:
    """Saves a JSON object to file."""
    with open(filename, 'w') as file:
        json.dump(obj, file, indent='\t')


def load_json(filename: str) -> dict:
    """Loads a JSON object from file."""
    with open(filename, 'r') as file:
        obj = json.load(file)

    return obj


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


def save_project(data: dict) -> str:
    """Saves a project."""
    filename = data['path']
    p_root = get_directory(filename)
    proj_rel_dir = get_file_base_name_no_ext(filename)

    if p_root.split(os.sep)[-1] != proj_rel_dir:
        p_root = os.path.join(p_root, proj_rel_dir)

    filename = os.path.join(p_root, get_file_base_name(filename))

    playlist = json.dumps(data['playlist'])

    return filename



def _pickle_remodule_load(file_obj):
    return _RemoduleUnpickler(file_obj).load()


def _pickle_remodule_loads(pickled_bytes):
    file_obj = io.BytesIO(pickled_bytes)
    return _pickle_remodule_loads(file_obj)
