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

"""Provide the COPIS SerialResponse Class."""
from typing import List

from dataclasses import dataclass

from copis.globals import Point5, SysStatFlags


@dataclass
class SerialResponse:
    """Data structure that implements a parsed COPIS serial response."""
    device_id: int = -1
    system_status_number: int = -1
    position: Point5 = Point5()
    error: str = None

    @property
    def is_idle(self) -> bool:
        """Returns a flag indicating where the serial connection is idle."""
        return self.system_status_number == 0

    @property
    def is_locked(self) -> bool:
        """Returns a flag indicating where the serial connection is idle."""
        return False if self.system_status_number < 0 else self.system_status_number & (1 << SysStatFlags.STA_LOCK.value) > 0

    def parse_sys_stat(self) -> List:
        """Returns system status as a listing of active flags, Empty list is idle."""
        ret = []
        if self.system_status_number & (1 << SysStatFlags.STA_PROC_SERIAL.value):
            ret.append(SysStatFlags.STA_PROC_SERIAL)
        if self.system_status_number & (1 << SysStatFlags.STA_PROC_TWI.value):
            ret.append(SysStatFlags.STA_PROC_TWI)
        if self.system_status_number & (1 << SysStatFlags.STA_CMD_AVAIL.value):
            ret.append(SysStatFlags.STA_CMD_AVAIL)
        if self.system_status_number & (1 << SysStatFlags.STA_GC_EXEC.value):
            ret.append(SysStatFlags.STA_GC_EXEC)
        if self.system_status_number & (1 << SysStatFlags.STA_MOTION_QUEUED.value):
            ret.append(SysStatFlags.STA_MOTION_QUEUED)
        if self.system_status_number & (1 << SysStatFlags.STA_MOTION_EXEC.value):
            ret.append(SysStatFlags.STA_MOTION_EXEC)
        if self.system_status_number & (1 << SysStatFlags.STA_HOMING.value):
            ret.append(SysStatFlags.STA_HOMING)
        if self.system_status_number & (1 << SysStatFlags.STA_LOCK.value):
            ret.append(SysStatFlags.STA_LOCK)
        return ret
