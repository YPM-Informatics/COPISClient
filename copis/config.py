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

from pathlib import Path
from configparser import ConfigParser
from dataclasses import dataclass

from enums import DebugEnv


@dataclass
class Settings:
    debug_env: str

    app_window_width: int
    app_window_height: int


class Config():
    """Handles application configuration."""

    _DEFAULT_CONFIG_PATH = os.environ.get('COPISCONFIG',
        os.path.expanduser(f'~{os.sep}.copis{os.sep}config.ini'))

    _DEFAULT_DEBUG_ENV = DebugEnv.PROD
    _DEFAULT_APP_WINDOW_WIDTH = 1400
    _DEFAULT_APP_WINDOW_HEIGHT = 1000


    def __init__(self) -> None:
        self._config_parser = self._ensure_config_exists(self._DEFAULT_CONFIG_PATH)
        self.settings = self._populate_settings()


    def _ensure_config_exists(self, file_path: str) -> ConfigParser:
        path = Path(file_path)
        parser = ConfigParser()
        
        if path.exists():
            parser.read(file_path)
        else:
            parser['AppWindow'] = {
                'width': str(self._DEFAULT_APP_WINDOW_WIDTH),
                'height': str(self._DEFAULT_APP_WINDOW_HEIGHT)
            }

            parser['Debug'] = {
                'env': str(self._DEFAULT_DEBUG_ENV)
            }

            path.parent.mkdir(parents = True, exist_ok = True)
            with path.open('w', -1) as f:
                parser.write(f)

        return parser


    def _populate_settings(self) -> Settings:
        app_window_height = self._config_parser.getint('AppWindow',
            'height', fallback = self._DEFAULT_APP_WINDOW_HEIGHT)

        app_window_width = self._config_parser.getint('AppWindow',
            'width', fallback = self._DEFAULT_APP_WINDOW_WIDTH)

        debug_env = self._config_parser.get('Debug', 'env',
            fallback = self._DEFAULT_DEBUG_ENV)

        if not any(e.value == debug_env for e in DebugEnv):
            debug_env = self._DEFAULT_DEBUG_ENV

        return Settings(debug_env, app_window_width, app_window_height)

