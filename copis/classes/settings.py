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

    # def __init__(self, data: List[Dict[str, str]]) -> None:
    #     self._machine_data = next(filter(lambda d: d['name'].lower() == 'machine', data), None)
    #     self._device_data = [d for d in data if d['name'].lower().startswith('camera ')]

    #     self._parse_machine()
    #     self._parse_devices()

    # def as_dict(self):
    #     """Return a dictionary representation of a MachineSettings instance."""
    #     this = {}

    #     this.update(self._machine.as_dict())

    #     for device in self._devices:
    #         this.update(device.as_dict())

    #     return this

    # def _parse_machine(self) -> None:
    #     def get_boolean(value: str):
    #         trues = ['yes', 'on', 'true', '1']

    #         return value.lower() in trues

    #     datum = self._machine_data
    #     self._machine = None

    #     if datum is not None:
    #         size_x = float(datum['size_x'])
    #         size_y = float(datum['size_y'])
    #         size_z = float(datum['size_z'])
    #         origin_x = float(datum['origin_x'])
    #         origin_y = float(datum['origin_y'])
    #         origin_z = float(datum['origin_z'])
    #         homing_sequence = datum['homing_sequence'].splitlines()
    #         self._machine = Machine(vec3(size_x, size_y, size_z),
    #             vec3(origin_x, origin_y, origin_z), homing_sequence)

    #         if 'is_parallel_execution' in datum.keys():
    #             is_parallel_execution = get_boolean(datum['is_parallel_execution'])
    #             self._machine.is_parallel_execution = is_parallel_execution

    # def _parse_devices(self) -> None:
    #     data = self._device_data
    #     self._devices = []

    #     for datum in data:
    #         device_id = int(datum['id'])
    #         name = datum['name'].split(' ', maxsplit=1)[1]
    #         pos_x = float(datum['x'])
    #         pos_y = float(datum['y'])
    #         pos_z = float(datum['z'])
    #         pos_p = float(datum['p'])
    #         pos_t = float(datum['t'])
    #         device_bounds = BoundingBox(
    #             vec3(float(datum['min_x']),
    #                  float(datum['min_y']),
    #                  float(datum['min_z'])),
    #             vec3(float(datum['max_x']),
    #                  float(datum['max_y']),
    #                  float(datum['max_z'])))
    #         size = vec3(float(datum['size_x']),
    #                     float(datum['size_y']),
    #                     float(datum['size_z']))
    #         device_type = datum['type']
    #         interfaces = datum['interfaces'].splitlines()
    #         port = datum['port']

    #         device = Device(
    #             device_id=device_id,
    #             device_name=name,
    #             device_type=device_type,
    #             interfaces=interfaces,
    #             position=Point5(pos_x, pos_y, pos_z, pos_p, pos_t),
    #             initial_position=Point5(pos_x, pos_y, pos_z, pos_p, pos_t),
    #             device_bounds=device_bounds,
    #             collision_bounds=size,
    #             port=port)

    #         self._devices.append(device)

    # @property
    # def machine(self) -> Machine:
    #     """Machine configuration settings' machine getter."""
    #     return self._machine

    # @property
    # def devices(self) -> List[Device]:
    #     """Machine configuration settings' devices getter."""
    #     return self._devices
