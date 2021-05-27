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

"""Provide the COPIS Action Class."""

from dataclasses import dataclass
from typing import Any, List, Optional

from copis.enums import ActionType

@dataclass
class Action:
    """Data structure that implements a camera action."""

    atype: ActionType = ActionType.NONE
    device: int = -1
    argc: int = 0
    args: Optional[List[Any]] = None
