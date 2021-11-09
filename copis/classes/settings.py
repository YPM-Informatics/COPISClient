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

from copis.globals import DebugEnv, Point5
from . import Device, Machine, BoundingBox


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
        self._machine_data = next(filter(lambda d: d['name'].lower() == 'machine', data), None)
        self._device_data = [d for d in data if d['name'].lower().startswith('camera ')]

        self._parse_machine()
        self._parse_devices()

    def as_dict(self):
        """Return a dictionary representation of a MachineSettings instance."""
        this = {}

        this.update(self._machine.as_dict())

        for device in self._devices:
            this.update(device.as_dict())

        return this

    def _parse_machine(self) -> None:
        datum = self._machine_data
        self._machine = None

        if datum is not None:
            size_x = float(datum['size_x'])
            size_y = float(datum['size_y'])
            size_z = float(datum['size_z'])
            origin_x = float(datum['origin_x'])
            origin_y = float(datum['origin_y'])
            origin_z = float(datum['origin_z'])
            homing_sequence = datum['homing_sequence'].splitlines()
            self._machine = Machine(vec3(size_x, size_y, size_z),
                vec3(origin_x, origin_y, origin_z), homing_sequence)

    def _parse_devices(self) -> None:
        data = self._device_data
        self._devices = []

        for datum in data:
            device_id = int(datum['id'])
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
            device_type = datum['type']
            interfaces = datum['interfaces'].splitlines()
            port = datum['port']

            device = Device(
                device_id=device_id,
                device_name=name,
                device_type=device_type,
                interfaces=interfaces,
                position=Point5(pos_x, pos_y, pos_z, pos_p, pos_t),
                initial_position=Point5(pos_x, pos_y, pos_z, pos_p, pos_t),
                device_bounds=device_bounds,
                collision_bounds=size,
                port=port)

            self._devices.append(device)

    @property
    def machine(self) -> Machine:
        """Machine configuration settings' machine getter."""
        return self._machine

    @property
    def devices(self) -> List[Device]:
        """Machine configuration settings' devices getter."""
        return self._devices
