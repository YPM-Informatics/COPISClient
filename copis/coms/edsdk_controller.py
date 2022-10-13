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
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""Manage COPIS EDSDK Communications."""

import os
import datetime
import time

from ctypes import c_int, c_ubyte, c_uint, c_void_p, sizeof, WINFUNCTYPE, string_at, cast
from dataclasses import dataclass

from typing import ClassVar, List
from mprop import mproperty

from canon.EDSDKLib import (
    EDSDK, EdsAccess, EdsCapacity, EdsDeviceInfo, EdsErrorCodes, EdsEvfAf,
    EdsFileCreateDisposition, EdsSaveTo, EdsShutterButton,
    EdsStorageType, EvfDriveLens, ImageQuality)

from copis.helpers import print_error_msg, print_info_msg, get_hardware_id
from copis.classes import Device as COPIS_Device
from copis.classes.sys_db import SysDB

class EDSDKController():
    """Implement EDSDK Functionalities."""
    _object_handler = _property_handler = _state_handler = object

    def __init__(self) -> None:
        self._edsdk = None
        self._console = None
        self._is_connected = False
        self._is_waiting_for_image = False
        self._print_error_msg = print_error_msg
        self._print_info_msg = print_info_msg
        self._string_at = string_at
        self._ctypes_cast = cast
        self._get_hardware_id = get_hardware_id

        self._camera_settings = CameraSettings()  #this should be replaced with device
        self._image_settings = ImageSettings()    #this should be replaced with device
        self._current_copis_device = None
        self._evf_image_ref = None
        self._evf_stream = None
        self._db_attached = False
        self._img_buffer_length = 1 #number of images that are expected to be buffered in camera when shutter is released via edsdk if saveto pc is enabled
        self._img_buffer_counter = 0 #number of images that have been downloaded from the camera's buffer
        # Locally aliasing WINFUNCTYPE is required to avoid NameError cause
        # by the use of @mproperty.
        # See: https://github.com/josiahcarlson/mprop
        self._win_func_type = WINFUNCTYPE

    @property
    def camera_count(self) -> int:
        """Returns camera count."""
        return self._camera_settings.count

    @property
    def is_connected(self) -> int:
        """Returns a flag indicating whether a device is connected."""
        return self._is_connected

    @property
    def is_waiting_for_image(self) -> bool:
        """Returns a flag indicating whether we are waiting for an image."""
        return self._is_waiting_for_image

    @property
    def is_enabled(self) -> bool:
        """Returns a flag indicating whether EDSDK is enabled."""
        return self._edsdk is not None

    @property
    def device_list(self) -> List[EdsDeviceInfo]:
        """Returns a list of descriptions of devices connected via edsdk."""
        self._update_camera_list()
        devices = []
        infos = self._get_device_info_list()

        for info in infos:
            h_id = self._get_hardware_id(info.szPortName.decode("utf-8"))
            connected = self._is_connected and h_id == self._camera_settings.hardware_id
            devices.append((info, connected))

        return devices

    def _get_prop_data(self, ref, prop_id, param, prop):
        param_info = self._edsdk.EdsGetPropertySize(ref, prop_id, param)
        self._edsdk.EdsGetPropertyData(ref, prop_id, param, param_info['size'], prop)

    def _get_device_info_list(self):
        infos = []

        count = self._camera_settings.count
        items = self._camera_settings.items

        for i in range(count):
            ref = self._edsdk.EdsGetChildAtIndex(items, i)
            info = self._edsdk.EdsGetDeviceInfo(ref)
            infos.append(info)
        return infos

    def _get_camera_info(self, hardware_id):
        def comparer(c_info):
            h_id = self._get_hardware_id(
                c_info.szPortName.decode("utf-8")).upper()

            return h_id == hardware_id.upper()

        return next(filter(comparer, self._get_device_info_list()), None)

    def _get_camera_ref(self, hardware_id):
        info = self._get_camera_info(hardware_id)
        cam_index = -1

        for i, item in enumerate(self._get_device_info_list()):
            if info.szPortName == item.szPortName:
                cam_index = i
                break

        return self._edsdk.EdsGetChildAtIndex(self._camera_settings.items, cam_index)

    def _update_camera_list(self):
        """Update camera list and camera count."""
        self._camera_settings.items = self._edsdk.EdsGetCameraList()
        self._camera_settings.count = self._edsdk.EdsGetChildCount(self._camera_settings.items)

    def _generate_file_name(self, ext:str):
        """Set the filename for an image.
            TODO - need to finalize what format of file name should look like.
            currently is adds a timestamp, 
        """
        if self._img_buffer_counter >= 1: #ensure consistent base name across multiple formats
            self._image_settings.filename = f'{os.path.splitext(self._image_settings.filename)[0]}.{ext}'
        else:
            now = datetime.datetime.now().isoformat()[:-7].replace(':', '-')
            self._image_settings.filename = (f'{self._image_settings.PREFIX}_{now}.{ext}')
            self._image_settings.filename = os.path.join(self._current_copis_device.edsdk_save_to_path,self._image_settings.filename)

    def _download_image(self, image) -> None:
        """Download image from camera buffer to host computer.

        Args:
            image: Pointer to the image.
        """
        self._is_waiting_for_image = True
        try:
            img_ref = c_void_p(image)
            dir_info = self._edsdk.EdsGetDirectoryItemInfo(img_ref)
            self._generate_file_name(os.path.splitext(dir_info.file_name)[1][1:])
            stream = self._edsdk.EdsCreateFileStream(self._image_settings.filename, EdsFileCreateDisposition.CreateAlways.value, EdsAccess.ReadWrite.value)
            self._edsdk.EdsDownload(img_ref, dir_info.size, stream)
            self._edsdk.EdsDownloadComplete(img_ref)
            self._edsdk.EdsRelease(stream)
            if self._db_attached:
                self._sys_db.update_pose_output(self._current_copis_device,self._image_settings.filename)
            self._img_buffer_counter +=1
            self._print_info_msg(self._console, f'Image {self._img_buffer_counter} of {self._img_buffer_length} saved at {self._image_settings.filename}')
        except Exception as err:
            _img_buffer_counter = self._img_buffer_length
            self._print_error_msg(self._console, f'An exception occurred while downloading an image: {err.args[0]}')
        finally:
            if (self._img_buffer_counter >= self._img_buffer_length):
                self._is_waiting_for_image = False
                self._current_copis_device.is_writing_eds =  False
                self._img_buffer_counter =0 #reset counter
                self.disconnect() #disconnect
               

    def _handle_object(self, event, obj, _context):
        """Handle the group of events where request notifications are issued to
        create, delete or transfer image data stored in a camera or image files on
        the memory card.
        """
        if event == self._edsdk.ObjectEvent_DirItemRequestTransfer:
            self._download_image(obj)
        return 0

    def _handle_property(self, _event, _property, _parameter, _context):
        """Handle the group of events where notifications are issued regarding
        changes in the properties of a camera.
        """

        return 0

    def _handle_state(self, event, _state, context):
        """Handle the group of events where notifications are issued regarding
        changes in the state of a camera, such as activation of a shut-down timer.
        """
        try:
            if event == self._edsdk.StateEvent_WillSoonShutDown:
                if self._is_connected and self._camera_settings.ref == context:
                    self._edsdk.EdsSendCommand(context, 1, 0)
            elif event == self._edsdk.StateEvent_Shutdown:
                self.disconnect(False)
        except Exception as err:
            self._print_error_msg(self._console, f'An exception occurred while handling the state change event: {err.args[0]}')

        return 0

    def _get_volumes(self):
        volumes = []
        count = self._edsdk.EdsGetChildCount(self._camera_settings.ref)

        for i in range(count):
            ref = self._edsdk.EdsGetChildAtIndex(self._camera_settings.ref, i)
            volumes.append(self._edsdk.EdsGetVolumeInfo(ref))

        return volumes

    def _get_volume_folders(self, volume_ref):
        folders = []
        count = self._edsdk.EdsGetChildCount(volume_ref)

        for i in range(count):
            ref = self._edsdk.EdsGetChildAtIndex(volume_ref, i)
            folders.append(self._edsdk.EdsGetDirectoryItemInfo(ref))

        return folders

    def _get_pictures(self, folder_ref):
        count = self._edsdk.EdsGetChildCount(folder_ref)
        pictures = []

        for i in range(count):
            ref = self._edsdk.EdsGetChildAtIndex(folder_ref, i)
            entry = self._edsdk.EdsGetDirectoryItemInfo(ref)

            if entry.isFolder:
                pictures.extend(self._get_pictures(ref))
            else:
                pictures.append(entry)

        return pictures

    def _download_pictures(self, destination, pic_info_list):
        for info in pic_info_list:
            filename = os.path.abspath(os.path.join(destination, info.file_name))
            stream = self._edsdk.EdsCreateFileStream(filename, EdsFileCreateDisposition.CreateAlways.value, EdsAccess.ReadWrite.value)

            self._edsdk.EdsDownload(info.ref, info.size, stream)
            self._edsdk.EdsDownloadComplete(info.ref)
            self._edsdk.EdsRelease(stream)

    def _delete_pictures(self, pic_info_list):
        for info in pic_info_list:
            self._edsdk.EdsDeleteDirectoryItem(info.ref)

    def attach_sys_db(self, sys_db : SysDB) -> bool:
        if sys_db.is_initialized:
            self._sys_db = sys_db
            self._db_attached = True
        else:
            self._db_attached = False
        return self._db_attached
            
    def initialize(self, console = None) -> None:
        """Initialize the EDSDK object."""
        if self._is_connected:
            return

        self._console = console

        try:
            self._edsdk = EDSDK()
            self._edsdk.EdsInitializeSDK()
            self._update_camera_list()

            # set handlers
            object_prototype = self._win_func_type(c_int, c_int, c_void_p, c_void_p)
            EDSDKController._object_handler = object_prototype(self._handle_object)

            property_prototype = self._win_func_type(c_int, c_int, c_int, c_int, c_void_p)
            EDSDKController._property_handler = property_prototype(self._handle_property)

            state_prototype = self._win_func_type(c_int, c_int, c_int, c_void_p)
            EDSDKController._state_handler = state_prototype(self._handle_state)

        except Exception as err:
            msg = f'An exception occurred while initializing Canon API: {err}'
            self._print_error_msg(self._console, msg)
    
    #def connect(self, hard_id: str, soft_id: int) -> bool:
    def connect(self, copis_device : COPIS_Device ) -> bool:
        """Connects to and initializes a camera at the specified IDs.

        Args:
            hard_id: Hardware ID set in the device config. It should match
                the devices identifier on the system.
            soft_id: Software ID set in the device config. This is the COPIS
                assigned device ID.

        Returns:
            True if successful, False otherwise.
        """
        hard_id = copis_device.port 
        soft_id = copis_device.device_id

        self._update_camera_list()

        cam_count, cam_hard_id, *_ = self._camera_settings

        hard_ids = [self._get_hardware_id(i.szPortName.decode("utf-8")).upper()
            for i in self._get_device_info_list()]

        # Already connected.
        if self._is_connected and hard_id.upper() == cam_hard_id.upper():
            return True

        # Disconnect from previously connected camera.
        if self._is_connected:
            self.disconnect()

        if cam_count == 0:
            self._print_error_msg(self._console, 'No cameras detected.')
            return False

        # Invalid camera identifier.
        if hard_id.upper() not in hard_ids:
            self._print_error_msg(self._console, f'Camera {soft_id} not found.')
            return False

        self._current_copis_device = copis_device
        self._camera_settings.software_id = soft_id
        self._camera_settings.hardware_id = hard_id.upper()
        self._camera_settings.ref = self._get_camera_ref(self._camera_settings.hardware_id)

        self._edsdk.EdsOpenSession(self._camera_settings.ref)
        self._edsdk.EdsSetPropertyData(self._camera_settings.ref, self._edsdk.PropID_SaveTo, 0, 4, EdsSaveTo.Host.value)
        #self._edsdk.EdsSetPropertyData(self._camera_settings.ref, self._edsdk.PropID_SaveTo, 0, 4, EdsSaveTo.Camera.value)
        self._edsdk.EdsSetCapacity(self._camera_settings.ref, EdsCapacity(10000000, 512, 1))

        self._edsdk.EdsSetObjectEventHandler(self._camera_settings.ref,self._edsdk.ObjectEvent_All, EDSDKController._object_handler, None)

        self._edsdk.EdsSetPropertyEventHandler(self._camera_settings.ref, self._edsdk.PropertyEvent_All, EDSDKController._property_handler,self._camera_settings.ref)

        self._edsdk.EdsSetCameraStateEventHandler(self._camera_settings.ref, self._edsdk.StateEvent_All, EDSDKController._state_handler, self._camera_settings.ref)

        prop_out_int = c_uint(0)
        prop_out_int = self._edsdk.EdsGetPropertyData(self._camera_settings.ref, self._edsdk.PropID_ImageQuality, 0,4, prop_out_int)
        iq = ImageQuality(prop_out_int.value)
        #RAW ONLY
        #single output image qualities
        soiq = 	(ImageQuality.EdsImageQuality_LR, ImageQuality.EdsImageQuality_MR, ImageQuality.EdsImageQuality_SR, ImageQuality.EdsImageQuality_CR,
	             ImageQuality.EdsImageQuality_LJ, ImageQuality.EdsImageQuality_M1J, ImageQuality.EdsImageQuality_M2J, ImageQuality.EdsImageQuality_SJ, 
	             ImageQuality.EdsImageQuality_LJF, ImageQuality.EdsImageQuality_LJN, ImageQuality.EdsImageQuality_MJF, ImageQuality.EdsImageQuality_MJN, ImageQuality.EdsImageQuality_SJF, ImageQuality.EdsImageQuality_SJN, ImageQuality.EdsImageQuality_S1JF, 
	             ImageQuality.EdsImageQuality_S1JN, ImageQuality.EdsImageQuality_S2JF, ImageQuality.EdsImageQuality_S3JF) 
        #should also add an overide to force a number from copis_device settings to always have a backup method in case this isn't reliable across newer cameras
        if iq in (soiq):
            self._img_buffer_length = 1
        else:
            self._img_buffer_length = 2
        

        self._is_connected = True
        self._print_info_msg(self._console, f'Connected to camera {self._camera_settings.software_id}')

        return self._is_connected

    def disconnect(self, close_session: bool=True) -> bool:
        """Disconnect from camera.

        Returns:
            True if successful, False otherwise.
        """
        if not self._is_connected:
            return True

        if close_session:
            self._edsdk.EdsCloseSession(self._camera_settings.ref)

        self._print_info_msg(self._console, f'Disconnected from camera {self._camera_settings.software_id}')

        self._camera_settings.ref = None
        self._camera_settings.software_id = -1
        self._camera_settings.hardware_id = None
        self._current_copis_device = None
        self._is_connected = False

        return not self._is_connected

    def take_picture(self, do_af: bool=True) -> bool:
        """Takes a picture on connected camera.

        Returns:
            True if successful, False otherwise.
        """
        if not self._is_connected:
            self._print_error_msg(self._console, 'No cameras currently connected.')

            return False

        try:
            self._is_waiting_for_image = True

            param = EdsShutterButton.CameraCommand_ShutterButton_Completely.value

            if not do_af:
                param = EdsShutterButton.CameraCommand_ShutterButton_Completely_NonAF.value

            self._edsdk.EdsSendCommand(self._camera_settings.ref, self._edsdk.CameraCommand_PressShutterButton, param)

            self._edsdk.EdsSendCommand(self._camera_settings.ref, self._edsdk.CameraCommand_PressShutterButton, EdsShutterButton.CameraCommand_ShutterButton_OFF.value)

            return True

        except Exception as err:
            msg = ' '.join(['An exception occurred while taking a photo with camera',
                f'{self._camera_settings.software_id}: {err.args[0]}'])

            if EdsErrorCodes.EDS_ERR_TAKE_PICTURE_AF_NG.name in err.args[0]:
                msg = f'Camera {self._camera_settings.software_id} EDSDK focus failed.'

            self._print_error_msg(self._console, msg)

            return False

    def terminate(self) -> None:
        """Terminates EDSDK."""
        try:
            self.disconnect()
            self._edsdk.EdsTerminateSDK()

        except Exception as err:
            self._print_error_msg(self._console,
                'An exception occurred while terminating Canon API: '
                f'{err.args[0]}')

    def step_focus(self, step: EvfDriveLens) -> bool:
        """Steps the camera's focus by the given value (direction and distance).

        Returns:
            True if successful, False otherwise.
        """
        if not self._is_connected:
            self._print_error_msg(self._console, 'No cameras currently connected.')

            return False

        try:
            self._edsdk.EdsSendCommand(self._camera_settings.ref,
                self._edsdk.CameraCommand_DriveLensEvf, step.value)

            return True

        except Exception as err:
            msg = ' '.join(["An exception occurred while stepping the camera's focus",
                f'{self._camera_settings.software_id}: {err.args[0]}'])

            if EdsErrorCodes.EDS_ERR_TAKE_PICTURE_AF_NG.name in err.args[0]:
                msg = f'Camera {self._camera_settings.software_id} EDSDK focus failed.'

            self._print_error_msg(self._console, msg)

            return False

    def transfer_pictures(self, destination) -> None:
        """Transfers pictures off of the camera."""
        if not self._is_connected:
            self._print_error_msg(self._console, 'No cameras currently connected.')

        volumes = self._get_volumes()
        pictures = []

        for vol in volumes:
            if vol.storage_type != EdsStorageType.Non:
                if vol.access == EdsAccess.Error:
                    self._print_error_msg(self._console,
                        'An unspecified error occurred while accessing the camera volumes.')
                    return

                if vol.access == EdsAccess.Read:
                    self._print_error_msg(self._console,
                        'Write access to the camera volumes is required.')
                    return

                folders = self._get_volume_folders(vol.ref)
                pic_folder = next(filter(lambda f: f.file_name.upper() == 'DCIM', folders), None)

                if pic_folder:
                    pictures.extend(self._get_pictures(pic_folder.ref))

        if pictures:
            count = len(pictures)

            self._download_pictures(destination, pictures)
            self._delete_pictures(pictures)

            self._print_info_msg(self._console,f'{count or "No"} picture{"s" if count != 1 else ""} transferred')
        else:
            self._print_info_msg(self._console, 'No pictures transferred')

    def evf_focus(self) -> bool:
        """Performs a live view specific auto-focus.

        Returns:
            True if successful, False otherwise.
        """
        if not self._is_connected:
            self._print_error_msg(self._console, 'No cameras currently connected.')
            return False

        try:
            self._edsdk.EdsSendCommand(self._camera_settings.ref,
                self._edsdk.CameraCommand_DoEvfAf, EdsEvfAf.CameraCommand_EvfAf_ON.value)

            time.sleep(1)

            self._edsdk.EdsSendCommand(self._camera_settings.ref,
                self._edsdk.CameraCommand_DoEvfAf, EdsEvfAf.CameraCommand_EvfAf_OFF.value)

            return True

        except Exception as err:
            msg = ' '.join(['An exception occurred while focusing with camera',
                f'{self._camera_settings.software_id}: {err.args[0]}'])

            if EdsErrorCodes.EDS_ERR_TAKE_PICTURE_AF_NG.name in err.args[0]:
                msg = f'Camera {self._camera_settings.software_id} EDSDK focus failed.'

            self._print_error_msg(self._console, msg)

            return False

    def focus(self, shutter_timeout: float=0) -> bool:
        """Focuses the camera.

        Returns:
            True if successful, False otherwise.
        """
        if not self._is_connected:
            self._print_error_msg(self._console, 'No cameras currently connected.')
            return False

        try:
            self._edsdk.EdsSendCommand(self._camera_settings.ref,
                self._edsdk.CameraCommand_PressShutterButton,
                EdsShutterButton.CameraCommand_ShutterButton_Halfway.value)

            if shutter_timeout > 0:
                time.sleep(shutter_timeout)

            self._edsdk.EdsSendCommand(self._camera_settings.ref,
                self._edsdk.CameraCommand_PressShutterButton,
                EdsShutterButton.CameraCommand_ShutterButton_OFF.value)

            return True

        except Exception as err:
            msg = ' '.join(['An exception occurred while focusing with camera',
                f'{self._camera_settings.software_id}: {err.args[0]}'])

            if EdsErrorCodes.EDS_ERR_TAKE_PICTURE_AF_NG.name in err.args[0]:
                msg = f'Camera {self._camera_settings.software_id} EDSDK focus failed.'

            self._print_error_msg(self._console, msg)

            return False

    def start_live_view(self) -> None:
        """Starts the live view for the connected camera."""

        self._edsdk.EdsSetPropertyData(
            self._camera_settings.ref, self._edsdk.PropID_Evf_OutputDevice,
            0, sizeof(c_uint), self._edsdk.EvfOutputDevice_TFT|self._edsdk.EvfOutputDevice_PC)

        self._evf_stream = self._edsdk.EdsCreateMemoryStream(sizeof(c_void_p))
        self._evf_image_ref = self._edsdk.EdsCreateEvfImageRef(self._evf_stream)

    def download_evf_data(self) -> bytearray:
        """Downloads the live view stream."""
        err = EdsErrorCodes.EDS_ERR_OBJECT_NOTREADY

        # Wait for images to start coming in.
        keep_waiting = True
        error_count = 0

        while keep_waiting and self._is_connected:
            try:
                self._edsdk.EdsDownloadEvfImage(self._camera_settings.ref, self._evf_image_ref)
                keep_waiting = False
            except Exception as err:
                if EdsErrorCodes.EDS_ERR_COMM_DISCONNECTED.name in err.args[0]:
                    keep_waiting = False
                    self.disconnect(False)
                # If camera not ready keep waiting for 5s while checking every 100ms.
                elif EdsErrorCodes.EDS_ERR_OBJECT_NOTREADY.name in err.args[0] and error_count < 50:
                    time.sleep(.1)
                    error_count += 1
                else:
                    keep_waiting = False
                    raise err

        if self._is_connected:
            img_byte_length = self._edsdk.EdsGetLength(self._evf_stream)
            image_data = (c_ubyte * img_byte_length.value)()
            p_image_data = self._edsdk.EdsGetPointer(self._evf_stream, image_data)

            arr_bytes = bytearray(self._string_at(p_image_data, img_byte_length.value))
            return arr_bytes

        return None

    def end_live_view(self) -> None:
        """Ends the live view for the connected camera."""
        self._edsdk.EdsSetPropertyData(
            self._camera_settings.ref, self._edsdk.PropID_Evf_OutputDevice, 0, sizeof(c_uint), 0)

        self._edsdk.EdsRelease(self._evf_stream)
        self._edsdk.EdsRelease(self._evf_image_ref)


@dataclass
class CameraSettings():
    """Data structure to hold the COPIS EDSDK camera settings."""
    def __init__(self) -> None:
        self.count = 0
        self.hardware_id = None
        self.software_id = -1
        self.items = None
        self.ref = None

    def __iter__(self):
        return iter((
            self.count,
            self.hardware_id,
            self.software_id,
            self.items,
            self.ref
        ))


@dataclass
class ImageSettings():
    """Data structure to hold the COPIS EDSDK image settings."""

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
start_live_view = _instance.start_live_view
end_live_view = _instance.end_live_view
download_evf_data = _instance.download_evf_data
focus = _instance.focus
transfer_pictures = _instance.transfer_pictures
step_focus = _instance.step_focus
evf_focus = _instance.evf_focus


@mproperty
def camera_count(mod) -> int:
    """Returns camera count from the module."""
    return mod._instance.camera_count

@mproperty
def is_connected(mod) -> bool:
    """Returns a flag indicating whether a device is connected."""
    return mod._instance.is_connected

@mproperty
def is_waiting_for_image(mod) -> bool:
    """Returns a flag indicating whether we are waiting for an image; from the module."""
    return mod._instance.is_waiting_for_image

@mproperty
def is_enabled(mod) -> bool:
    """Returns a flag indicating whether EDSDK is enabled; from the module."""
    return mod._instance.is_enabled

@mproperty
def device_list(mod) -> List[EdsDeviceInfo]:
    """Returns a list of descriptions of devices connected via edsdk; from the module."""
    return mod._instance.device_list
