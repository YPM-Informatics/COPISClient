#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import wx
import sys
from mainFrame import MainFrame
from camera import *

APP_EXIT = 1

class COPISApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None)
        self.frame.Show()
        return True

def handleObject(event, object, context):
    if event == self.edsdk.ObjectEvent_DirItemRequestTransfer:
        self.downloadImage(object)
        
def handleProperty(event, property, param, context):
    return 0

def handleState(event, state, context):
    if event == self.edsdk.StateEvent_WillSoonShutDown:
        self.panelRight.resultBox.AppendText("Camera is about to shut off.")
        self.edsdk.EdsSendCommand(context, 1, 0)
    return 0

if __name__ == '__main__':
    app = COPISApp()
    app.MainLoop()

    #for camera in camera_models:
    #    del camera
    #
    #edsdk.EdsTerminateSDK()

