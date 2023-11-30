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

"""Provide the COPIS Configuration class"""

from glm import vec3
import copis.store as store
from .globals import DebugEnv, Size, WindowState
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

    _MAX_RECENT_PROJECTS_COUNT = 5

    def __init__(self, display_size) -> None:
        self._config_parser = store.load_config()
        self._ensure_window_state_exists(display_size, self._config_parser)
        self._application_settings = self._populate_application_settings()
        self._machine_settings = self._populate_machine_settings()

        self._log_serial_tx = False
        self._log_serial_rx = False
        db_path = store.get_sys_db_path()

        if db_path and self._config_parser.has_option('System', 'log_serial_tx'):
            self._log_serial_tx = _get_bool(self._config_parser['System']['log_serial_tx'])

        if db_path and self._config_parser.has_option('System', 'log_serial_rx'):
            self._log_serial_rx = _get_bool(self._config_parser['System']['log_serial_rx'])

    @property
    def log_serial_tx(self) -> bool:
        """Returns a flag indicating whether to log serial Tx, if a database is configured."""
        return self._log_serial_tx

    @property
    def log_serial_rx(self) -> bool:
        """Returns a flag indicating whether to log serial Rx, if a database is configured."""
        return self._log_serial_rx

    @property
    def application_settings(self) -> ApplicationSettings:
        """Application configuration settings getter."""
        return self._application_settings

    @property
    def machine_settings(self) -> MachineSettings:
        """Machine configuration settings getter."""
        return self._machine_settings

    def _ensure_window_state_exists(self, display_rect, parser):
        get_sixty_pct = lambda val: int(val * 60 / 100)

        app = parser['App']

        min_width, min_height = [int(d) for d in app['window_min_size'].split(',')]
        x, y, width, height, is_maximized = None, None, int(min_width), int(min_height), False

        if 'window_state' in app:
            state_parts = _get_state_parts(app['window_state'])
            x, y, width, height, is_maximized = state_parts
        else:
            width, height = [get_sixty_pct(d) for d in display_rect[2:4]]

        if not is_maximized:
            if x is not None and y is not None:
                if x < 0:
                    width = max(min_width, width + x)
                    x = 0
                if y < 0:
                    height = max(min_height, height + y)
                    y = 0
                if x > display_rect.X + display_rect.Width:
                    offset = x - display_rect.X
                    width = max(min_width, width - offset)
                    x = x - offset
                if y  > display_rect.Y + display_rect.Height:
                    offset = y - display_rect.Y
                    height = max(min_height, height - offset)
                    y = y - offset
                if x + width > display_rect.X + display_rect.Width:
                    offset = x + width - display_rect.X - display_rect.Width
                    width = max(min_width, width - offset)
                if y + height > display_rect.Y+ display_rect.Height:
                    offset = y + height - display_rect.Y - display_rect.Height
                    height = max(min_height, height - offset)
            else:
                x = int((display_rect.X - width) / 2)
                y = int((display_rect.Y - height) / 2)

            app['window_state'] = f'{x},{y},{width},{height},{is_maximized}'
            store.save_config_parser(parser)

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
            debug_env = 'prod'

        app_settings = ApplicationSettings(DebugEnv(debug_env), window_min_size, window_state)

        key = 'last_output_path'
        if key in app:
            last_output_path = app[key]
            if last_output_path:
                app_settings.last_output_path = last_output_path

        key = 'recent_projects'
        if key in app:
            recent_projects = app[key]
            if recent_projects:
                app_settings.recent_projects = [
                    l.strip('\t') for l in recent_projects.splitlines()]

        return app_settings

    def _populate_machine_settings(self) -> MachineSettings:
        section = 'Machine'
        machine = self._config_parser[section]

        size_x = machine.getfloat('size_x')
        size_y = machine.getfloat('size_y')
        size_z = machine.getfloat('size_z')
        origin_x = machine.getfloat('origin_x')
        origin_y = machine.getfloat('origin_y')
        origin_z = machine.getfloat('origin_z')

        origin = vec3(origin_x, origin_y, origin_z)
        dimensions = vec3(size_x, size_y, size_z)

        return MachineSettings(origin, dimensions)

    def update_window_state(self, state: WindowState) -> None:
        """Updates the window geometry application setting."""
        self.application_settings.window_state = state

        store.save_config(self)

    def update_recent_projects(self, path: str) -> None:
        """Updates the recent projects and last output path application settings."""
        self.application_settings.last_output_path = store.get_directory(path)
        self.application_settings.recent_projects.insert(0, path)

        if len(self.application_settings.recent_projects) > self._MAX_RECENT_PROJECTS_COUNT:
            self.application_settings.recent_projects = self.application_settings.recent_projects[
                :self._MAX_RECENT_PROJECTS_COUNT]

        store.save_config(self)

    def remove_recent_project(self, path: str) -> None:
        """Removes a recent projects entry."""
        recent_projects = list(map(str.lower, self.application_settings.recent_projects))
        index = recent_projects.index(path.strip().lower())

        if index >= 0:
            self.application_settings.recent_projects.pop(index)
            store.save_config(self)

    def as_dict(self):
        """"Return a dictionary representation of a Config instance."""
        config = {}
        config.update(self.application_settings.as_dict())
        config.update(self.machine_settings.as_dict())

        return config
