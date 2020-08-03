"""Thing3D manager class."""

import math
import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from gl.thing3d import Thing3D

from enums import ViewCubePos, ViewCubeSize
from utils import timing


class Thing3DManager():
    def __init__(self, parent):
        self._parent = parent
        self._hover_id = None
        self._things = {}

        self.init()

    def init(self):
        return

    def add_thing(self, id, thing):
        self._things[id] = thing

    @property
    def hover_id(self):
        return self._hover_id

    @hover_id.setter
    def hover_id(self, value):
        self._hover_id = value

    def render_all(self):
        if not self._things:
            return

        for thing in self._things:
            thing.render()

    def render_all_for_picking(self):
        if not self._things:
            return

        for thing in self._things:
            thing.render_for_picking()
