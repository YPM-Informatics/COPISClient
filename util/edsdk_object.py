# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

import os
import time
from ctypes import *

from util.Canon.EDSDKLib import *

_edsdk = None
_console = None
_camlist = None
_camref = None
_camindex = -1
running = False

num_cams = 0

waiting_for_image = False
image_filename = None
image_folder = ''
image_prefix = 'COPIS'
image_index = None


def initialize(console):
    if running:
        return

    global _edsdk, _console

    _console = console

    try:
        _edsdk = EDSDK()
        _edsdk.EdsInitializeSDK()
        _update_camera_list()

    except Exception as e:
        _console.print(f'An exception occurred while initializing Canon API: {e.args[0]}')


def connect(index: int = 0):
    """Connect to camera at index, and init it for capturing images.

    Args:
        index: Defaults to 0.
    """
    global running, _camref, _camindex

    _update_camera_list()

    if index >= num_cams:
        return

    if running:
        disconnect()

    running = True

    _camindex = index
    _camref = _edsdk.EdsGetChildAtIndex(_camlist, _camindex)
    _edsdk.EdsOpenSession(_camref)
    _edsdk.EdsSetPropertyData(_camref, _edsdk.PropID_SaveTo, 0, 4, EdsSaveTo.Host.value)
    _edsdk.EdsSetCapacity(_camref, EdsCapacity(10000000, 512, 1))

    # set handlers
    _edsdk.EdsSetObjectEventHandler(_camref, _edsdk.ObjectEvent_All, object_handler, None)
    _edsdk.EdsSetPropertyEventHandler(_camref, _edsdk.PropertyEvent_All, property_handler, _camref)
    _edsdk.EdsSetCameraStateEventHandler(_camref, _edsdk.StateEvent_All, state_handler, _camref)

    _edsdk.EdsSetPropertyData(_camref, _edsdk.PropID_Evf_OutputDevice, 0, sizeof(c_uint), _edsdk.EvfOutputDevice_TFT)


def disconnect():
    global running, _camref, _camindex

    if not running:
        return

    _edsdk.EdsCloseSession(_camref)

    running = False
    _camref = None
    _camindex = -1


def take_picture():
    if not running:
        return

    try:
        global waiting_for_image
        waiting_for_image = True
        _edsdk.EdsSendCommand(_camref, 0, 0)

        # while waiting_for_image:
        #     pythoncom.PumpWaitingMessages()

    except Exception as e:
        _console.print(f'An exception occurred while taking a photo with camera {str(_camref)}: {e.args[0]}')


def step_focus():
    return


def start_evf():
    return


def download_evf():
    return


def end_evf():
    return


def get_camera_count():
    return num_cams


def _update_camera_list():
    global _camlist, num_cams
    _camlist = _edsdk.EdsGetCameraList()
    num_cams = _edsdk.EdsGetChildCount(_camlist)


def terminate():
    try:
        global running

        _edsdk.EdsTerminateSDK()
        running = False

    except Exception as e:
        _console.print(f'An exception occurred while terminating Canon API: {e.args[0]}')


def _generate_file_name():
    """Sets filename for an image with date and file extension."""
    global image_filename, image_folder, image_prefix

    now = datetime.datetime.now().isoformat()[:-7].replace(':', '-')
    image_filename = os.path.abspath(f'./{image_prefix}_{now}.jpg')


def _download_image(image) -> None:
    """Using EDSDK, get the location of the image in camera, create the -file
    stream that processes transfer image from camera to PC, and download image.

    Args:
        image: Pointer to the image.
    """
    try:
        _generate_file_name()

        dir_info = _edsdk.EdsGetDirectoryItemInfo(image)
        stream = _edsdk.EdsCreateFileStream(image_filename, 1, 2)

        _edsdk.EdsDownload(image, dir_info.size, stream)
        _edsdk.EdsDownloadComplete(image)
        _edsdk.EdsRelease(stream)

        global waiting_for_image
        waiting_for_image = False

        _console.print(f'Image saved at {image_filename}.')

    except Exception as e:
        _console.print(f'An exception occurred while downloading an image: {e.args[0]}')


ObjectHandlerType = WINFUNCTYPE(c_int, c_int, c_void_p, c_void_p)
def _handle_object(event, object, context):
    """Handles the group of events where request notifications are issued to
    create, delete or transfer image data stored in a camera or image files on
    the memory card.

    Args:
        event: EdsObjectEvent event type supplemented
        object: EdsBaseRef reference to object created by the event
        context: EdsVoid any data needed for the application
    """
    if event == _edsdk.ObjectEvent_DirItemRequestTransfer:
        _download_image(object)
    return 0
object_handler = ObjectHandlerType(_handle_object)


PropertyHandlerType = WINFUNCTYPE(c_int, c_int, c_int, c_int, c_void_p)
def _handle_property(event, property, param, context):
    """Handles the group of events where notifications are issued regarding
    changes in the properties of a camera.

    Args:
        event: EdsPropertyEvent event type supplemented
        property: EdsPropertyID property ID created by the event
        param: EdsUInt32 used to identify information created by the event for
            custom function properties or other properties that have multiple
            items of information
        context: EdsVoid any data needed for the application
    """
    return 0
property_handler = PropertyHandlerType(_handle_property)


StateHandlerType = WINFUNCTYPE(c_int, c_int, c_int, c_void_p)
def _handle_state(event, state, context):
    """Handles the group of events where notifications are issued regarding
    changes in the state of a camera, such as activation of a shut-down timer.

    Args:
        event: EdsStateEvent event type supplemented
        state: EdsUInt32 pointer to the event data
        context: EdsVoid any data needed for the application
    """
    if event == _edsdk.StateEvent_WillSoonShutDown:
        try:
            _edsdk.EdsSendCommand(context, 1, 0)
        except Exception as e:
            _console.print(f'An exception occurred while handling the state change event: {e.args[0]}')
    return 0
state_handler = StateHandlerType(_handle_state)

class EvfDataSet(Structure):
    _fields_ = [
        ('stream', c_void_p),
        ('zoom', c_uint),
        ('zoomRect', EdsRect),
        ('imagePosition', EdsPoint),
        ('sizeJpgLarge', EdsSize),
    ]
