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

"""Provides the COPIS machine related data structures."""

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from copis.models.geometries import BoundingBox, Point5, Size3

class ControllerStatusFlags(Enum):
    """Bit positions for each COPIS controller status flag."""
    STA_PROC_SERIAL = 0
    STA_PROC_TWI = 1
    STA_CMD_AVAIL = 2
    STA_GC_EXEC = 3
    STA_MOTION_QUEUED = 4
    STA_MOTION_EXEC = 5
    STA_HOMING = 6
    STA_LOCK = 7


class DeviceGroup:
    """Data structure representing a logical group of devices (i.e.: from the same chamber).

        Attributes:
            main_device: main device (role>=1) that orchestrates the others.
            aux_devices: secondary (auxiliary) devices.
            tx_thread: transmit (write) thread.
            rx_thread: receive (read) thread.
    """
    def __init__(self, main_device = None, aux_devices = None, tx_thread = None, rx_thread = None) -> None:
        self.main_device = main_device
        self.aux_devices = aux_devices
        self.tx_thread = tx_thread
        self.rx_thread = rx_thread

    def execute_raw(self, g_code: str) -> None:
        """Executes a string of g-code."""
        # TODO: to be implemented.
        pass


@dataclass
class DeviceSettings:
    """Data structure that holds a device's settings (from its controller)."""
    _KEY_MAP: ClassVar[dict] = {
        'Device id': 'device_id',
        'Role': 'role',
        'Use I2C Settings': 'use_i2c_settings',
        'HW version': 'hardware_version',
        'FW version': 'firmware_version',
        'Polling [ms]': 'polling_ms',
        'Serial reporting': 'serial_reporting',
        'Debug general': 'debug_general',
        'Debug communications': 'debug_communications',
        'Debug motion control': 'debug_motion_control',
        'Debug camera control': 'debug_camera_control',
        'X [step/mm]': 'x_steps_per_mm',
        'Y [step/mm]': 'y_steps_per_mm',
        'Z [step/mm]': 'z_steps_per_mm',
        'P [step/dd]': 'p_steps_per_dd',
        'T [step/dd]': 't_steps_per_dd',
        'Default feed [mm_or_dd/min]': 'default_feed_mm_or_dd_per_min',
        'Default seek [mm_or_dd/min]': 'default_seek_mm_or_dd_per_min',
        'Default homing feed [mm_or_dd/min]': 'default_homing_feed_mm_or_dd_per_min',
        'Max speed X [mm/min]': 'max_speed_x_steps_per_mm',
        'Max speed Y [mm/min]': 'max_speed_y_steps_per_mm',
        'Max speed Z [mm/min]': 'max_speed_z_steps_per_mm',
        'Max speed P [dd/min]': 'max_speed_p_steps_per_dd',
        'Max speed T [dd/min]': 'max_speed_t_steps_per_dd',
        'Acceleration [mm_or_dd/sec^2]': 'acceleration_mm_or_dd_per_sec_sq',
        'Junction Deviation [mm_or_dd]': 'junction_deviation_mm_or_dd',
        'Step pulse [usec]': 'step_puls_usec',
        'X Home [mm]': 'x_home_mm',
        'Y Home [mm]': 'y_home_mm',
        'Z Home [mm]': 'z_home_mm',
        'P Home [dd]': 'p_home_dd',
        'T Home [dd]': 't_home_dd',
        'X Home Offset [mm]': 'x_home_offset_mm',
        'Y Home Offset [mm]': 'y_home_offset_mm',
        'Z Home Offset [mm]': 'z_home_offset_mm',
        'P Home Offset [dd]': 'p_home_offset_dd',
        'T Home Offset [dd]': 't_home_offset_dd',
        'X Min [mm]': 'x_min_mm',
        'Y Min [mm]': 'y_min_mm',
        'Z Min [mm]': 'z_min_mm',
        'P Min [dd]': 'p_min_dd',
        'T Min [dd]': 't_min_dd',
        'X Max [mm]': 'x_max_mm',
        'Y Max [mm]': 'y_max_mm',
        'Z Max [mm]': 'z_max_mm',
        'P Max [dd]': 'p_max_dd',
        'T Max [dd]': 't_max_dd',
        'Multi-Turn Enabled': 'multi_turn_enabled',
        'Stepper Idle Lock Time [ms]': 'stepper_idle_lock_time_ms',
        'Stepper Idle Lock Time Out [ms]': 'stepper_idle_lock_timeout_ms',
        'Invert X': 'invert_x',
        'Invert Y': 'invert_y',
        'Invert Z': 'invert_z',
        'Invert P': 'invert_p',
        'Invert T': 'invert_t'
    }

    device_id: int = None
    role: int = None
    use_i2c_settings: bool = None
    hardware_version: float = None
    firmware_version: float = None
    polling_ms: float = None
    serial_reporting: bool = None
    debug_general: bool = None
    debug_communications: bool = None
    debug_motion_control: bool = None
    debug_camera_control: bool = None
    x_steps_per_mm: float = None
    y_steps_per_mm: float = None
    z_steps_per_mm: float = None
    p_steps_per_dd: float = None
    t_steps_per_dd: float = None
    default_feed_mm_or_dd_per_min: float = None
    default_seek_mm_or_dd_per_min: float = None
    default_homing_feed_mm_or_dd_per_min: float = None
    max_speed_x_steps_per_mm: float = None
    max_speed_y_steps_per_mm: float = None
    max_speed_z_steps_per_mm: float = None
    max_speed_p_steps_per_dd: float = None
    max_speed_t_steps_per_dd: float = None
    acceleration_mm_or_dd_per_sec_sq: float = None
    junction_deviation_mm_or_dd: float = None
    step_puls_usec: float = None
    x_home_mm: float = None
    y_home_mm: float = None
    z_home_mm: float = None
    p_home_dd: float = None
    t_home_dd: float = None
    x_home_offset_mm: float = None
    y_home_offset_mm: float = None
    z_home_offset_mm: float = None
    p_home_offset_dd: float = None
    t_home_offset_dd: float = None
    x_min_mm: float = None
    y_min_mm: float = None
    z_min_mm: float = None
    p_min_dd: float = None
    t_min_dd: float = None
    x_max_mm: float = None
    z_max_mm: float = None
    y_max_mm: float = None
    p_max_dd: float = None
    t_max_dd: float = None
    multi_turn_enabled: bool = None
    stepper_idle_lock_time_ms: float = None
    stepper_idle_lock_timeout_ms: float = None
    invert_x: bool = None
    invert_y: bool = None
    invert_z: bool = None
    invert_p: bool = None
    invert_t: bool = None


@dataclass
class Device:
    """Data structure that represents an imaging device; e.g.: a camera and a COPIS controller pair.

        Attributes:
            id: identifier.
            role: a primary device has a role >= 1, all others have 0.
            name: a short device description.
            type: the device's imaging hardware name, e.g.: Camera,
            serial_no: the device's imaging hardware serial number.
            group: a reference to the group the device belongs to.
            gantry_orientation: orientation of the device's gantry.
            edsdk_save_to_path: path to output edsdk data for the device.
            home_position: the coordinates of the device at its homed position.
            range_3d: The available 3 dimensional range of move for the device.
            head_radius: the device's head radius.
            head_dims: the devices's head dimensions.
            z_body_dims: the device's Z axis body dimensions.
            gantry_dims: the device's X axis dimensions.
            settings: the device's controller's settings.
            description: a long device description.
    """
    id: int = None
    role: int = None
    name: str = None
    type: str = None
    serial_no: str = None
    group: DeviceGroup = None
    gantry_orientation: int = None
    edsdk_save_to_path: str = None
    home_position: Point5 = None
    range_3d: BoundingBox = None
    head_radius: float = None
    head_dims: Size3 = None
    z_body_dims: Size3 = None
    gantry_dims: Size3 = None
    settings: DeviceSettings = None
    description: str = None
