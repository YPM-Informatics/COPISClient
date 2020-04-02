from Canon.EDSDKLib import *
import time
from ctypes import *
from enum import *

edsdk = EDSDK()
edsdk.EdsInitializeSDK()

##############################################################################
#  Function:   generateFileName
#
#  Description:
#      Generates the image file name consists of date and file extension
#
#  Parameters:
#       In:    None
#
#  Returns:    file_name - image file name
##############################################################################
def generateFileName():
    now = datetime.datetime.now()
    file_name = "IMG_" + now.isoformat()[:-7].replace(':', '-') + ".jpg"
    return file_name


##############################################################################
#  Function:   downloadImage
#
#  Description:
#      Using EDSDK, get the location of the image in camera, create the file
#      stream that processes transfer image from camera to PC, and download
#      the image
#
#  Parameters:
#       In:    image - the image reference
#
#  Returns:    None
##############################################################################
def downloadImage(image):
    dir_info = edsdk.EdsGetDirectoryItemInfo(image)
    #self.panelRight.resultBox.AppendText("Picture is taken.")
    file_name = generateFileName()
    stream = edsdk.EdsCreateFileStream(file_name, 1, 2)
    edsdk.EdsDownload(image, dir_info.size, stream)
    edsdk.EdsDownloadComplete(image)
    #self.panelRight.resultBox.AppendText("Image is saved as " + file_name)
    edsdk.EdsRelease(stream) 


ObjectHandlerType = WINFUNCTYPE(c_int,c_int,c_void_p,c_void_p)
##############################################################################
#  Function:   handleObject
#
#  Description:
#      Handles the group of events where request notifications are issued to
#      create, delete or transfer image data stored in a camera or image files
#      on the memory card
#
#  Parameters:
#       In:    event - EdsObjectEvent event type supplemented
#              object - EdsBaseRef reference to object created by the event
#              context - EdsVoid any data needed for the application
#
#  Returns:    None
##############################################################################
def handleObject(event, object, context):
    if event == edsdk.ObjectEvent_DirItemRequestTransfer:
        downloadImage(object)
    return 0
object_handler = ObjectHandlerType(handleObject)


StateHandlerType = WINFUNCTYPE(c_int,c_int,c_int,c_void_p)
##############################################################################
#  Function:   handleState
#
#  Description:
#      Handles the group of events where notifications are issued regarding
#      changes in the state of a camera, such as activation of a shut-down
#      timer
#
#  Parameters:
#       In:    event - EdsStateEvent event type supplemented
#              state - EdsUInt32 pointer to the event data
#              context - EdsVoid any data needed for the application
#
#  Returns:    None
##############################################################################
def handleState(event, state, context):
    if event == edsdk.StateEvent_WillSoonShutDown:
        #self.panelRight.resultBox.AppendText("Camera is about to shut off.")
        edsdk.EdsSendCommand(context, 1, 0)
    return 0
state_handler = StateHandlerType(handleState)


PropertyHandlerType = WINFUNCTYPE(c_int,c_int,c_int,c_int,c_void_p)
##############################################################################
#  Function:   handleProperty
#
#  Description:
#      Handles the group of events where notifications are issued regarding
#      changes in the properties of a camera
#
#  Parameters:
#       In:    event - EdsPropertyEvent event type supplemented
#              property - EdsPropertyID property ID created by the event
#              param - EdsUInt32 used to identify information created by the
#                      event for custom function properties or other 
#                      properties that have multiple items of information
#              context - EdsVoid any data needed for the application
#
#  Returns:    None
##############################################################################
def handleProperty(event, property, param, context):
    return 0
property_handler = PropertyHandlerType(handleProperty)


class Camera:
    def __init__(self, id, camref):
        self.camref = camref
        self.id = id   
        self.device = c_void_p()
        
        ## set the handlers
        edsdk.EdsSetObjectEventHandler(self.camref, edsdk.ObjectEvent_All, object_handler, None)
        edsdk.EdsSetPropertyEventHandler(self.camref, edsdk.PropertyEvent_All, property_handler, None)
        edsdk.EdsSetCameraStateEventHandler(self.camref, edsdk.StateEvent_All, state_handler, self.camref)
        
        ## connect to the camera
        edsdk.EdsOpenSession(self.camref)
        edsdk.EdsSetPropertyData(self.camref, edsdk.PropID_SaveTo, 0, 4, EdsSaveTo.Host.value)
        edsdk.EdsSetCapacity(self.camref, EdsCapacity(10000000,512,1))

    def __del__(self):
        if self.camref is not None:
            edsdk.EdsCloseSession(self.camref)
            edsdk.EdsRelease(self.camref)

    def shoot(self):
        global Wait_For_Image
        Wait_For_Image = True

        edsdk.EdsSendCommand(self.camref, 0, 0)

    def getEvfData(self):
        ## start live view
        self.device = edsdk.EvfOutputDevice_PC
        self.device = edsdk.EdsSetPropertyData(self.camref, edsdk.PropID_Evf_OutputDevice, 0, sizeof(c_uint), self.device)

        evfStream = edsdk.EdsCreateMemoryStream(0)
        evfImageRef = edsdk.EdsCreateEvfImageRef(evfStream)
        edsdk.EdsDownloadEvfImage(self.camref, evfImageRef)

        dataset = EvfDataSet()
        dataset.stream = evfStream
        dataset.zoom = edsdk.EdsGetPropertyData(evfImageRef, edsdk.PropID_Evf_Zoom, 0, sizeof(c_uint), dataset.zoom)
        dataset.imagePosition = edsdk.EdsGetPropertyData(evfImageRef, edsdk.PropID_Evf_ImagePosition, 0, sizeof(EdsPoint), dataset.imagePosition)
        dataset.zoomRect = edsdk.EdsGetPropertyData(evfImageRef, edsdk.PropID_Evf_ZoomRect, 0, sizeof(EdsRect), dataset.zoomRect)
        dataset.sizeJpgLarge = edsdk.EdsGetPropertyData(evfImageRef, edsdk.PropID_Evf_CoordinateSystem, 0, sizeof(EdsSize), dataset.sizeJpgLarge)

        edsdk.EdsRelease(evfStream)
        edsdk.EdsRelease(evfImageRef)
    
class CameraList:
    def __init__(self):
        self.list = c_void_p(None)
        self.list = edsdk.EdsGetCameraList()
        self.cam_model_list = []
        self.selected_camera = None

        ## transfer EDSDK camera object to custom camera object
        for i in range(self.get_count()):
            self.cam_model_list.append(Camera(i, edsdk.EdsGetChildAtIndex(self.list, i)))

    def get_count(self):
        return edsdk.EdsGetChildCount(self.list)

    def get_camera_by_index(self, index):
        return cam_model_list[index]

    def get_camera_by_id(self, id):
        if id not in range(len(self.cam_model_list)):
            for model in self.cam_model_list:
                if model.id == id:
                    return model
        else:
            index = id
            while index in range(len(self.cam_model_list)):
                model_index = self.cam_model_list[index]
                if model_index.id == id:
                    return model_index
                elif model_index.id > id:
                    index -= 1
                else:
                    index += 1
        return None

    def set_selected_cam_by_id(self, id):
        self.selected_camera = self.get_camera_by_id(id)

class EvfDataSet(Structure):
    _fields_: [('stream', c_void_p),
               ('zoom', c_uint),
               ('zoomRect', EdsRect),
               ('imagePosition', EdsPoint),
               ('sizeJpgLarge', EdsSize)]