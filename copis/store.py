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
from shutil import rmtree
from typing import Any, Optional


class Store():
    """Handle application-wide data storage operations."""

    _PROJECT_FOLDER = 'copis'
    _CONFIG_FILE = 'COPIS.ini'
    _PROXY_FOLDER = 'proxies'
    _VERSION_FILE = '__version__.py'

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

    def clear_configs(self):
        """Clears the configuration directory"""
        rmtree(self._config_dir)
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
        with open(self._config_path, 'w', encoding='utf-8') as file:
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
        """Finds the given file name's full path relative to the COPIS root folder."""
        paths = list(Path(self._root_dir).rglob(filename))
        return str(paths[0]) if len(paths) > 0 else ''

    def find_proxy(self, file_name: str='') -> str:
        """Finds the given proxy file name's full path relative to the COPIS root folder."""
        return self.find_path(os.path.join(Store._PROXY_FOLDER, file_name))

    def get_copis_version(self) -> str:
        """Gets the current version of the COPIS app."""
        pkg_attrs  = {}
        version_path = self.find_path(Store._VERSION_FILE)

        if path_exists(version_path):
            # pylint: disable=exec-used
            with open(version_path, encoding='utf-8') as file:
                exec(file.read(), pkg_attrs)

            return pkg_attrs['__version__']

        return ""


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
    with open(filename, 'wb', encoding='utf-8') as file:
        pickle.dump(obj, file)


def load_pickle(filename: str, obj: object) -> object:
    """Loads a pickled object from file."""
    with open(filename, 'rb', encoding='utf-8') as file:
        obj = _pickle_remodule_load(file) # pickle.load(file)

    return obj


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


def _pickle_remodule_load(file_obj):
    return _RemoduleUnpickler(file_obj).load()


def _pickle_remodule_loads(pickled_bytes):
    file_obj = io.BytesIO(pickled_bytes)
    return _pickle_remodule_loads(file_obj)
