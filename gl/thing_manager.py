"""GLThing manager class."""

import math
from gl.thing import GLThing

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from enums import ViewCubePos, ViewCubeSize
from utils import timing


class GLThingManager():
    id_ = 0

    def __init__(self, parent):
        self._canvas = parent

        self._things = {}
        self._hovered_id = -1
        self._selected_id = -1
        self._initialized = False

    def init(self):
        if self._initialized:
            return True

        self._initialized = True
        return True

    def render_all(self):
        if not self._things:
            return

        for thing in self._things:
            thing.render()

    def render_all_for_picking(self):
        if not self._things:
            return

        for id_, thing in self._things:
            r = (id_ & (0x0000000FF << 0)) >> 0
            g = (id_ & (0x0000000FF << 8)) >> 8
            b = (id_ & (0x0000000FF << 16)) >> 16
            a = 1.0

            glUseProgram(self.get_shader_program('color'))
            glUniform4f(2, r / 255.0, g / 255.0, b / 255.0, a)

            thing.render_for_picking()

        glBindVertexArray(0)
        glUseProgram(0)

    def add(self, thing):
        self._things[self.id_] = thing
        self.id_ += 1
        self._canvas.dirty = True

    @property
    def hovered_id(self):
        return self._hovered_id

    @hovered_id.setter
    def hovered_id(self, value):
        self._things[self._hovered_id] = False
        self._things[value].hovered = True
        self._hovered_id = value

    @property
    def selected_id(self):
        return self._selected_id

    @selected_id.setter
    def selected_id(self, value):
        self._things[self._selected_id] = False
        self._things[value].selected = True
        self._selected_id = value

    def get_shader_program(self, value):
        return self._canvas.get_shader_program(value)
