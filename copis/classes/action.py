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

"""Provide the COPIS Action Class."""
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, List, Optional

from copis.globals import ActionType

@dataclass
class Action(dict):
    """Data structure that implements a camera action."""
    atype: ActionType = ActionType.NONE
    device: int = -1
    argc: int = 0
    args: Optional[List[Any]] = None

    def __post_init__(self):
        a_type = self.atype
        if isinstance(a_type, str):
            a_type = a_type.upper()
            if any(t.name == a_type for t in ActionType):
                a_type = ActionType[a_type]
            else:
                a_type = ActionType.NONE
            self.__dict__['atype'] = a_type
        a_type_name = a_type.name
        a_dict = deepcopy(self.__dict__)
        a_dict['atype'] = a_type_name
        dict.__init__(self, a_dict)

    def update(self):
        """Updates the action instance's dictionary store."""
        a_type = self.atype
        a_type_name = a_type.name
        a_dict = deepcopy(self.__dict__)
        a_dict['atype'] = a_type_name
        dict.update(self, a_dict)
