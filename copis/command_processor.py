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

"""COPIS Application action commands processor."""


import re

from itertools import chain

from .classes.action import Action
from .models.g_code import Gcode
from .helpers import rad_to_dd, is_number


def deserialize_command(cmd: str) -> Action:
    """deserialize the string of an action into an Action object."""
    segments = re.split('([a-zA-Z])', cmd)
    device_id = 0
    atype = None
    args = []

    for i, segment in enumerate(segments):
        if segment.startswith('>'):
            device_id = int(segment[1:])
        elif len(segment) > 0 and segment.upper() in 'CGM':
            cmd = f'{segment}{segments[i + 1]}'
            atype = Gcode[cmd.upper()]

        elif len(segment) > 0 and segment.upper() in 'XYZPTFSV':
            args.append((segment, segments[i + 1]))

    return Action(atype, device_id, len(args), args)

def serialize_command(action: Action) -> str:
    """Serialize an Action object into a string."""
    get_g_code = lambda input: str(input).split('.')[1]

    g_code = get_g_code(action.atype)
    dest = '' if action.device == 0 else f'>{action.device}'

    args = action.args.copy() if action.args else []

    if args and len(args) > 0:
        for i, arg in enumerate(args):
            value = str(arg[1])

            if is_number(value):
                value = float(arg[1])

                if g_code[0] == 'G' and arg[0] in 'PT':
                    value = rad_to_dd(value)

                args[i] = (arg[0], f'{value}')

    g_cmd = ''.join(chain.from_iterable(args))

    return f'{dest}{g_code}{g_cmd}'
