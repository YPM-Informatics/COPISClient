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

import os

from pathlib import Path, PurePath
from configparser import ConfigParser
from typing import List

from settings import Settings
from session_image import SessionImage


class Store():
    """Handles application-wide data storage operations."""

    _PROJECT_FOLDER = 'copis'

    _CONFIG_FOLDER = 'config'
    _CONFIG_FILE = 'app.ini'

    # _SESSION_DIR = os.path.join(_CONFIG_DIR, 'sessions')


    def __init__(self) -> None:
        current = os.path.dirname(__file__)
        segments = current.split(os.sep)
        index = segments.index(self._PROJECT_FOLDER)
        root_segments = segments[1:index]

        root = '/' + Path(os.path.join(*root_segments)).as_posix()
        
        self._root_dir = Path(root)
        self._config_dir = Path(os.path.join(root, self._PROJECT_FOLDER, self._CONFIG_FOLDER))
        self._config_path = Path(os.path.join(self._config_dir, self._CONFIG_FILE))
        # self._session_dir = Path(self._SESSION_DIR)

        if not self._config_dir.exists():
            self._config_dir.mkdir(parents = True, exist_ok = True)
        
        # if not self._session_dir.exists():
        #     self._session_dir.mkdir(parents = True, exist_ok = True)


    def save_config(self, parser: ConfigParser) -> None:
        with self._config_path.open('w', -1) as f:
            parser.write(f)


    def save_config_settings(self, settings: Settings) -> None:
        parser = ConfigParser()
        parser.read_dict(settings.as_dict())

        self.save_config(parser)


    def load_config(self) -> ConfigParser:
        if self._config_path.exists():
            parser = ConfigParser()
            parser.read(self._config_path)

            return parser
        else:
            return None


    def create_session_path(self) -> str:
        """Returns new session path. Checks folder names first"""
        pass


    def check_session_path(self) -> bool:
        """Verifies that a session path exists"""
        pass


    def save_session_script(self, filename: str) -> None:
        """Saves session script, which is the action list"""
        pass


    def load_session_script(self, filename: str) -> None:
        """Saves session script, which is the action list"""
        pass


    def save_session_images(self, images: List[SessionImage]) -> None:
        """Saves session images and image metadata"""
        pass
