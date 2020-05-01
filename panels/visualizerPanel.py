import wx
from components.canvas import Canvas, Camera3D
import random
import util

class VisualizerPanel(wx.Panel):
    def __init__(self, parent):
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

    def onDrawCamera(self, id):
        x = float(random.randrange(-100, 100)) / 100
        y = float(random.randrange(-100, 100)) / 100
        z = float(random.randrange(-100, 100)) / 100
        b = random.randrange(0, 360, 5)
        c = random.randrange(0, 360, 5)

        cam_3d = Camera3D(id, x, y, z, b, c)
        self.canvas.camera_objects.append(cam_3d)
        cam_3d.onDraw()
        self.canvas.SwapBuffers()

    def onClearCameras(self):
        self.canvas.camera_objects = []
        self.canvas.SwapBuffers()
 