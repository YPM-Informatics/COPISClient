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

from configparser import ConfigParser

from enums import DebugEnv
from store import Store
from settings import Settings


class Config():
    """Handles application configuration."""

    _DEFAULT_DEBUG_ENV = DebugEnv.PROD
    _DEFAULT_APP_WINDOW_WIDTH = 1400
    _DEFAULT_APP_WINDOW_HEIGHT = 1000

    def __init__(self) -> None:
        self._store = Store()
        self._config_parser = self._ensure_config_exists()
        self._settings = self._populate_settings()

    def _ensure_config_exists(self) -> ConfigParser:
        parser = self._store.load_config()

        if parser is None:
            parser = ConfigParser()

            parser['AppWindow'] = {
                'width': str(self._DEFAULT_APP_WINDOW_WIDTH),
                'height': str(self._DEFAULT_APP_WINDOW_HEIGHT)
            }

            parser['Debug'] = {
                'env': self._DEFAULT_DEBUG_ENV.value
            }

            self._store.save_config(parser)

        return parser

    def _populate_settings(self) -> Settings:
        app_window_height = self._config_parser.getint('AppWindow',
            'height', fallback=self._DEFAULT_APP_WINDOW_HEIGHT)

        app_window_width = self._config_parser.getint('AppWindow',
            'width', fallback=self._DEFAULT_APP_WINDOW_WIDTH)

        debug_env = self._config_parser.get('Debug', 'env',
            fallback = self._DEFAULT_DEBUG_ENV)

        if not any(e.value == debug_env for e in DebugEnv):
            debug_env = self._DEFAULT_DEBUG_ENV

        devices = self._config_parser.get('Devices', 'items', fallback = '').splitlines()

        return Settings(debug_env, app_window_width, app_window_height, devices)


    @property
    def settings(self) -> Settings:
        """Settings getter"""
        return self._settings
