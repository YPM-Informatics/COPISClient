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


from pickle import TRUE
import re

from itertools import chain

from .classes.action import Action
from .globals import ActionType
from .helpers import rad_to_dd, is_number


def deserialize_command(cmd: str) -> Action:
    """deserialize the string of an action into an Action object."""
    segments = re.split('([a-zA-Z])', cmd)
    device_id = 0
    atype = ActionType.NONE
    args = []

    for i, segment in enumerate(segments):
        if segment.startswith('>'):
            device_id = int(segment[1:])
        elif len(segment) > 0 and segment.upper() in 'CGM':
            cmd = f'{segment}{segments[i + 1]}'
            atype = ActionType[cmd.upper()]

        elif len(segment) > 0 and segment.upper() in 'XYZPTFSV':
            args.append((segment, segments[i + 1]))

    return Action(atype, device_id, len(args), args)

def serialize_command(action: Action) -> str:
    """Serialize an Action object into a string."""
    get_g_code = lambda input: str(input).split('.')[1]

    g_code = get_g_code(action.atype)
    dest = '' if action.device == 0 else f'>{action.device}'

    args = action.args.copy() if action.args else []
    raw = False
    if hasattr(action, '_raw'):
        raw = action._raw
    
    if args and len(args) > 0:
        for i, arg in enumerate(args):
            value = str(arg[1])

            if is_number(value):
                value = float(arg[1])
                #values for poses are currently stored in actions as radians.  The  firmware expact angles in degrees, so a conversion is made for gcodes starting with G. Not sure why this was done like this, but Will have too look into how this might effect advanced gcodes used in homing.   Nometheless, is the action contains the _raw attribute, we pass it without conversion. Actions used by poses should not use "_raw" or that would get serialized. TODO: rework action serialization while maintaining file format compatibility.
                if not raw and g_code[0] == 'G' and arg[0] in 'PT':  
                    value = rad_to_dd(value)

                args[i] = (arg[0], f'{value}')

    g_cmd = ''.join(chain.from_iterable(args))
    
    #hack for overiding rad to dd conversion in sending PT
    if g_code == 'M92':
        g_code = 'G92'

    return f'{dest}{g_code}{g_cmd}'
