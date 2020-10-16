"""ActionVis class."""


from collections import defaultdict
from typing import Tuple, Union

import glm
import wx
from enums import ActionType
from OpenGL.GL import *
from OpenGL.GLU import *
from utils import xyzpt_to_mat4, point5_to_mat4


class GLActionVis:
    """Text

    Args:

    Attributes:
    """

    colors = [(1,0,0), (0,1,0), (0,0,1), (1,1,0), (1,0,1), (0,1,1)]

    def __init__(self, parent):
        self.parent = parent
        self._initialized = False

        self._lines = defaultdict(list)
        self._points = defaultdict(list)

    # def create(self) -> None:


    #     return

    def update(self, actions) -> None:
        core = wx.GetApp().core

        # add initial points
        for device in core.devices:
            self._points[device.device_id].append(point5_to_mat4(device.position))

        for action in core.actions:
            if action.atype in (ActionType.G0, ActionType.G1):
                if action.argc == 5:
                    self._lines[action.device].append(xyzpt_to_mat4(*action.args))
            if action.atype in (ActionType.C0,):
                if action.device in self._lines.keys():
                    self._points[action.device].append(self._lines[action.device][-1])
                else:
                    self._points[action.device].append(self._points[action.device][0])

        print(self._lines, self._points)


    def init(self) -> bool:
        if self._initialized:
            return True

        self.create()

        self._initialized = True
        return True

    def render(self) -> None:
        if not self.init():
            return

    def render_for_picking(self) -> None:
        if not self.init():
            return
