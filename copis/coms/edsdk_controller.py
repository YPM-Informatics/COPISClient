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

"""Manages COPIS EDSDK Communications"""

import os
import datetime

from ctypes import c_int, c_uint, c_void_p, sizeof, WINFUNCTYPE
from dataclasses import dataclass
from typing import ClassVar, List
from mprop import mproperty

from canon.EDSDKLib import (
    EDSDK, EdsCapacity, EdsDeviceInfo, EdsPoint, EdsRect, EdsSaveTo,
    EdsShutterButton, EdsSize, Structure)


class EDSDKController():
    """Implement EDSDK Functionalities"""
    _object_handler = _property_handler = _state_handler = object

    def __init__(self) -> None:
        self._edsdk = None
        self._console = None
        self._is_connected = False
        self._is_waiting_for_image = False

        self._camera = CameraSettings()
        self._image = ImageSettings()

        # Locally aliasing WINFUNCTYPE is required to avoid NameError cause
        # by the use of @mproperty.
        # See: https://github.com/josiahcarlson/mprop
        self._win_func_type = WINFUNCTYPE

    def initialize(self, console) -> None:
        """Initialize the EDSDK object"""
        if self._is_connected:
            return

        self._console = console

        try:
            self._edsdk = EDSDK()
            self._edsdk.EdsInitializeSDK()
            self._update_camera_list()

        # TODO: Check everywhere messages are dispatched to the console.
        # Because it is part of the main frame and that doesn't get loaded (in client) till
        # after Core, messages dispatched in parts of Core and its descendants (like here) don't get
        # printed because the console doesn't exist yet.
        # That causes a lot of errors to get swallowed up.
        except FileNotFoundError as err:
            msg = f'An exception occurred while initializing Canon API: {err.args[0]}'
            self._console.print(msg)
            print(msg)

    def connect(self, index: int = 0) -> bool:
        """Connect to camera at index, and init it for capturing images.

        Args:
            index: Defaults to 0.

        Returns:
            True if successful, False otherwise.
        """
        self._update_camera_list()

        cam_count, cam_index, cam_items, cam_ref = self._camera

        # already connected
        if self._is_connected and index == cam_index:
            self._console.print(f'Already connected to camera {cam_index}.')
            return True

        # disconnect from previously connected camera
        if self._is_connected:
            self.disconnect()

        if cam_count == 0:
            self._console.print('No cameras detected.')
            return False

        # invalid index
        if index < 0 or index >= cam_count:
            self._console.print(f'Invalid camera index: {index}.')
            return False

        self._camera.index = index
        self._camera.ref = self._edsdk.EdsGetChildAtIndex(cam_items, index)

        *_, cam_ref = self._camera

        self._edsdk.EdsOpenSession(cam_ref)
        self._edsdk.EdsSetPropertyData(
            cam_ref, self._edsdk.PropID_SaveTo, 0, 4, EdsSaveTo.Host.value)

        self._edsdk.EdsSetCapacity(cam_ref, EdsCapacity(10000000, 512, 1))

        # set handlers
        object_prototype = self._win_func_type(c_int, c_int, c_void_p, c_void_p)
        EDSDKController._object_handler = object_prototype(self._handle_object)

        property_prototype = self._win_func_type(c_int, c_int, c_int, c_int, c_void_p)
        EDSDKController._property_handler = property_prototype(self._handle_property)

        state_prototype = self._win_func_type(c_int, c_int, c_int, c_void_p)
        EDSDKController._state_handler = state_prototype(self._handle_state)

        self._edsdk.EdsSetObjectEventHandler(
            cam_ref, self._edsdk.ObjectEvent_All, EDSDKController._object_handler, None)

        self._edsdk.EdsSetPropertyEventHandler(
            cam_ref, self._edsdk.PropertyEvent_All, EDSDKController._property_handler, cam_ref)

        self._edsdk.EdsSetCameraStateEventHandler(
            cam_ref, self._edsdk.StateEvent_All, EDSDKController._state_handler, cam_ref)

        self._edsdk.EdsSetPropertyData(cam_ref, self._edsdk.PropID_Evf_OutputDevice,
            0, sizeof(c_uint), self._edsdk.EvfOutputDevice_TFT)

        self._is_connected = True
        self._console.print(f'Connected to camera {self._camera.index}.')

        return self._is_connected

    def disconnect(self) -> bool:
        """Disconnect from camera.

        Returns:
            True if successful, False otherwise.
        """
        if not self._is_connected:
            self._console.print('No cameras currently connected.')
            return False

        self._edsdk.EdsCloseSession(self._camera.ref)
        self._console.print(f'Disconnected from camera {self._camera.index}.')

        self._camera.ref = None
        self._camera.index = -1

        self._is_connected = False

        return not self._is_connected

    def take_picture(self) -> bool:
        """Take picture on connected camera.

        Returns:
            True if successful, False otherwise.
        """
        if not self._is_connected:
            self._console.print('No cameras currently connected.')
            return False

        try:
            self._is_waiting_for_image = True

            self._edsdk.EdsSendCommand(self._camera.ref,
                self._edsdk.CameraCommand_PressShutterButton,
                EdsShutterButton.CameraCommand_ShutterButton_Completely.value)

            self._edsdk.EdsSendCommand(self._camera.ref,
                self._edsdk.CameraCommand_PressShutterButton,
                EdsShutterButton.CameraCommand_ShutterButton_OFF.value)

            # while waiting_for_image:
            #     pythoncom.PumpWaitingMessages()

            return True

        except Exception as err:
            self._console.print('An exception occurred while taking a photo with camera '
                f'{self._camera.index}: {err.args[0]}')
            return False

    def terminate(self):
        """Terminate EDSDK."""
        try:
            self.disconnect()
            self._edsdk.EdsTerminateSDK()

        except Exception as err:
            self._console.print(f'An exception occurred while terminating Canon API: {err.args[0]}')

    @property
    def camera_count(self) -> int:
        """Returns camera count"""
        return self._camera.count

    @property
    def is_waiting_for_image(self) -> bool:
        """Returns a flag indicating whether we are waiting for an image"""
        return self._is_waiting_for_image

    @property
    def is_enabled(self) -> bool:
        """Returns a flag indicating whether EDSDK is enabled"""
        return self._edsdk is not None

    @property
    def device_list(self) -> List[EdsDeviceInfo]:
        """Returns a list of descriptions of devices connected via edsdk"""
        devices = []
        self._update_camera_list()

        cam_count, cam_index, cam_items, *_ = self._camera

        for i in range(cam_count):
            ref = self._edsdk.EdsGetChildAtIndex(cam_items, i)
            info = self._edsdk.EdsGetDeviceInfo(ref)

            is_connected = self._is_connected and i == cam_index

            devices.append((info, is_connected))

        return devices

    # def step_focus(self) -> bool:
    #     """TODO

    #     Returns:
    #         True if successful, False otherwise.
    #     """
    #     return False

    # def start_liveview(self):
    #     """TODO"""
    #     return

    # def download_evf_data(self):
    #     """TODO"""
    #     return

    # def end_liveview(self):
    #     """TODO"""
    #     return

    def _update_camera_list(self):
        """Updates camera list and camera count."""
        self._camera.items = self._edsdk.EdsGetCameraList()
        self._camera.count = self._edsdk.EdsGetChildCount(self._camera.items)

    def _generate_file_name(self):
        """Sets the filename for an image."""
        now = datetime.datetime.now().isoformat()[:-7].replace(':', '-')
        self._image.filename = os.path.abspath(f'./{self._image.PREFIX}_{now}.jpg')

    def _download_image(self, image) -> None:
        """Download image from camera buffer to host computer.

        Args:
            image: Pointer to the image.
        """
        try:
            self._generate_file_name()

            dir_info = self._edsdk.EdsGetDirectoryItemInfo(image)
            stream = self._edsdk.EdsCreateFileStream(self._image.filename, 1, 2)

            self._edsdk.EdsDownload(image, dir_info.size, stream)
            self._edsdk.EdsDownloadComplete(image)
            self._edsdk.EdsRelease(stream)

            self._is_waiting_for_image = False

            self._console.print(f'Image saved at {self._image.filename}.')

        except Exception as err:
            self._console.print(f'An exception occurred while downloading an image: {err.args[0]}')

    def _handle_object(self, event, obj, _context):
        """Handles the group of events where request notifications are issued to
        create, delete or transfer image data stored in a camera or image files on
        the memory card.
        """
        if event == self._edsdk.ObjectEvent_DirItemRequestTransfer:
            self._download_image(obj)
        return 0

    def _handle_property(self, _event, _property, _parameter, _context):
        """Handles the group of events where notifications are issued regarding
        changes in the properties of a camera.
        """
        return 0

    def _handle_state(self, event, _state, context):
        """Handles the group of events where notifications are issued regarding
        changes in the state of a camera, such as activation of a shut-down timer.
        """
        if event == self._edsdk.StateEvent_WillSoonShutDown:
            try:
                self._edsdk.EdsSendCommand(context, 1, 0)
            except Exception as err:
                self._console.print(
                    f'An exception occurred while handling the state change event: {err.args[0]}')

        return 0


@dataclass
class EvfDataSet(Structure):
    """EVF data structure"""
    _fields_ = [
        ('stream', c_void_p),
        ('zoom', c_uint),
        ('zoomRect', EdsRect),
        ('imagePosition', EdsPoint),
        ('sizeJpgLarge', EdsSize),
    ]


@dataclass
class CameraSettings():
    """Data structure to hold the COPIS EDSDK camera settings"""
    def __init__(self) -> None:
        self.count = 0
        self.index = -1
        self.items = None
        self.ref = None

    def __iter__(self):
        return iter((
            self.count,
            self.index,
            self.items,
            self.ref
        ))


@dataclass
class ImageSettings():
    """Data structure to hold the COPIS EDSDK image settings"""

    PREFIX: ClassVar[str] = 'COPIS'

    def __init__(self) -> None:
        self.filename = None
        self.folder = ''
        self.index = None

    def __iter__(self):
        return iter((
            self.filename,
            self.folder,
            self.index,
        ))


_instance = EDSDKController()

connect = _instance.connect
disconnect = _instance.disconnect
initialize = _instance.initialize
take_picture = _instance.take_picture
terminate = _instance.terminate

@mproperty
def camera_count(mod) -> int:
    """Returns camera count from the module"""
    return mod._instance.camera_count

@mproperty
def is_waiting_for_image(mod) -> bool:
    """Returns a flag indicating whether we are waiting for an image; from the module"""
    return mod._instance.is_waiting_for_image

@mproperty
def is_enabled(mod) -> bool:
    """Returns a flag indicating whether EDSDK is enabled; from the module"""
    return mod._instance.is_enabled

@mproperty
def device_list(mod) -> List[EdsDeviceInfo]:
    """Returns a list of descriptions of devices connected via edsdk; from the module"""
    return mod._instance.device_list
