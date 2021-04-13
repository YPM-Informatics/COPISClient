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
from typing import ClassVar

from canon.EDSDKLib import (
    EDSDK, EdsCapacity, EdsPoint, EdsRect, EdsSaveTo,
    EdsShutterButton, EdsSize, Structure)

class LocalEDSDK():
    """Implement EDSDK Functionalities"""
    def __init__(self) -> None:
        self._edsdk = None
        self._console = None
        self._is_connected = False
        self._is_waiting_for_image = False

        self._camera = CameraSettings()
        self._image = ImageSettings()

    def initialize(self, console) -> None:
        """Initialize the EDSDK object"""
        if self._is_connected:
            return

        self._console = console

        try:
            self._edsdk = EDSDK()
            self._edsdk.EdsInitializeSDK()
            self._update_camera_list()

        except Exception as err:
            self._console.print(
                f'An exception occurred while initializing Canon API: {err.args[0]}')

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


        self._is_connected = True

        self._camera.index = index
        self._camera.ref = self._edsdk.EdsGetChildAtIndex(cam_items, index)
        self._console.print(f'Connected to camera {self._camera.index}.')

        *_, cam_ref = self._camera

        self._edsdk.EdsOpenSession(cam_ref)
        self._edsdk.EdsSetPropertyData(
            cam_ref, self._edsdk.PropID_SaveTo, 0, 4, EdsSaveTo.Host.value)

        self._edsdk.EdsSetCapacity(cam_ref, EdsCapacity(10000000, 512, 1))

        # set handlers
        object_prototype = WINFUNCTYPE(c_int, c_int, c_void_p, c_void_p)
        object_handler = object_prototype(self._handle_object)

        property_prototype = WINFUNCTYPE(c_int, c_int, c_int, c_int, c_void_p)
        property_handler = property_prototype(self._handle_property)

        state_prototype = WINFUNCTYPE(c_int, c_int, c_int, c_void_p)
        state_handler = state_prototype(self._handle_state)

        self._edsdk.EdsSetObjectEventHandler(
            cam_ref, self._edsdk.ObjectEvent_All, object_handler, None)

        self._edsdk.EdsSetPropertyEventHandler(
            cam_ref, self._edsdk.PropertyEvent_All, property_handler, cam_ref)

        self._edsdk.EdsSetCameraStateEventHandler(
            cam_ref, self._edsdk.StateEvent_All, state_handler, cam_ref)

        self._edsdk.EdsSetPropertyData(cam_ref, self._edsdk.PropID_Evf_OutputDevice,
            0, sizeof(c_uint), self._edsdk.EvfOutputDevice_TFT)

        return True

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

        self._is_connected = False
        self._camera.ref = None
        self._camera.index = -1

        return True

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

    def get_camera_count(self) -> int:
        """Return camera count"""
        return self._camera.count

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
        """Update camera list and camera count."""
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

    def _handle_object(self, evt, obj):
        """Handles the group of events where request notifications are issued to
        create, delete or transfer image data stored in a camera or image files on
        the memory card.
        """
        if evt == self._edsdk.ObjectEvent_DirItemRequestTransfer:
            self._download_image(obj)
        return 0

    def _handle_property(self, evt, prop, param, ctx):
        """Handles the group of events where notifications are issued regarding
        changes in the properties of a camera.
        """
        return 0

    def _handle_state(self, evt, state, ctx):
        """Handles the group of events where notifications are issued regarding
        changes in the state of a camera, such as activation of a shut-down timer.
        """
        if evt == self._edsdk.StateEvent_WillSoonShutDown:
            try:
                self._edsdk.EdsSendCommand(ctx, 1, 0)
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


_instance = LocalEDSDK()

connect = _instance.connect
disconnect = _instance.disconnect
get_camera_count = _instance.get_camera_count
initialize = _instance.initialize
take_picture = _instance.take_picture
terminate = _instance.terminate
