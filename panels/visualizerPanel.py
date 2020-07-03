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

    def get_camera_objects(self):
        return False if self.canvas is None else self.canvas.get_camera_objects()

    def add_camera(self, id=-1):
        return None if self.canvas is None else self.canvas.add_camera(id)
        # x = float(random.randrange(-100, 100)) / 100
        # y = float(random.randrange(-100, 100)) / 100
        # z = float(random.randrange(-100, 100)) / 100
        # b = random.randrange(0, 360, 5)
        # c = random.randrange(0, 360, 5)

        # if id == -1:
        #     id = self.generate_cam_id()

        # cam_3d = Camera3D(id, x, y, z, b, c)
        # self.canvas.camera_objects.append(cam_3d)
        # self.canvas.set_dirty()
        # return str(cam_3d._id)

    def on_clear_cameras(self):
        return False if self.canvas is None else self.canvas.clear_camera_objects()

    def get_cam_by_id(self, id):
        return None if self.canvas is None else self.canvas.get_camera_by_id(id)
