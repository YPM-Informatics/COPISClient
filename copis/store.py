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
import pickle

from pathlib import PurePath
from configparser import ConfigParser

from settings import Settings

class Store():
    """Handles application-wide data storage operations."""

    _PROJECT_FOLDER = 'copis'

    _CONFIG_FOLDER = 'config'
    _CONFIG_FILE = 'app.ini'


    def __init__(self) -> None:
        current = os.path.dirname(__file__)
        segments = current.split(os.sep)
        index = segments.index(self._PROJECT_FOLDER)
        root_segments = segments[1:index]

        root = '/' + PurePath(os.path.join(*root_segments)).as_posix()

        self._root_dir = root
        self._config_dir = os.path.join(root, self._PROJECT_FOLDER, self._CONFIG_FOLDER)
        self._config_path = os.path.join(self._config_dir, self._CONFIG_FILE)

        if not os.path.exists(self._config_dir):
            os.makedirs(self._config_dir)


    def save_config(self, parser: ConfigParser) -> None:
        """Saves a configuration object to file."""
        with open(self._config_path, 'w') as file:
            parser.write(file)


    def save_config_settings(self, settings: Settings) -> None:
        """Saves a configuration object to file, via its settings object."""
        parser = ConfigParser()
        parser.read_dict(settings.as_dict())

        self.save_config(parser)


    def load_config(self) -> ConfigParser:
        """Load a configuration object from file"""
        if os.path.exists(self._config_path):
            parser = ConfigParser()
            parser.read(self._config_path)

            return parser

        return None


    def save(self, filename: str, obj: object) -> None:
        """Saves an object to file"""
        with open(filename, 'wb') as file:
            pickle.dump(obj, file)


    def load(self, filename: str, obj: object) -> object:
        """Loads as object from file"""
        with open(filename, 'rb') as file:
            obj = pickle.load(file)

        return obj
