from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import random
from Canon.EDSDKLib import *
import sys
import time
import wx

class Camera():
    def __init__(self, id, camref):
        self.mode = 'normal'
        self.camref = camref
        self.id = id

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
