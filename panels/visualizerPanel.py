#!/usr/bin/env python3
"""TODO: Fill in docstring"""

import util
import random

import wx
from components.camview import Canvas, Camera3D


class VisualizerPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(VisualizerPanel, self).__init__(parent)
        self.parent = parent
        self.canvas = Canvas(self)
        self.InitPanel()

    def InitPanel(self):
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

    def onDrawCamera(self, id=-1):
        x = float(random.randrange(-100, 100)) / 100
        y = float(random.randrange(-100, 100)) / 100
        z = float(random.randrange(-100, 100)) / 100
        b = random.randrange(0, 360, 5)
        c = random.randrange(0, 360, 5)

        if id == -1:
            id = self.generateCamId()

        cam_3d = Camera3D(id, x, y, z, b, c)
        self.canvas.camera_objects.append(cam_3d)
        self.canvas.OnDraw()

        return cam_3d

    def onClearCameras(self):
        self.canvas.camera_objects = []
        self.canvas.Refresh()
        self.canvas.SwapBuffers()

    def getCamById(self, id):
        for cam in self.canvas.camera_objects:
            if cam.id == id:
                return cam
        return None

    def generateCamId(self):
        self.canvas.camera_objects.sort(key=lambda x: x.id)
        if self.canvas.camera_objects:
            return self.canvas.camera_objects[-1].id + 1
        return 0
