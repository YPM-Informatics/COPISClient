"""GLThing class."""

import math
import numpy as np

import glm
from OpenGL.GL import *
from OpenGL.GLU import *

from utils import timing
from abc import ABC, abstractmethod


class GLThing(ABC):
    def __init__(self, parent):
        super().__init__()
        self._mgr = parent
        self._volumes = None

        self._vao = None
        self._vao_picking = None

        self._hovered = False
        self._selected = False
        self._initialized = False

    @abstractmethod
    def create_vao(self):
        """Bind VAOs to define vertex data."""
        pass

    def init(self):
        """Initialize for rendering."""
        if self._initialized:
            return True

        self.create_vao()

        self._initialized = True
        return True

    @abstractmethod
    def render(self):
        """Render to screen."""
        pass

    @abstractmethod
    def render_for_picking(self):
        """Render for picking pass. Usually disables any sort of multisampling
        or antialiasing which may affect pixel values."""
        pass

    @property
    def hovered(self):
        return self._hovered

    @hovered.setter
    def hovered(self, value):
        self._hovered = value

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value
