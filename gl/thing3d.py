"""Thing3D class."""

import math
import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from enums import ViewCubePos, ViewCubeSize
from utils import timing


class Thing3D():
    def __init__(self, parent):
        self._parent = parent
        self._volumes = None

        self._thing_id = None

    def render(self):
        return

    def render_for_picking(self):
        return
