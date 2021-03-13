#!/usr/bin/env python3

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

import os
from pathlib import Path

_PROJECT_FOLDER = 'copis'

_current = os.path.dirname(__file__)
_segments = _current.split(os.sep)
_index = _segments.index(_PROJECT_FOLDER)
_root_segments = _segments[1:_index]

_root = '/' + Path(os.path.join(*_root_segments)).as_posix()

def find(filename: str = '') -> str:
    paths = [p for p in Path(_root).rglob(filename)]

    return str(paths[0]) if len(paths) > 0 else ''