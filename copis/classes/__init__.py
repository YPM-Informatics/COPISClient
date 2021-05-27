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

"""COPIS classes package."""

from .device import Device
from .bounding_box import BoundingBox
from .proxy import Proxy
from .action import Action
from .chamber import Chamber
from .monitored_list import MonitoredList
from .settings import ConfigSettings, MachineSettings

__all__ = ["Device", "BoundingBox", "Proxy", "Action", "Chamber",
            "MonitoredList", "ConfigSettings", "MachineSettings"]
