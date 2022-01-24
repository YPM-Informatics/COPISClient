import copy

from enum import Enum
from json import JSONEncoder


def _enum_as_dict(enum_o):
    if isinstance(enum_o, Enum):
        return {'__enum__': str(enum_o)}
    return enum_o.__dict__


class ActionEncoder(JSONEncoder):
    """JSON encoder for the Action class."""
    def default(self, o):
        a_type = copy.deepcopy(o.atype)
        o.atype = None

        a_dict = o.__dict__
        a_dict.update({'atype': _enum_as_dict(a_type)})

        return a_dict


class EnumEncoder(JSONEncoder):
    """JSON encode for enums."""
    def default(self, o):
        return _enum_as_dict(o)
