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

"""Provide the COPIS Configuration class"""

from configparser import ConfigParser
from glm import vec3

from .globals import DebugEnv, Size, WindowState
from .store import Store
from .classes import ApplicationSettings, MachineSettings


def _get_bool(val):
    return val.lower() in ['yes', 'on', 'true', '1']


def _get_state_parts(state_str):
    parts = state_str.split(',')

    return list(int(s)
        if i < len(parts) - 1 else _get_bool(s)
            for i, s in enumerate(parts))


class Config():
    """Handle application configuration."""

    _DEFAULT_CONFIG = {
        'App': {
            'window_min_size': '800,600',
            'debug_env': 'prod'
        },
        'Machine': {
            'is_parallel_execution': 'True',
            'size_x': '700',
            'size_y': '800',
            'size_z': '450',
            'origin_x': '350',
            'origin_y': '400',
            'origin_z': '0'
        }
    }

    def __init__(self, display_size) -> None:
        self._store = Store()
        self._config_parser = self._ensure_config_exists(display_size)

        self._application_settings = self._populate_application_settings()
        self._machine_settings = self._populate_machine_settings()

    @property
    def application_settings(self) -> ApplicationSettings:
        """Configuration settings getter."""
        return self._application_settings

    @property
    def machine_settings(self) -> MachineSettings:
        """Machine configuration settings getter."""
        return self._machine_settings

    def _ensure_config_exists(self, display_size) -> ConfigParser:
        get_sixty_pct = lambda val: int(val * 60 / 100)

        parser = self._store.load_config()

        if parser is None:
            parser = ConfigParser()

            parser['App'] = self._DEFAULT_CONFIG['App']
            parser['Machine'] = self._DEFAULT_CONFIG['Machine']

            self._store.save_config_parser(parser)

        app = parser['App']
        min_width, min_height = [int(d) for d in app['window_min_size'].split(',')]
        x, y, width, height, is_maximized = None, None, int(min_width), int(min_height), False

        if 'window_state' in app:
            x, y, width, height, is_maximized = _get_state_parts(app['window_state'])
        else:
            width, height = [get_sixty_pct(d) for d in display_size]

        width = min(width, display_size.x)
        height = min(height, display_size.y)

        if not is_maximized:
            if x is not None and y is not None:
                if x < 0:
                    x = 0
                    width = max(min_width, width + x)
                if y < 0:
                    y = 0
                    height = max(min_height, height + y)
                if x + width > display_size.x:
                    offset = x + width - display_size.x
                    width = max(min_width, width - offset)
                if y + height > display_size.y:
                    offset = y + height - display_size.y
                    height = max(min_height, height - offset)
            else:
                x = int((display_size.x - width) / 2)
                y = int((display_size.y - height) / 2)

            app['window_state'] = f'{x},{y},{width},{height},{is_maximized}'
            self._store.save_config_parser(parser)

        return parser

    def _populate_application_settings(self) -> ApplicationSettings:
        get_size_parts = lambda val: list(int(i) for i in val.split(','))

        section = 'App'
        app = self._config_parser[section]

        parts = get_size_parts(app['window_min_size'])
        window_min_size = Size(*parts)

        parts = _get_state_parts(app['window_state'])
        window_state = WindowState(*parts)

        debug_env = app['debug_env']

        if not any(e.value == debug_env for e in DebugEnv):
            debug_env = self._DEFAULT_CONFIG[section]['debug_env']

        return ApplicationSettings(DebugEnv(debug_env), window_min_size, window_state)

    def _populate_machine_settings(self) -> MachineSettings:
        section = 'Machine'
        machine = self._config_parser[section]

        size_x = machine.getfloat('size_x')
        size_y = machine.getfloat('size_y')
        size_z = machine.getfloat('size_z')
        origin_x = machine.getfloat('origin_x')
        origin_y = machine.getfloat('origin_y')
        origin_z = machine.getfloat('origin_z')
        is_parallel_execution = machine.getboolean('is_parallel_execution')

        origin = vec3(origin_x, origin_y, origin_z)
        dimensions = vec3(size_x, size_y, size_z)

        return MachineSettings(origin, dimensions, is_parallel_execution)

    def update_window_state(self, state: WindowState) -> None:
        """Updates the window geometry application setting."""
        self.application_settings.window_state = state

        self._store.save_config(self)

    def as_dict(self):
        """"Return a dictionary representation of a Config instance."""
        config = {}
        config.update(self.application_settings.as_dict())
        config.update(self.machine_settings.as_dict())

        return config
