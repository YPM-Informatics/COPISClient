#!/usr/bin/env python3
"""Path3D class."""

import math
import numpy as np
import threading

import wx
from OpenGL.GL import *
from OpenGL.GLU import *

EVT_RESULT_ID = wx.NewId()


def EVT_RESULT(win, func):
     """Define Result Event."""
     win.Connect(-1, -1, EVT_RESULT_ID, func)


class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data


class Path3DWorker(threading.Thread):
    def __init__(self, notify_window):
        super().__init__(self)
        self._notify_window = notify_window
        self._want_abort = False
        self.start()

    def run(self):
        if self._want_abort:
            wx.PostEvent(self._notify_window, ResultEvent(None))
            return
        wx.PostEvent(self._notify_window, ResultEvent(1))

    def abort(self):
        self._want_abort = True


class Path3D():
    def __init__(self, *args, **kwargs):
        self._path = None
        self._path_outline = None
        self._cameras = None

    def attach_camera(self):
        return

    def detach_camera(self, id):
        return

    def detach_all_cameras(self):
        return

    def has_path(self):
        return not self._path is None

    def add_point(self, *args):
        return
