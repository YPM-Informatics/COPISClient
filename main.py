#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import wx
import sys
from mainFrame import MainFrame
from Canon.EDSDKLib import *
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
    edsdk = EDSDK()
    edsdk.EdsInitializeSDK()

    ## detect cameras
    cameraList = edsdk.EdsGetCameraList()
    camCount = edsdk.EdsGetChildCount(cameraList)

    camera_models = []
    selected_cam = None

    for i in range(camCount):
        x = float(random.randrange(-100, 100)) / 100
        y = float(random.randrange(-100, 100)) / 100
        z = float(random.randrange(-100, 100)) / 100
        b = random.randrange(0, 360, 5)
        c = random.randrange(0, 360, 5)
        
        camera = Camera(x, y, z, b, c, edsdk.EdsGetChildAtIndex(cameraList, i))
        camera_models.append(camera)

    edsdk.EdsRelease(cameraList)

    selected_cam = camera_models[0]

    if camCount != 0:
        ObjectHandlerType = WINFUNCTYPE   (c_int,c_int,c_void_p,c_void_p)
        object_handler = ObjectHandlerType(handleObject)
        edsdk.EdsSetObjectEventHandler(selected_cam.camref, edsdk.ObjectEvent_All, object_handler, None)

        PropertyHandlerType = WINFUNCTYPE   (c_int,c_int,c_int,c_int,c_void_p)
        property_handler = PropertyHandlerType(handleProperty)
        edsdk.EdsSetPropertyEventHandler(selected_cam.camref, edsdk.PropertyEvent_All, property_handler, None)

        StateHandlerType = WINFUNCTYPE   (c_int,c_int,c_int,c_void_p)
        state_handler = StateHandlerType(handleState)
        edsdk.EdsSetCameraStateEventHandler(selected_cam.camref, edsdk.StateEvent_All, state_handler, selected_cam.camref)

        edsdk.EdsOpenSession(selected_cam.camref)
        edsdk.EdsSetPropertyData(selected_cam.camref, edsdk.PropID_SaveTo, 0, 4, EdsSaveTo.Host.value)
        edsdk.EdsSetCapacity(selected_cam.camref, EdsCapacity(10000000,512,1))

    app = COPISApp()
    app.MainLoop()

    for camera in camera_models:
        del camera

    edsdk.EdsTerminateSDK()

