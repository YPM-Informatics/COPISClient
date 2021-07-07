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
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

"""COPIS Application Data storage facility."""

__version__ = ""

import os
import io
import pickle
from configparser import ConfigParser
from pathlib import PurePath
from typing import Optional

from .classes import ConfigSettings, MachineSettings


class Store():
    """Handle application-wide data storage operations."""

    _PROJECT_FOLDER = 'copis'

    _CONFIG_FOLDER = 'config'
    _CONFIG_FILE = 'app.ini'

    def __init__(self) -> None:
        current = os.path.dirname(__file__)
        segments = current.split(os.sep)
        index = segments.index(Store._PROJECT_FOLDER)
        root_segments = segments[1:index]

        root = '/' + PurePath(os.path.join(*root_segments)).as_posix()

        self._root_dir = root
        self._config_dir = os.path.join(root, Store._PROJECT_FOLDER, Store._CONFIG_FOLDER)
        self._config_path = os.path.join(self._config_dir, Store._CONFIG_FILE)

        if not os.path.exists(self._config_dir):
            os.makedirs(self._config_dir)

    def save_config(self, parser: ConfigParser) -> None:
        """Save a configuration object to file."""
        with open(self._config_path, 'w') as file:
            parser.write(file)

    def save_config_settings(self, settings: ConfigSettings) -> None:
        """Save a configuration object to file, via its settings object."""
        parser = ConfigParser()
        parser.read_dict(settings.as_dict())

        self.save_config(parser)

    def load_config(self) -> Optional[ConfigParser]:
        """Load a configuration object from file."""
        if os.path.exists(self._config_path):
            parser = ConfigParser()
            parser.read(self._config_path)
            return parser

        return None


class _RemoduleUnpickler(pickle.Unpickler):
    """Extends the pickle unpickler so that we can provided the correct module
    when unpickling an object pickled with an outdated version of the module."""
    def find_class(self, module, name):
        renamed_module = module
        if module == "copis.enums":
            renamed_module = "copis.globals"

        return super(_RemoduleUnpickler, self).find_class(renamed_module, name)


def save_machine(filename: str, settings: MachineSettings) -> None:
    """Save a machine configuration settings object to file."""
    parser = ConfigParser()
    parser.read_dict(settings.as_dict())

    with open(filename, 'w') as file:
        parser.write(file)

def load_machine(filename: str) -> ConfigParser:
    """Parse a machine.ini file and returns instances of the objects within."""
    parser = ConfigParser()
    parser.read(filename)

    return parser

def save(filename: str, obj: object) -> None:
    """Save an object to file."""
    with open(filename, 'wb') as file:
        pickle.dump(obj, file)


def load(filename: str, obj: object) -> object:
    """Load an object from file."""
    with open(filename, 'rb') as file:
        obj = _pickle_remodule_load(file) # pickle.load(file)

    return obj


def _pickle_remodule_load(file_obj):
    return _RemoduleUnpickler(file_obj).load()


def _pickle_remodule_loads(pickled_bytes):
    file_obj = io.BytesIO(pickled_bytes)
    return _pickle_remodule_loads(file_obj)
