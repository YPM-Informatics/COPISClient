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
from typing import List, Dict
from glm import vec3

from copis.enums import DebugEnv
from copis.helpers import Point5
from . import Device, Chamber, BoundingBox

@dataclass
class ConfigSettings:
    """Configuration settings data structure."""
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


class MachineSettings:
    """Machine configuration settings data structure."""
    def __init__(self, data: List[Dict[str, str]]) -> None:
        self._chamber_data = [d for d in data if d['name'].lower().startswith('chamber ')]
        self._device_data = [d for d in data if d['name'].lower().startswith('camera ')]

        self._parse_chambers()
        self._parse_devices()

    def as_dict(self):
        """Return a dictionary representation of a MachineSettings instance."""
        this = {}
        for chamber in self._chambers:
            this.update(chamber.as_dict())

        for device in self._devices:
            this.update(device.as_dict())

        return this

    def _parse_chambers(self) -> None:
        data = self._chamber_data
        self._chambers = []

        for i, datum in enumerate(data):
            name = datum['name'].split(' ', maxsplit=1)[1]
            min_x = float(datum['min_x'])
            min_y = float(datum['min_y'])
            min_z = float(datum['min_z'])
            max_x = float(datum['max_x'])
            max_y = float(datum['max_y'])
            max_z = float(datum['max_z'])
            port = datum['port']

            box = BoundingBox(vec3(min_x, min_y, min_z), vec3(max_x, max_y, max_z))
            chamber = Chamber(i, name, box, port)
            self._chambers.append(chamber)

    def _parse_devices(self) -> None:
        data = self._device_data
        self._devices = []

        for i, datum in enumerate(data):
            name = datum['name'].split(' ', maxsplit=1)[1]
            pos_x = float(datum['x'])
            pos_y = float(datum['y'])
            pos_z = float(datum['z'])
            pos_p = float(datum['p'])
            pos_t = float(datum['t'])
            device_bounds = BoundingBox(
                vec3(float(datum['min_x']),
                     float(datum['min_y']),
                     float(datum['min_z'])),
                vec3(float(datum['max_x']),
                     float(datum['max_y']),
                     float(datum['max_z'])))
            size = vec3(float(datum['size_x']),
                        float(datum['size_y']),
                        float(datum['size_z']))
            chamber_name = datum['chamber']
            device_type = datum['type']
            interfaces = datum['interfaces'].splitlines()
            home = '' if 'home' not in datum.keys() else datum['home']

            device = Device(
                device_id=i,
                device_name=name,
                device_type=device_type,
                chamber_name=chamber_name,
                interfaces=interfaces,
                position=Point5(pos_x, pos_y, pos_z, pos_p, pos_t),
                initial_position=Point5(pos_x, pos_y, pos_z, pos_p, pos_t),
                device_bounds=device_bounds,
                collision_bounds=size,
                homing_sequence=home)

            self._devices.append(device)

    @property
    def chambers(self) -> List[Chamber]:
        """Machine configuration settings' chambers getter."""
        return self._chambers

    @property
    def devices(self) -> List[Device]:
        """Machine configuration settings' devices getter."""
        return self._devices
