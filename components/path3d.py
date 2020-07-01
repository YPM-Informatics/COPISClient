#!/usr/bin/env python3

import math
import numpy as np
import threading

import wx
from OpenGL.GL import *
from OpenGL.GLU import *


class Path3D():
    def __init__(self):
        self.path = None
