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

"""Provide the COPIS Settings class"""

from dataclasses import dataclass
from math import inf
from glm import vec3

from copis.globals import DebugEnv, Size, WindowState


@dataclass
class ApplicationSettings:
    """Application settings data structure."""
    debug_env: DebugEnv = DebugEnv.PROD
    window_min_size: Size = Size(800, 600)
    window_state: WindowState = WindowState(0, 0, 800, 600, False)

    def as_dict(self):
        """Return a dictionary representation of an ApplicationSettings instance."""
        stringify = lambda val: ','.join([str(d) for d in val])

        return {
            'App': {
                'window_min_size': stringify(self.window_min_size),
                'debug_env': self.debug_env.value,
                'window_state': stringify(self.window_state)
            }
        }

@dataclass
class MachineSettings:
    """Machine settings settings data structure."""
    origin: vec3 = vec3(inf)
    dimensions: vec3 = vec3(inf)
    is_parallel_execution: bool = True

    def as_dict(self):
        """"Return a dictionary representation of a MachineSettings instance."""

        return {
            'Machine': {
                'is_parallel_execution': self.is_parallel_execution,
                'size_x': self.dimensions.x,
                'size_y': self.dimensions.y,
                'size_z': self.dimensions.z,
                'origin_x': self.origin.x,
                'origin_y': self.origin.y,
                'origin_z': self.origin.z
            }
        }
