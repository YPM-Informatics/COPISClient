#!/usr/bin/env python3
"""TODO: Fill in docstring"""

import util

import wx
from components.canvas3d import Canvas3D


class VisualizerPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(VisualizerPanel, self).__init__(parent)
        self.parent = parent
        self.canvas = Canvas3D(self)
        self.init_panel()

    def init_panel(self):
        ## LAYOUT

        #################################################################################################
        ##                                                                                             ##
        ## hbox  ------------------------------------------------------------------------------------- ##
        ## Right | --------------------------------------------------------------------------------- | ##
        ##       | |                                                                               | | ##
        ##       | |                                                                               | | ##
        ##       | |                                                                               | | ##
        ##       | |                                 C A N V A S                                   | | ##
        ##       | |                                                                               | | ##
        ##       | |                                                                               | | ##
        ##       | |                                                                               | | ##
        ##       | |                                                                               | | ##
        ##       | --------------------------------------------------------------------------------- | ##
        ##       ------------------------------------------------------------------------------------- ##
        ##                                                                                             ##
        #################################################################################################
        hboxRight = wx.BoxSizer()
        self.canvas.SetMinSize((200, 200))
        hboxRight.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizerAndFit(hboxRight)

    def on_clear_cameras(self):
        return False if self.canvas is None else self.canvas.clear_camera_objects()

    def get_camera_objects(self):
        return False if self.canvas is None else self.canvas.get_camera_objects()

    def add_camera(self, id=-1):
        return None if self.canvas is None else self.canvas.add_camera(id)

    def get_cam_by_id(self, id):
        return None if self.canvas is None else self.canvas.get_camera_by_id(id)
