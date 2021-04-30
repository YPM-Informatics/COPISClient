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

from dataclasses import dataclass

from .enums import DebugEnv

@dataclass
class ConfigSettings:
    """Configuration settings data structure"""
    debug_env: DebugEnv

    app_window_width: int
    app_window_height: int

    machine_config_path: str

    def as_dict(self):
        """Return a dictionary representation of a Settings instance."""
        return {
            'AppWindow': {
                'width': self.app_window_width,
                'height': self.app_window_height
            },
            'Debug': {
                'env': self.debug_env
            },
            'Machine': {
                'path': self.machine_config_path
            }
        }
