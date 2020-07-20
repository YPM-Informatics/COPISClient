#!/usr/bin/env python3
"""Visualizer panel. Creates a Canvas3D OpenGL canvas."""

import util

import wx
from components.canvas3d import Canvas3D


class VisualizerPanel(wx.Panel):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        style = style | wx.NO_FULL_REPAINT_ON_RESIZE
        super().__init__(parent, id, pos, size, style)

        self.parent = parent
        self.canvas = Canvas3D(
            self,
            build_dimensions=[400, 400, 400, 200, 200, 200],
            axes=True,
            every=100,
            subdivisions=10)
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

    def set_dirty(self):
        self.canvas.set_dirty()

    def on_clear_cameras(self):
        return self.canvas.on_clear_cameras()

    def get_camera_objects(self):
        return self.canvas.get_camera_objects()

    def add_camera(self, id=-1):
        return self.canvas.add_camera(id)

    def get_camera_by_id(self, id):
        return self.canvas.get_camera_by_id(id)
