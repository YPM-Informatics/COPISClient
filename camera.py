from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import random
from enums import Axis
from Canon.EDSDKLib import *
import sys
import time
import wx

class Camera():
    def __init__(self, x, y, z, b, c, camref):
        ## 3D camera object part
        try:
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)
            self.b = float(b)
            self.c = float(c)
        except:
            self.setDialog('Values for axis should be numbers.')
        self.start = (self.x, self.y, self.z, self.b, self.c)

        self.angle = 0
        self.rotationVector = []
    
        self.mode = 'normal'
        
        self.camref = camref



    

    def downloadImage(self, image):
        dir_info = self.edsdk.EdsGetDirectoryItemInfo(image)
        self.panelRight.resultBox.AppendText("Picture is taken.")
        file_name = self.generateFileName()
        stream = self.edsdk.EdsCreateFileStream(file_name, 1, 2)
        self.edsdk.EdsDownload(image, dir_info.size, stream)
        self.edsdk.EdsDownloadComplete(image)
        self.panelRight.resultBox.AppendText("Image is saved as " + file_name)
        self.edsdk.EdsRelease(stream)

    def __del__(self):
        if self.camref is not None:
            self.edsdk.EdsCloseSession(self.camref)
            self.edsdk.EdsRelease(self.camref)

    def shoot(self, file_name = None):
        if file_name is None:
            file_name = self.generateFileName()

        self.edsdk.EdsSendCommand(self.camref, 0, 0)
        return file_name

    def generateFileName(self):
        now = datetime.datetime.now()
        file_name = "IMG_" + now.isoformat()[:-7].replace(':', '-') + ".jpg"
        return file_name
