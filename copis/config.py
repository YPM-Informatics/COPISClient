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

from .globals import DebugEnv, Size, Rectangle
from .store import Store
from .classes import ApplicationSettings, MachineSettings


class Config():
    """Handle application configuration."""

    _DEFAULT_CONFIG = {
        'App': {
            'window_min_size': '800,600',
            'debug_env': 'prod'
        },
        'Machine': {
            'is_parallel_execution': 'yes',
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

        # filepath = '\\projects\\ypm\\python\\COPISClient\\copis\\config\\copis1.ini'
        # with open(filepath, 'w') as configfile:
        #     self._config_parser.write(configfile)

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
        min_w, min_h = [int(d) for d in app['window_min_size'].split(',')]
        x, y, w, h = None, None, int(min_w), int(min_h)

        if 'window_geometry' in app:
            coords = [int(c) for c in app['window_geometry'].split(',')]
            if len(coords) == 4:
                x, y, w, h = coords
            elif len(coords) == 2:
                w, h = max(min_w, coords[0]), max(min_h, coords[1])
        else:
            w, h = [get_sixty_pct(d) for d in display_size]

        w = min(w, display_size.x)
        h = min(h, display_size.y)

        if x is not None and y is not None:
            if x < 0:
                x = 0
                w = max(min_w, w + x)
            if y < 0:
                y = 0
                h = max(min_h, h + y)
            if x + w > display_size.x:
                offset = x + w - display_size.x
                w = max(min_w, w - offset)
            if y + h > display_size.y:
                offset = y + h - display_size.y
                h = max(min_h, h - offset)
        else:
            x = int((display_size.x - w) / 2)
            y = int((display_size.y - h) / 2)

        app['window_geometry'] = f'{x},{y},{w},{h}'
        self._store.save_config_parser(parser)

        return parser

    def _populate_application_settings(self) -> ApplicationSettings:
        get_ints = lambda val: list(int(i) for i in val.split(','))

        section = 'App'
        app = self._config_parser[section]

        ints = get_ints(app['window_min_size'])
        window_min_size = Size(*ints)

        ints = get_ints(app['window_geometry'])
        window_geometry = Rectangle(*ints)

        debug_env = app['debug_env']

        if not any(e.value == debug_env for e in DebugEnv):
            debug_env = self._DEFAULT_CONFIG[section]['debug_env']

        return ApplicationSettings(DebugEnv(debug_env), window_min_size, window_geometry)

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

    def update_window_geometry(self, rect: Rectangle) -> None:
        """Updates the window geometry application setting."""
        self.application_settings.window_geometry = rect

        self._store.save_config(self)

    def as_dict(self):
        """"Return a dictionary representation of a Config instance."""
        config = {}
        config.update(self.application_settings.as_dict())
        config.update(self.machine_settings.as_dict())

        return config
