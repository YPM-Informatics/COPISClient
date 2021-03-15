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

import logging
import os
import time
from ctypes import *

from canon.EDSDKLib import *

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


def connect(index: int = 0) -> bool:
    """Connect to camera at index, and init it for capturing images.

    Args:
        index: Defaults to 0.

    Returns:
        True if successful, False otherwise.
    """
    global running, _camref, _camindex

    _update_camera_list()

    # already connected
    if running and index == _camindex:
        _console.print(f'Already connected to camera {_camindex}.')
        return True

    # disconnect from previously connected camera
    if running:
        disconnect()

    if num_cams == 0:
        _console.print('No cameras detected.')
        return False

    # invalid index
    if index < 0 or index >= num_cams:
        _console.print(f'Invalid camera index: {index}.')
        return False


    running = True

    _camindex = index
    _camref = _edsdk.EdsGetChildAtIndex(_camlist, _camindex)
    _console.print(f'Connected to camera {_camindex}.')

    _edsdk.EdsOpenSession(_camref)
    _edsdk.EdsSetPropertyData(_camref, _edsdk.PropID_SaveTo, 0, 4, EdsSaveTo.Host.value)
    _edsdk.EdsSetCapacity(_camref, EdsCapacity(10000000, 512, 1))

    # set handlers
    _edsdk.EdsSetObjectEventHandler(_camref, _edsdk.ObjectEvent_All, object_handler, None)
    _edsdk.EdsSetPropertyEventHandler(_camref, _edsdk.PropertyEvent_All, property_handler, _camref)
    _edsdk.EdsSetCameraStateEventHandler(_camref, _edsdk.StateEvent_All, state_handler, _camref)

    _edsdk.EdsSetPropertyData(_camref, _edsdk.PropID_Evf_OutputDevice, 0, sizeof(c_uint), _edsdk.EvfOutputDevice_TFT)
    return True


def disconnect() -> bool:
    """Disconnect from camera.

    Returns:
        True if successful, False otherwise.
    """
    global running, _camref, _camindex

    if not running:
        _console.print('No cameras currently connected.')
        return False

    _edsdk.EdsCloseSession(_camref)
    _console.print(f'Disconnected from camera {_camindex}.')

    running = False
    _camref = None
    _camindex = -1

    return True


def take_picture() -> bool:
    """Take picture on connected camera.

    Returns:
        True if successful, False otherwise.
    """
    if not running:
        _console.print('No cameras currently connected.')
        return False

    try:
        global waiting_for_image
        waiting_for_image = True

        _edsdk.EdsSendCommand(_camref, _edsdk.CameraCommand_PressShutterButton,
            EdsShutterButton.CameraCommand_ShutterButton_Completely.value)

        _edsdk.EdsSendCommand(_camref, _edsdk.CameraCommand_PressShutterButton,
            EdsShutterButton.CameraCommand_ShutterButton_OFF.value)

        # while waiting_for_image:
        #     pythoncom.PumpWaitingMessages()

        return True

    except Exception as e:
        _console.print(f'An exception occurred while taking a photo with camera {_camindex}: {e.args[0]}')
        return False


def step_focus() -> bool:
    """TODO

    Returns:
        True if successful, False otherwise.
    """
    return False


def start_liveview():
    """TODO"""
    return


def download_evf_data():
    """TODO"""
    return


def end_liveview():
    """TODO"""
    return


def _update_camera_list():
    """Update camera list and camera count."""
    global _camlist, num_cams

    _camlist = _edsdk.EdsGetCameraList()
    num_cams = _edsdk.EdsGetChildCount(_camlist)


def terminate():
    """Terminate EDSDK."""
    try:
        global running

        _edsdk.EdsTerminateSDK()
        running = False

    except Exception as e:
        _console.print(f'An exception occurred while terminating Canon API: {e.args[0]}')


def _generate_file_name():
    """Sets the filename for an image."""
    global image_filename, image_folder, image_prefix

    now = datetime.datetime.now().isoformat()[:-7].replace(':', '-')
    image_filename = os.path.abspath(f'./{image_prefix}_{now}.jpg')


def _download_image(image) -> None:
    """Download image from camera buffer to host computer.

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
    """
    if event == _edsdk.ObjectEvent_DirItemRequestTransfer:
        _download_image(object)
    return 0
object_handler = ObjectHandlerType(_handle_object)


PropertyHandlerType = WINFUNCTYPE(c_int, c_int, c_int, c_int, c_void_p)
def _handle_property(event, property, param, context):
    """Handles the group of events where notifications are issued regarding
    changes in the properties of a camera.
    """
    return 0
property_handler = PropertyHandlerType(_handle_property)


StateHandlerType = WINFUNCTYPE(c_int, c_int, c_int, c_void_p)
def _handle_state(event, state, context):
    """Handles the group of events where notifications are issued regarding
    changes in the state of a camera, such as activation of a shut-down timer.
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
