from ctypes import *
import EDSDKLib
import struct

class Camera:
    def __init__(self, camera):
        unknown_code = c_uint(0xffffffff)

        self.camera = camera
        self.model_name = ""
        self.is_type_DS = False
        self.AE_mode = unknown_code
        self.AF_mode = unknown_code
        self.drive_mode = unknown_code
        self.white_balance = unknown_code
        self.av = unknown_code
        self.tv = unknown_code
        self.iso = unknown_code
        self.metering_mode = unknown_code
        self.exposure_compensation = unknown_code
        self.image_quality = unknown_code
        self.available_shot = 0
        self.evf_mode = unknown_code
        self.evf_output_device = unknown_code
        self.evf_depth_of_field_preview = unknown_code
        self.evf_af_mode = unknown_code
        self.focus_info = EDSDKLib.EDSDK.EdsFocusInfo()
        self.battery_level = unknown_code
        self.zoom = unknown_code
        self.zoom_rect = EDSDKLib.EDSDK.EdsRect()
        self.flash_mode = unknown_code
        self.can_download_image = True
        self.is_evf_enable = False
        self.temp_status = unknown_code
        self.roll_pitch = 1
        self.movie_quality = unknown_code
        self.fixed_movie = unknown_code
        self.mirror_up_setting = unknown_code
        self.click_WB = POINTER(c_byte)
        self.click_point = c_int()
        self.AE_mode_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.drive_mode_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.white_balance_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.av_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.tv_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.iso_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.metering_mode_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.exposure_compensation_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.image_quality_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.evf_AF_mode_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.zoom_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.flash_mode_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        self.move_quality_desc = EDSDKLib.EDSDK.EdsPropertyDesc()
        _execute_status = self.Status()

    class Status(Enum):
        NONE = 0
        DOWNLOADING = 1
        DELETING = 2
        CANCELING = 3

    def SetPropertyUInt32(self, property_id, value):
        if EDSDKLib.EDSDK.PropID_AEModeSelect: 
            self.AEMode = value
        elif EDSDKLib.EDSDK.PropID_AFMode:
            self.AFMode = value
        elif EDSDKLib.EDSDK.PropID_DriveMode:
            self.DriveMode = value
        elif EDSDKLib.EDSDK.PropID_Tv:
            self.Tv = value
        elif EDSDKLib.EDSDK.PropID_Av:
            self.Av = value
        elif EDSDKLib.EDSDK.PropID_ISOSpeed:
            self.Iso = value
        elif EDSDKLib.EDSDK.PropID_MeteringMode:
            self.MeteringMode = value
        elif EDSDKLib.EDSDK.PropID_ExposureCompensation:
            self.ExposureCompensation = value
        elif EDSDKLib.EDSDK.PropID_ImageQuality:
            self.ImageQuality = value
        elif EDSDKLib.EDSDK.PropID_Evf_Mode:
            self.EvfMode = value
        elif EDSDKLib.EDSDK.PropID_Evf_OutputDevice:
            self.EvfOutputDevice = value
        elif EDSDKLib.EDSDK.PropID_Evf_DepthOfFieldPreview:
            self.EvfDepthOfFieldPreview = value
        elif EDSDKLib.EDSDK.PropID_Evf_AFMode:
            self.EvfAFMode = value
        elif EDSDKLib.EDSDK.PropID_AvailableShots:
            self.AvailableShot = value
        elif EDSDKLib.EDSDK.PropID_DC_Zoom:
            self.Zoom = value
        elif EDSDKLib.EDSDK.PropID_DC_Strobe:
            self.FlashMode = value
        elif EDSDKLib.EDSDK.PropID_TempStatus:
            self.TempStatus = value
        elif EDSDKLib.EDSDK.PropID_FixedMovie:
            self.FixedMovie = value
        elif EDSDKLib.EDSDK.PropID_MirrorUpSetting:
            self.MirrorUpSetting = value

    def SetPropertyInt32(self, property_id, value):
        if property_id == EDSDKLib.EDSDK.PropID_WhiteBalance:
            self.white_balance = value
        elif property_id == EDSDKLib.EDSDK.PropID_BatteryLevel:
            self.battery_level = value

    def SetPropertyString(self, property_id, str):
        if property_id == EDSDKLib.EDSDK.PropID_ProductName:
            self.model_name = str
            self.is_type_DS = "EOS" in str

    def SetPropertyFocusInfo(self, property_id, info):
        if property_id == EDSDKLib.EDSDK.PropID_FocusInfo:
            self.focus_info = info

    def SetPropertyByteBlock(self, property_id, data):
        if property_id == EDSDKLib.EDSDK.PropID_MovieParam:
            self.movie_quality = struct.pack('i', data)
        if property_id == EDSDKLib.EDSDK.PropID_Evf_ClickWBCoeffs:
            self.click_WB = data

    def SetPropertyRect(self, property_id, info):
        if property_id == EDSDKLib.EDSDK.PropID_Evf_ZoomRect: 
            self.zoom_rect = info

    def SetPropertyDesc(self, property_id, desc):
        if EDSDKLib.EDSDK.PropID_AEModeSelect: 
            self.AEModeDesc = desc
        elif EDSDKLib.EDSDK.PropID_DriveMode: 
            self.DriveModeDesc = desc
        elif EDSDKLib.EDSDK.PropID_WhiteBalance: 
            self.WhiteBalanceDesc = desc
        elif EDSDKLib.EDSDK.PropID_Tv: 
            self.TvDesc = desc
        elif EDSDKLib.EDSDK.PropID_Av: 
            self.AvDesc = desc
        elif EDSDKLib.EDSDK.PropID_ISOSpeed: 
            self.IsoDesc = desc
        elif EDSDKLib.EDSDK.PropID_MeteringMode: 
            self.MeteringModeDesc = desc
        elif EDSDKLib.EDSDK.PropID_ExposureCompensation: 
            self.ExposureCompensationDesc = desc
        elif EDSDKLib.EDSDK.PropID_ImageQuality: 
            self.ImageQualityDesc = desc
        elif EDSDKLib.EDSDK.PropID_Evf_AFMode: 
            self.EvfAFModeDesc = desc
        elif EDSDKLib.EDSDK.PropID_DC_Zoom: 
            self.ZoomDesc = desc
        elif EDSDKLib.EDSDK.PropID_DC_Strobe: 
            self.FlashModeDesc = desc
        elif EDSDKLib.EDSDK.PropID_MovieParam: 
            self.MovieQualityDesc = desc

    def GetPropertyDesc(self, property_id):
        desc = EDSDKLib.EDSDK.EdsPropertyDesc()

        if EDSDKLib.EDSDK.PropID_AEModeSelect: 
            desc = self.AEModeDesc
        elif EDSDKLib.EDSDK.PropID_DriveMode: 
            desc = self.DriveModeDesc
        elif EDSDKLib.EDSDK.PropID_WhiteBalance: 
            desc = self.WhiteBalanceDesc
        elif EDSDKLib.EDSDK.PropID_Tv: 
            desc = self.TvDesc
        elif EDSDKLib.EDSDK.PropID_Av: 
            desc = self.AvDesc
        elif EDSDKLib.EDSDK.PropID_ISOSpeed: 
            desc = self.IsoDesc
        elif EDSDKLib.EDSDK.PropID_MeteringMode: 
            desc = self.MeteringModeDesc
        elif EDSDKLib.EDSDK.PropID_ExposureCompensation: 
            desc = self.ExposureCompensationDesc
        elif EDSDKLib.EDSDK.PropID_ImageQuality: 
            desc = self.ImageQualityDesc
        elif EDSDKLib.EDSDK.PropID_Evf_AFMode: 
            desc = self.EvfAFModeDesc
        elif EDSDKLib.EDSDK.PropID_DC_Zoom: 
            desc = self.ZoomDesc
        elif EDSDKLib.EDSDK.PropID_DC_Strobe: 
            desc = self.FlashModeDesc
        elif EDSDKLib.EDSDK.PropID_MovieParam: 
            desc = self.MovieQualityDesc

        return desc

    def GetZoomPosition(self):
        zoomPosition = EDSDKLib.EDSDK.EdsPoint()
        zoomPosition.x = self.zoom_rect.x
        zoomPosition.y = self.zoom_rect.y
        return zoomPosition