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

"""Provide the COPIS SerialResponse Class."""

from dataclasses import dataclass

from copis.globals import Point5


@dataclass
class SerialResponse:
    """Data structure that implements a parsed COPIS serial response."""
    device_id: int = -1
    system_status_number: int = -1
    position: Point5 = Point5()
    error: str = None

    @property
    def system_status_flags(self) -> str:
        """Returns the system status flags, on per binary digit."""
        return f'{self.system_status_number:08b}' \
            if self.system_status_number >= 0 else None

    @property
    def is_idle(self) -> bool:
        """Returns a flag indicating where the serial connection is idle."""
        return self.system_status_number == 0
