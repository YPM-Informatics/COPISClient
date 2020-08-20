"""GLThing class."""

import math
from abc import ABC, abstractmethod

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

import glm
from utils import timing


class GLThing(ABC):
    """TODO
    """

    def __init__(self, parent) -> None:
        super().__init__()
        self._mgr = parent
        self._volumes = None

        self._hovered = False
        self._selected = False
        self._initialized = False

    @abstractmethod
    def create_vao(self) -> None:
        """Bind VAOs to define vertex data."""
        pass

    def init(self) -> None:
        """Initialize for rendering."""
        if self._initialized:
            return True

        self.create_vao()

        self._initialized = True
        return True

    @abstractmethod
    def render(self) -> None:
        """Render to screen."""
        pass

    @abstractmethod
    def render_for_picking(self) -> None:
        """Render for picking pass. Usually disables any sort of multisampling
        or antialiasing which may affect pixel values."""
        pass

    @property
    def hovered(self) -> bool:
        return self._hovered

    @hovered.setter
    def hovered(self, value: bool) -> None:
        self._hovered = value

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool) -> None:
        self._selected = value
