from ctypes import *
import os
from enum import *

class EDSDK():
	def __init__(self):
		dll_path_format = os.path.dirname(__file__) + os.path.sep + '{}'
		self.dll = CDLL(dll_path_format.format('EDSDK.dll')) 
		self.errorFormat = "EDSDK Exception Occurred: {} {}"

		################ Property Ids ################
		
		## Camera Setting Properties
		self.PropID_Unknown              = 0x0000ffff
		self.PropID_ProductName          = 0x00000002
		self.PropID_BodyIDEx             = 0x00000015
		self.PropID_OwnerName            = 0x00000004
		self.PropID_MakerName            = 0x00000005
		self.PropID_DateTime             = 0x00000006
		self.PropID_FirmwareVersion      = 0x00000007
		self.PropID_BatteryLevel         = 0x00000008
		self.PropID_CFn                  = 0x00000009
		self.PropID_SaveTo               = 0x0000000b
		self.kEdsPropID_CurrentStorage   = 0x0000000c
		self.kEdsPropID_CurrentFolder    = 0x0000000d
		self.PropID_BatteryQuality       = 0x00000010

		## Image Properties
		self.PropID_ImageQuality         = 0x00000100
		self.PropID_Orientation          = 0x00000102
		self.PropID_ICCProfile           = 0x00000103
		self.PropID_FocusInfo            = 0x00000104
		self.PropID_WhiteBalance         = 0x00000106
		self.PropID_ColorTemperature     = 0x00000107
		self.PropID_WhiteBalanceShift    = 0x00000108
		self.PropID_ColorSpace           = 0x0000010d
		self.PropID_PictureStyle         = 0x00000114
		self.PropID_PictureStyleDesc     = 0x00000115
		self.PropID_PictureStyleCaption  = 0x00000200

		## Capture Properties
		self.PropID_AEMode               = 0x00000400
		self.PropID_AEModeSelect         = 0x00000436
		self.PropID_DriveMode            = 0x00000401
		self.PropID_ISOSpeed             = 0x00000402
		self.PropID_MeteringMode         = 0x00000403
		self.PropID_AFMode               = 0x00000404
		self.PropID_Av                   = 0x00000405
		self.PropID_Tv                   = 0x00000406
		self.PropID_ExposureCompensation = 0x00000407
		self.PropID_FocalLength          = 0x00000409
		self.PropID_AvailableShots       = 0x0000040a
		self.PropID_Bracket              = 0x0000040b
		self.PropID_WhiteBalanceBracket  = 0x0000040c
		self.PropID_LensName             = 0x0000040d
		self.PropID_AEBracket            = 0x0000040e
		self.PropID_FEBracket            = 0x0000040f
		self.PropID_ISOBracket           = 0x00000410
		self.PropID_NoiseReduction       = 0x00000411
		self.PropID_FlashOn              = 0x00000412
		self.PropID_RedEye               = 0x00000413
		self.PropID_FlashMode            = 0x00000414
		self.PropID_LensStatus           = 0x00000416
		self.PropID_Artist	             = 0x00000418
		self.PropID_Copyright	         = 0x00000419

		## EVF Properties
		self.PropID_Evf_OutputDevice        = 0x00000500
		self.PropID_Evf_Mode                = 0x00000501
		self.PropID_Evf_WhiteBalance        = 0x00000502
		self.PropID_Evf_ColorTemperature    = 0x00000503
		self.PropID_Evf_DepthOfFieldPreview = 0x00000504
		
		## EVF IMAGE DATA Properties
		self.PropID_Evf_Zoom                = 0x00000507
		self.PropID_Evf_ZoomPosition        = 0x00000508
		self.PropID_Evf_ImagePosition       = 0x0000050B
		self.PropID_Evf_HistogramStatus     = 0x0000050C
		self.PropID_Evf_AFMode              = 0x0000050E
		self.PropID_Evf_HistogramY          = 0x00000515
		self.PropID_Evf_HistogramR          = 0x00000516
		self.PropID_Evf_HistogramG          = 0x00000517
		self.PropID_Evf_HistogramB          = 0x00000518
		
		self.PropID_Evf_CoordinateSystem    = 0x00000540
		self.PropID_Evf_ZoomRect            = 0x00000541
		
		self.PropID_Record                  = 0x00000510
		
		## Image GPS Properties
		self.PropID_GPSVersionID			 =  0x00000800
		self.PropID_GPSLatitudeRef		 =  0x00000801
		self.PropID_GPSLatitude			 =  0x00000802
		self.PropID_GPSLongitudeRef		 =  0x00000803
		self.PropID_GPSLongitude			 =  0x00000804
		self.PropID_GPSAltitudeRef		 =  0x00000805
		self.PropID_GPSAltitude			 =  0x00000806
		self.PropID_GPSTimeStamp			 =  0x00000807
		self.PropID_GPSSatellites		 =  0x00000808
		self.PropID_GPSStatus			 =  0x00000809
		self.PropID_GPSMapDatum			 =  0x00000812
		self.PropID_GPSDateStamp			 =  0x0000081D
		
		## DC Properties
		self.PropID_DC_Zoom               = 0x00000600
		self.PropID_DC_Strobe             = 0x00000601
		self.PropID_LensBarrelStatus      = 0x00000605
		
		self.PropID_TempStatus            = 0x01000415
		self.PropID_Evf_RollingPitching   = 0x01000544
		self.PropID_FixedMovie            = 0x01000422
		self.PropID_MovieParam            = 0x01000423
		
		self.PropID_Evf_ClickWBCoeffs     = 0x01000506
		self.PropID_ManualWhiteBalanceData = 0x01000204
		
		self.PropID_MirrorUpSetting       = 0x01000438
		self.PropID_MirrorLockUpState     = 0x01000421
		
		self.PropID_UTCTime               = 0x01000016
		self.PropID_TimeZone              = 0x01000017
		self.PropID_SummerTimeSetting     = 0x01000018

		############################################

		################ Event Ids #################

		## Camera Events
		## Property Event
		## Notifies all property events. 
		self.PropertyEvent_All                   = 0x00000100

		## Notifies that a camera property value has been changed. 
		# The changed property can be retrieved from event data. 
		# The changed value can be retrieved by means of EdsGetPropertyData. 
		# In the case of type 1 protocol standard cameras, 
		# notification of changed properties can only be issued for custom functions (CFn). 
		# If the property type is 0x0000FFFF, the changed property cannot be identified. 
		# Thus, retrieve all required properties repeatedly. 
		self.PropertyEvent_PropertyChanged       = 0x00000101

		## Notifies of changes in the list of camera properties with configurable values.
		# The list of configurable values for property IDs indicated in event data
		# can be retrieved by means of EdsGetPropertyDesc. 
		# For type 1 protocol standard cameras, the property ID is identified as "Unknown"
		# during notification. 
		# Thus, you must retrieve a list of configurable values for all properties and
		# retrieve the property values repeatedly. 
		# (For details on properties for which you can retrieve a list of configurable
		# properties, 
		# see the description of EdsGetPropertyDesc). 
		self.PropertyEvent_PropertyDescChanged    = 0x00000102

		## Object Event
		## Notifies all object events. 
		self.ObjectEvent_All                     = 0x00000200

		## Notifies that the volume object (memory card) state (VolumeInfo)
		# has been changed. 
		# Changed objects are indicated by event data. 
		# The changed value can be retrieved by means of EdsGetVolumeInfo. 
		# Notification of this event is not issued for type 1 protocol standard cameras. 
		self.ObjectEvent_VolumeInfoChanged       = 0x00000201

		## Notifies if the designated volume on a camera has been formatted.
		# If notification of this event is received, get sub-items of the designated
		# volume again as needed. 
		# Changed volume objects can be retrieved from event data. 
		# Objects cannot be identified on cameras earlier than the D30
		# if files are added or deleted. 
		# Thus, these events are subject to notification. 
		self.ObjectEvent_VolumeUpdateItems       = 0x00000202

		## Notifies if many images are deleted in a designated folder on a camera.
		# If notification of this event is received, get sub-items of the designated
		# folder again as needed. 
		# Changed folders (specifically, directory item objects) can be retrieved
		# from event data. 
		self.ObjectEvent_FolderUpdateItems       = 0x00000203

		## Notifies of the creation of objects such as new folders or files
		# on a camera compact flash card or the like. 
		# This event is generated if the camera has been set to store captured
		# images simultaneously on the camera and a computer,
		# for example, but not if the camera is set to store images
		# on the computer alone. 
		# Newly created objects are indicated by event data. 
		# Because objects are not indicated for type 1 protocol standard cameras,
		# (that is, objects are indicated as NULL),
		# you must again retrieve child objects under the camera object to 
		# identify the new objects. 
		self.ObjectEvent_DirItemCreated          = 0x00000204

		## Notifies of the deletion of objects such as folders or files on a camera
		# compact flash card or the like. 
		# Deleted objects are indicated in event data. 
		# Because objects are not indicated for type 1 protocol standard cameras, 
		# you must again retrieve child objects under the camera object to
		# identify deleted objects. 
		self.ObjectEvent_DirItemRemoved          = 0x00000205

		## Notifies that information of DirItem objects has been changed. 
		# Changed objects are indicated by event data. 
		# The changed value can be retrieved by means of EdsGetDirectoryItemInfo. 
		# Notification of this event is not issued for type 1 protocol standard cameras. 
		self.ObjectEvent_DirItemInfoChanged      = 0x00000206

		## Notifies that header information has been updated, as for rotation information
		# of image files on the camera. 
		# If this event is received, get the file header information again, as needed. 
		# This function is for type 2 protocol standard cameras only. 
		self.ObjectEvent_DirItemContentChanged   = 0x00000207

		## Notifies that there are objects on a camera to be transferred to a computer. 
		# This event is generated after remote release from a computer or local release
		# from a camera. 
		# If this event is received, objects indicated in the event data must be downloaded.
		# Furthermore, if the application does not require the objects, instead
		# of downloading them,
		# execute EdsDownloadCancel and release resources held by the camera. 
		# The order of downloading from type 1 protocol standard cameras must be the order
		# in which the events are received. 
		self.ObjectEvent_DirItemRequestTransfer  = 0x00000208

		## Notifies if the camera's direct transfer button is pressed. 
		# If this event is received, objects indicated in the event data must be downloaded. 
		# Furthermore, if the application does not require the objects, instead of
		# downloading them, 
		# execute EdsDownloadCancel and release resources held by the camera. 
		# Notification of this event is not issued for type 1 protocol standard cameras. 
		self.ObjectEvent_DirItemRequestTransferDT    = 0x00000209

		## Notifies of requests from a camera to cancel object transfer 
		# if the button to cancel direct transfer is pressed on the camera. 
		# If the parameter is 0, it means that cancellation of transfer is requested for
		# objects still not downloaded,
		# with these objects indicated by kEdsObjectEvent_DirItemRequestTransferDT. 
		# Notification of this event is not issued for type 1 protocol standard cameras. 
		self.ObjectEvent_DirItemCancelTransferDT     = 0x0000020a

		self.ObjectEvent_VolumeAdded                 = 0x0000020c
		self.ObjectEvent_VolumeRemoved				= 0x0000020d

		## State Event
		## Notifies all state events. 
		self.StateEvent_All                      = 0x00000300

		## Indicates that a camera is no longer connected to a computer, 
		# whether it was disconnected by unplugging a cord, opening
		# the compact flash compartment, 
		# turning the camera off, auto shut-off, or by other means. 
		self.StateEvent_Shutdown                 = 0x00000301

		## Notifies of whether or not there are objects waiting to
		# be transferred to a host computer. 
		# This is useful when ensuring all shot images have been transferred 
		# when the application is closed. 
		# Notification of this event is not issued for type 1 protocol 
		# standard cameras. 
		self.StateEvent_JobStatusChanged         = 0x00000302

		## Notifies that the camera will shut down after a specific period. 
		# Generated only if auto shut-off is set. 
		# Exactly when notification is issued (that is, the number of
		# seconds until shutdown) varies depending on the camera model. 
		# To continue operation without having the camera shut down,
		# use EdsSendCommand to extend the auto shut-off timer.
		# The time in seconds until the camera shuts down is returned
		# as the initial value. 
		self.StateEvent_WillSoonShutDown         = 0x00000303

		## As the counterpart event to kEdsStateEvent_WillSoonShutDown,
		# this event notifies of updates to the number of seconds until
		# a camera shuts down. 
		# After the update, the period until shutdown is model-dependent. 
		self.StateEvent_ShutDownTimerUpdate      = 0x00000304 

		## Notifies that a requested release has failed, due to focus
		# failure or similar factors. 
		self.StateEvent_CaptureError             = 0x00000305

		## Notifies of internal SDK errors. 
		# If this error event is received, the issuing device will probably
		# not be able to continue working properly,
		# so cancel the remote connection. 
		self.StateEvent_InternalError            = 0x00000306
		
		self.StateEvent_AfResult                  = 0x00000309

		############################################

		################ Camera Commands #################

		## Send Commands
		self.CameraCommand_TakePicture             = 0x00000000
		self.CameraCommand_ExtendShutDownTimer     = 0x00000001
		self.CameraCommand_BulbStart			      = 0x00000002
		self.CameraCommand_BulbEnd				  = 0x00000003
		self.CameraCommand_DoEvfAf                 = 0x00000102
		self.CameraCommand_DriveLensEvf            = 0x00000103
		self.CameraCommand_DoClickWBEvf            = 0x00000104
		self.CameraCommand_MovieSelectSwON         = 0x00000107
		self.CameraCommand_MovieSelectSwOFF        = 0x00000108

		self.CameraCommand_PressShutterButton      = 0x00000004
		self.CameraCommand_SetRemoteShootingMode   = 0x0000010f
		self.CameraCommand_RequestRollPitchLevel   = 0x00000109

		## Status Commands
		self.CameraState_UILock                = 0x00000000
		self.CameraState_UIUnLock              = 0x00000001
		self.CameraState_EnterDirectTransfer   = 0x00000002
		self.CameraState_ExitDirectTransfer    = 0x00000003

		##################################################

		## Drive Lens
		self.EvfDriveLens_Near1		= 0x00000001
		self.EvfDriveLens_Near2		= 0x00000002
		self.EvfDriveLens_Near3		= 0x00000003
		self.EvfDriveLens_Far1		= 0x00008001
		self.EvfDriveLens_Far2		= 0x00008002
		self.EvfDriveLens_Far3		= 0x00008003

		## Depth of Field Preview
		self.EvfDepthOfFieldPreview_OFF	= 0x00000000
		self.EvfDepthOfFieldPreview_ON	= 0x00000001

		##Image Format 
		self.ImageFormat_Unknown = 0x00000000
		self.ImageFormat_Jpeg = 0x00000001
		self.ImageFormat_CRW = 0x00000002
		self.ImageFormat_RAW = 0x00000004

		self.ImageFormat_CR2 = 0x00000006

		self.ImageSize_Large = 0
		self.ImageSize_Middle = 1
		self.ImageSize_Small = 2
		self.ImageSize_Middle1 = 5
		self.ImageSize_Middle2 = 6
		self.ImageSize_Unknown = -1

		self.CompressQuality_Normal = 2
		self.CompressQuality_Fine = 3
		self.CompressQuality_Lossless = 4
		self.CompressQuality_SuperFine = 5
		self.CompressQuality_Unknown = -1

		##Battery level
		self.BatteryLevel_Empty    = 1   
		self.BatteryLevel_Low      = 30      
		self.BatteryLevel_Half     = 50      
		self.BatteryLevel_Normal   = 80
		self.BatteryLevel_AC       = 0xFFFFFFFF     

		##White Balance
		self.WhiteBalance_Click         = -1
		self.WhiteBalance_Auto          = 0
		self.WhiteBalance_Daylight      = 1
		self.WhiteBalance_Cloudy        = 2
		self.WhiteBalance_Tungsten      = 3
		self.WhiteBalance_Fluorescent   = 4
		self.WhiteBalance_Strobe        = 5
		self.WhiteBalance_Shade         = 8
		self.WhiteBalance_ColorTemp     = 9
		self.WhiteBalance_Manual1       = 6
		self.WhiteBalance_Manual2       = 15
		self.WhiteBalance_Manual3       = 16
		self.WhiteBalance_Manual4       = 18
		self.WhiteBalance_Manual5       = 19
		self.WhiteBalance_PCSet1        = 10
		self.WhiteBalance_PCSet2        = 11
		self.WhiteBalance_PCSet3        = 12
		self.WhiteBalance_PCSet4        = 20
		self.WhiteBalance_PCSet5        = 21
		self.WhiteBalance_AwbWhite      = 23 

		##Color Space
		self.ColorSpace_sRGB       = 1
		self.ColorSpace_AdobeRGB   = 2
		self.ColorSpace_Unknown    = 0xffffffff

		##PictureStyle
		self.PictureStyle_Standard     = 0x0081
		self.PictureStyle_Portrait     = 0x0082
		self.PictureStyle_Landscape    = 0x0083
		self.PictureStyle_Neutral      = 0x0084
		self.PictureStyle_Faithful     = 0x0085
		self.PictureStyle_Monochrome   = 0x0086
		self.PictureStyle_Auto         = 0x0087
		self.PictureStyle_FineDetail   = 0x0088
		self.PictureStyle_User1        = 0x0021
		self.PictureStyle_User2        = 0x0022
		self.PictureStyle_User3        = 0x0023
		self.PictureStyle_PC1          = 0x0041
		self.PictureStyle_PC2          = 0x0042
		self.PictureStyle_PC3          = 0x0043

		##AE Mode
		self.AEMode_Program          = 0
		self.AEMode_Tv               = 1
		self.AEMode_Av               = 2
		self.AEMode_Mamual           = 3
		self.AEMode_Bulb             = 4
		self.AEMode_A_DEP            = 5
		self.AEMode_DEP              = 6
		self.AEMode_Custom           = 7
		self.AEMode_Lock             = 8
		self.AEMode_Green            = 9
		self.AEMode_NigntPortrait    = 10
		self.AEMode_Sports           = 11
		self.AEMode_Portrait         = 12
		self.AEMode_Landscape        = 13
		self.AEMode_Closeup          = 14
		self.AEMode_FlashOff         = 15
		self.AEMode_CreativeAuto     = 19
		self.AEMode_Movie			= 20
		self.AEMode_PhotoInMovie		= 21
		self.AEMode_SceneIntelligentAuto = 22
		self.AEMode_SCN              = 25
		self.AEMode_HandheldNightScenes  = 23
		self.AEMode_Hdr_BacklightControl = 24
		self.AEMode_Children         = 26
		self.AEMode_Food             = 27
		self.AEMode_CandlelightPortraits = 28
		self.AEMode_CreativeFilter   = 29
		self.AEMode_RoughMonoChrome  = 30
		self.AEMode_SoftFocus        = 31
		self.AEMode_ToyCamera        = 32
		self.AEMode_Fisheye          = 33
		self.AEMode_WaterColor       = 34
		self.AEMode_Miniature        = 35
		self.AEMode_Hdr_Standard     = 36
		self.AEMode_Hdr_Vivid        = 37
		self.AEMode_Hdr_Bold         = 38
		self.AEMode_Hdr_Embossed     = 39
		self.AEMode_Movie_Fantasy    = 40
		self.AEMode_Movie_Old        = 41
		self.AEMode_Movie_Memory     = 42
		self.AEMode_Movie_DirectMono = 43
		self.AEMode_Movie_Mini       = 44
		self.AEMode_Panning          = 45
		self.AEMode_GroupPhoto       = 46

		self.AEMode_SelfPortrait     = 50
		self.AEMode_PlusMovieAuto    = 51
		self.AEMode_SmoothSkin       = 52
		self.AEMode_Panorama         = 53
		self.AEMode_Silent           = 54
		self.AEMode_Flexible         = 55
		self.AEMode_OilPainting      = 56
		self.AEMode_Fireworks        = 57
		self.AEMode_StarPortrait     = 58
		self.AEMode_StarNightscape   = 59
		self.AEMode_StarTrails       = 60
		self.AEMode_StarTimelapseMovie = 61
		self.AEMode_BackgroundBlur   = 62
		self.AEMode_Unknown          = 0xffffffff

		##Bracket
		self.Bracket_AEB             = 0x01
		self.Bracket_ISOB            = 0x02
		self.Bracket_WBB             = 0x04
		self.Bracket_FEB             = 0x08
		self.Bracket_Unknown         = 0xffffffff

		##EVF Output Device [Flag]
		self.EvfOutputDevice_TFT	= 1
		self.EvfOutputDevice_PC		= 2

		##EVF Zoom
		self.EvfZoom_Fit	= 1
		self.EvfZoom_x5		= 5
		self.EvfZoom_x10	= 10

		

	################################# Basic functions #################################
	###################################################################################
	#
	#  Function:   EdsInitializeSDK
	#
	#  Description:
	#      Initializes the libraries. 
	#      When using the EDSDK libraries, you must call this API once  
	#          before using EDSDK APIs.
	#
	#  Parameters:
	#       In:    None
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	###################################################################################
	def EdsInitializeSDK(self):
		err = self.dll.EdsInitializeSDK()
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))

	###################################################################################
	#
	#  Function:   EdsTerminateSDK
	#
	#  Description:
	#      Terminates use of the libraries. 
	#      This function muse be called when ending the SDK.
	#      Calling this function releases all resources allocated by the libraries.
	#
	#  Parameters:
	#       In:    None
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	###################################################################################
	def EdsTerminateSDK(self):	
		err = self.dll.EdsTerminateSDK()
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))

	###################### Reference-counter operating functions ######################
	###################################################################################
	#
	#  Function:   EdsRetain
	#
	#  Description:
	#      Increments the reference counter of existing objects.
	#
	#  Parameters:
	#       In:    inRef - The reference for the item.
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	###################################################################################
	def EdsRetain(self, inRef):
		err = self.dll.EdsRetain(c_int(inRef))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	###################################################################################
	#
	#  Function:   EdsRelease
	#
	#  Description:
	#      Decrements the reference counter to an object. 
	#      When the reference counter reaches 0, the object is released.
	#
	#  Parameters:
	#       In:    inRef - The reference of the item.
	#      Out:    None
	#  Returns:    Any of the sdk errors.
	###################################################################################
	def EdsRelease(self, inRef):
		err = self.dll.EdsRelease(inRef)
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	########################## Item-tree operating functions ##########################
	###################################################################################
	#
	#  Function:   EdsGetChildCount
	#
	#  Description:
	#      Gets the number of child objects of the designated object.
	#      Example: Number of files in a directory
	#
	#  Parameters:
	#       In:    inRef - The reference of the list.
	#      Out:    outCount - Number of elements in this list.
	#
	#  Returns:    Any of the sdk errors.
	###################################################################################
	def EdsGetChildCount(self, inRef):
		outCount = c_int()
		err = self.dll.EdsGetChildCount(inRef, byref(outCount))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outCount.value
	
	###################################################################################
	#
	#  Function:   EdsGetChildAtIndex
	#
	#  Description:
	#       Gets an indexed child object of the designated object. 
	#
	#  Parameters:
	#       In:    inRef - The reference of the item.
	#              inIndex -  The index that is passed in, is zero based.
	#      Out:    outRef - The pointer which receives reference of the 
	#                           specified index .
	#
	#  Returns:    Any of the sdk errors.
	###################################################################################
	def EdsGetChildAtIndex(self, inRef, inIndex):
		outRef = c_void_p()
		err = self.dll.EdsGetChildAtIndex(inRef, inIndex, byref(outRef))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outRef
	
	###################################################################################
	#
	#  Function:   EdsGetParent
	#
	#  Description:
	#      Gets the parent object of the designated object.
	#
	#  Parameters:
	#       In:    inRef        - The reference of the item.
	#      Out:    outParentRef - The pointer which receives reference.
	#
	#  Returns:    Any of the sdk errors.
	###################################################################################
	def EdsGetParent(self, inRef):
		outParentRef = c_void_p()
		err = self.dll.EdsGetParent(c_int(inRef), byref(outParentRef))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outParentRef
	
	########################### Property operating functions ##########################  
	###################################################################################
	#
	#  Function:   EdsGetPropertySize
	#
	#  Description:
	#      Gets the byte size and data type of a designated property 
	#          from a camera object or image object.
	#
	#  Parameters:
	#       In:    inRef - The reference of the item.
	#              inPropertyID - The ProprtyID
	#              inParam - Additional information of property.
	#                   We use this parameter in order to specify an index
	#                   in case there are two or more values over the same ID.
	#      Out:    outDataType - Pointer to the buffer that is to receive the property
	#                        type data.
	#              outSize - Pointer to the buffer that is to receive the property
	#                        size.
	#
	#  Returns:    Any of the sdk errors.
	###################################################################################
	def EdsGetPropertySize(self, inRef, inPropertyID, inParam):
		outDataType = c_uint()
		outSize = c_int()
		err = self.dll.EdsGetPropertySize(inRef, c_uint(inPropertyID), c_int(inParam), byref(outDataType), byref(outSize))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		outDataType = EdsDataType(outDataType.value)
		return {"dataType": outDataType, "size": outSize}
	
	###################################################################################
	#
	#  Function:   EdsGetPropertyData
	#
	#  Description:
	#      Gets property information from the object designated in inRef.
	#
	#  Parameters:
	#       In:    inRef - The reference of the item.
	#              inPropertyID - The ProprtyID
	#              inParam - Additional information of property.
	#                   We use this parameter in order to specify an index
	#                   in case there are two or more values over the same ID.
	#              inPropertySize - The number of bytes of the prepared buffer
	#                  for receive property-value.
	#       Out:   outPropertyData - The buffer pointer to receive property-value.
	#
	#  Returns:    Any of the sdk errors.
	###################################################################################
	def EdsGetPropertyData(self, inRef, inPropertyID, inParam, inPropertySize, outPropertyData):
		err = self.dll.EdsGetPropertyData(inRef, inPropertyID, inParam, inPropertySize, byref(outPropertyData))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outPropertyData

	##############################################################################
	#  Function:   EdsSetPropertyData
	#
	#  Description:
	#      Sets property data for the object designated in inRef. 
	#
	#  Parameters:
	#       In:    inRef - The reference of the item.
	#              inPropertyID - The ProprtyID
	#              inParam - Additional information of property.
	#              inPropertySize - The number of bytes of the prepared buffer
	#                  for set property-value.
	#              inPropertyData - The buffer pointer to set property-value.
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsSetPropertyData(self, inRef, inPropertyID, inParam, inPropertySize, inPropertyData):
		data = c_int(inPropertyData)
		err = self.dll.EdsSetPropertyData(inRef, inPropertyID, inParam, inPropertySize, byref(data))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsGetPropertyDesc
	#
	#  Description:
	#      Gets a list of property data that can be set for the object 
	#          designated in inRef, as well as maximum and minimum values. 
	#      This API is intended for only some shooting-related properties.
	#
	#  Parameters:
	#       In:    inRef - The reference of the camera.
	#              inPropertyID - The Property ID.
	#       Out:   outPropertyDesc - Array of the value which can be set up.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	#def EdsGetPropertyDesc( IntPtr inRef, uint inPropertyID, out EdsPropertyDesc outPropertyDesc):
	
	
	##############################################################################
	#  Function:   EdsGetCameraList
	#
	#  Description:
	#      Gets camera list objects.
	#
	#  Parameters:
	#       In:    None
	#      Out:    outCameraListRef - Pointer to the camera-list.
	#
	#  Returns:    Any of the sdk errors..
	##############################################################################
	def EdsGetCameraList(self):
		outCameraListRef = c_void_p(None)
		err = self.dll.EdsGetCameraList(byref(outCameraListRef))
	
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outCameraListRef
	
	##############################################################################
	#  Function:   EdsGetDeviceInfo
	#
	#  Description:
	#      Gets device information, such as the device name.  
	#      Because device information of remote cameras is stored 
	#          on the host computer, you can use this API 
	#          before the camera object initiates communication
	#          (that is, before a session is opened). 
	#
	#  Parameters:
	#       In:    inCameraRef - The reference of the camera.
	#      Out:    outDeviceInfo - Information as device of camera.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsGetDeviceInfo(self, inCameraRef):
		deviceInfo = EdsDeviceInfo()
		err = self.dll.EdsGetDeviceInfo(inCameraRef, byref(deviceInfo))

		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))

		return deviceInfo
	
	##############################################################################
	#  Function:   EdsOpenSession
	#
	#  Description:
	#      Establishes a logical connection with a remote camera. 
	#      Use this API after getting the camera's EdsCamera object.
	#
	#  Parameters:
	#       In:    inCameraRef - The reference of the camera 
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsOpenSession(self, inCameraRef):
		err = self.dll.EdsOpenSession(inCameraRef)
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsCloseSession
	#
	#  Description:
	#       Closes a logical connection with a remote camera.
	#
	#  Parameters:
	#       In:    inCameraRef - The reference of the camera 
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsCloseSession(self, inCameraRef):
		err = self.dll.EdsCloseSession(inCameraRef)
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsSendCommand
	#
	#  Description:
	#       Sends a command such as "Shoot" to a remote camera. 
	#
	#  Parameters:
	#       In:    inCameraRef - The reference of the camera which will receive the 
	#                      command.
	#              inCommand - Specifies the command to be sent.
	#              inParam -     Specifies additional command-specific information.
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsSendCommand(self, inCameraRef, inCommand, inParam):
		err = self.dll.EdsSendCommand(inCameraRef, c_uint(inCommand), c_int(inParam))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsSendStatusCommand
	#
	#  Description:
	#       Sets the remote camera state or mode.
	#
	#  Parameters:
	#       In:    inCameraRef - The reference of the camera which will receive the 
	#                      command.
	#              inStatusCommand - Specifies the command to be sent.
	#              inParam -     Specifies additional command-specific information.
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsSendStatusCommand(self, inCameraRef, inCameraState, inParam):
		err = self.dll.EdsSendStatusCommand(inCameraRef, c_uint(inCameraState), c_int(inParam))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsSetCapacity
	#
	#  Description:
	#      Sets the remaining HDD capacity on the host computer
	#          (excluding the portion from image transfer),
	#          as calculated by subtracting the portion from the previous time. 
	#      Set a reset flag initially and designate the cluster length 
	#          and number of free clusters.
	#      Some type 2 protocol standard cameras can display the number of shots 
	#          left on the camera based on the available disk capacity 
	#          of the host computer. 
	#      For these cameras, after the storage destination is set to the computer, 
	#          use this API to notify the camera of the available disk capacity 
	#          of the host computer.
	#
	#  Parameters:
	#       In:    inCameraRef - The reference of the camera which will receive the 
	#                      command.
	#              inCapacity -  The remaining capacity of a transmission place.
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsSetCapacity(self, inCameraRef, inCapacity):
		err = self.dll.EdsSetCapacity(inCameraRef,inCapacity)
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsGetVolumeInfo
	#
	#  Description:
	#      Gets volume information for a memory card in the camera.
	#
	#  Parameters:
	#       In:    inVolumeRef - The reference of the volume.
	#      Out:    outVolumeInfo - information of  the volume.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsGetVolumeInfo(self, inVolumeRef):
		outVolumeInfo = EdsVolumeInfo()
		err = self.dll.EdsGetVolumeInfo(inVolumeRef, byref(outVolumeInfo))
		outVolumeInfo.ref = inVolumeRef
		
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outVolumeInfo
	
	##############################################################################
	#  Function:   EdsFormatVolume
	#
	#  Description:
	#       .
	#
	#  Parameters:
	#       In:    inVolumeRef - The reference of volume .
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsFormatVolume(self, inVolumeRef):
		err = self.dll.EdsFormatVolume(c_int(inVolumeRef))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsGetDirectoryItemInfo
	#
	#  Description:
	#      Gets information about the directory or file objects 
	#          on the memory card (volume) in a remote camera.
	#
	#  Parameters:
	#       In:    inDirItemRef - The reference of the directory item.
	#      Out:    outDirItemInfo - information of the directory item.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsGetDirectoryItemInfo(self, inDirItemRef):
		out_dir_item_info = DirectoryItemInfo()
		err = self.dll.EdsGetDirectoryItemInfo(c_int64(inDirItemRef), byref(out_dir_item_info))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return out_dir_item_info
	
	##############################################################################
	#  Function:   EdsDeleteDirectoryItem
	#
	#  Description:
	#      Deletes a camera folder or file.
	#      If folders with subdirectories are designated, all files are deleted 
	#          except protected files. 
	#      EdsDirectoryItem objects deleted by means of this API are implicitly 
	#          released by the EDSDK. Thus, there is no need to release them 
	#          by means of EdsRelease.
	#
	#  Parameters:
	#       In:    inDirItemRef - The reference of the directory item.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsDeleteDirectoryItem(self, inDirItemRef):
		err = self.dll.EdsDeleteDirectoryItem(c_int(inDirItemRef))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsDownload
	#
	#  Description:
	#       Downloads a file on a remote camera 
	#          (in the camera memory or on a memory card) to the host computer. 
	#      The downloaded file is sent directly to a file stream created in advance. 
	#      When dividing the file being retrieved, call this API repeatedly. 
	#      Also in this case, make the data block size a multiple of 512 (bytes), 
	#          excluding the final block.
	#
	#  Parameters:
	#       In:    inDirItemRef - The reference of the directory item.
	#              inReadSize   - 
	#
	#      Out:    outStream    - The reference of the stream.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsDownload(self, inDirItemRef, inReadSize, stream):
		outStream = stream
		err = self.dll.EdsDownload(c_int64(inDirItemRef), inReadSize, outStream)
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outStream
	
	##############################################################################
	#  Function:   EdsDownloadCancel
	#
	#  Description:
	#       Must be executed when downloading of a directory item is canceled. 
	#      Calling this API makes the camera cancel file transmission.
	#      It also releases resources. 
	#      This operation need not be executed when using EdsDownloadThumbnail. 
	#
	#  Parameters:
	#       In:    inDirItemRef - The reference of the directory item.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsDownloadCancel (self, inDirItemRef):
		err = self.dll.EdsDownloadCancel(c_int(inDirItemRef))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsDownloadComplete
	#
	#  Description:
	#       Must be called when downloading of directory items is complete. 
	#          Executing this API makes the camera 
	#              recognize that file transmission is complete. 
	#          This operation need not be executed when using EdsDownloadThumbnail.
	#
	#  Parameters:
	#       In:    inDirItemRef - The reference of the directory item.
	#
	#      Out:    outStream    - None.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsDownloadComplete (self, inDirItemRef):
		err = self.dll.EdsDownloadComplete(c_int64(inDirItemRef))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsDownloadThumbnail
	#
	#  Description:
	#      Extracts and downloads thumbnail information from image files in a camera. 
	#      Thumbnail information in the camera's image files is downloaded 
	#          to the host computer. 
	#      Downloaded thumbnails are sent directly to a file stream created in advance.
	#
	#  Parameters:
	#       In:    inDirItemRef - The reference of the directory item.
	#
	#      Out:    outStream - The reference of the stream.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsDownloadThumbnail(self, inDirItemRef):
		outStream = c_void_p()
		err = self.dll.EdsDownloadThumbnail(c_void_p(inDirItemRef))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outStream
	
	##############################################################################
	#  Function:   EdsGetAttribute
	#
	#  Description:
	#      Gets attributes of files on a camera.
	#  
	#  Parameters:
	#       In:    inDirItemRef - The reference of the directory item.
	#      Out:    outFileAttribute  - Indicates the file attributes. 
	#                  As for the file attributes, OR values of the value defined
	#                  by enum EdsFileAttributes can be retrieved. Thus, when 
	#                  determining the file attributes, you must check 
	#                  if an attribute flag is set for target attributes. 
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	#def EdsGetAttribute( IntPtr inDirItemRef, out EdsFileAttribute outFileAttribute):
	
	##############################################################################
	#  Function:   EdsSetAttribute
	#
	#  Description:
	#      Changes attributes of files on a camera.
	#  
	#  Parameters:
	#       In:    inDirItemRef - The reference of the directory item.
	#              inFileAttribute  - Indicates the file attributes. 
	#                      As for the file attributes, OR values of the value 
	#                      defined by enum EdsFileAttributes can be retrieved. 
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	#def EdsSetAttribute( IntPtr inDirItemRef, EdsFileAttribute inFileAttribute):
	
	##############################################################################
	#  Function:   EdsCreateFileStream
	#
	#  Description:
	#      Creates a new file on a host computer (or opens an existing file) 
	#          and creates a file stream for access to the file. 
	#      If a new file is designated before executing this API, 
	#          the file is actually created following the timing of writing 
	#          by means of EdsWrite or the like with respect to an open stream.
	#
	#  Parameters:
	#       In:    inFileName - Pointer to a null-terminated string that specifies
	#                           the file name.
	#              inCreateDisposition - Action to take on files that exist, 
	#                                and which action to take when files do not exist.  
	#              inDesiredAccess - Access to the stream (reading, writing, or both).
	#      Out:    outStream - The reference of the stream.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsCreateFileStream(self, inFileName, inCreateDisposition, inDesiredAccess):
		outStream = c_void_p()
		err = self.dll.EdsCreateFileStream(create_string_buffer(str.encode(inFileName), 256).value, inCreateDisposition, inDesiredAccess, byref(outStream))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outStream
	
	##############################################################################
	#  Function:   EdsCreateMemoryStream
	#
	#  Description:
	#      Creates a stream in the memory of a host computer. 
	#      In the case of writing in excess of the allocated buffer size, 
	#          the memory is automatically extended.
	#
	#  Parameters:
	#       In:    inBufferSize - The number of bytes of the memory to allocate.
	#      Out:    outStream - The reference of the stream.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsCreateMemoryStream(self, inBufferSize):
		outStream = c_void_p()
		err = self.dll.EdsCreateMemoryStream(c_int64(inBufferSize), byref(outStream))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outStream
	
	##############################################################################
	#  Function:   EdsCreateStreamEx
	#
	#  Description:
	#      An extended version of EdsCreateStreamFromFile. 
	#      Use this function when working with Unicode file names.
	#
	#  Parameters:
	#       In:    inFileName - Designate the file name. 
	#              inCreateDisposition - Action to take on files that exist, 
	#                                and which action to take when files do not exist.  
	#              inDesiredAccess - Access to the stream (reading, writing, or both).
	#
	#      Out:    outStream - The reference of the stream.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	#def EdsCreateStreamEx(string inFileName, EdsFileCreateDisposition inCreateDisposition, EdsAccess inDesiredAccess, out IntPtr outStream):
	
	##############################################################################
	#  Function:   EdsCreateMemoryStreamFromPointer        
	#
	#  Description:
	#      Creates a stream from the memory buffer you prepare. 
	#      Unlike the buffer size of streams created by means of EdsCreateMemoryStream, 
	#      the buffer size you prepare for streams created this way does not expand.
	#
	#  Parameters:
	#       In:    inBufferSize - The number of bytes of the memory to allocate.
	#      Out:    outStream - The reference of the stream.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsCreateMemoryStreamFromPointer(self, inUserBuffer, inBufferSize):
		outStream = c_void_p()
		err = self.dll.EdsCreateMemoryStreamFromPointer(c_void_p(inUserBuffer), c_uint64(inBufferSize))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outStream
	
	##############################################################################
	#  Function:   EdsGetPointer
	#
	#  Description:
	#      Gets the pointer to the start address of memory managed by the memory stream. 
	#      As the EDSDK automatically resizes the buffer, the memory stream provides 
	#          you with the same access methods as for the file stream. 
	#      If access is attempted that is excessive with regard to the buffer size
	#          for the stream, data before the required buffer size is allocated 
	#          is copied internally, and new writing occurs. 
	#      Thus, the buffer pointer might be switched on an unknown timing. 
	#      Caution in use is therefore advised. 
	#
	#  Parameters:
	#       In:    inStream - Designate the memory stream for the pointer to retrieve. 
	#      Out:    outPointer - If successful, returns the pointer to the buffer 
	#                  written in the memory stream.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsGetPointer(self, inStreamRef, data):
		outPointer = (POINTER(c_ubyte))(data)
		err = self.dll.EdsGetPointer(inStreamRef, byref(outPointer))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outPointer
	
	##############################################################################
	#  Function:   EdsRead
	#
	#  Description:
	#      Reads data the size of inReadSize into the outBuffer buffer, 
	#          starting at the current read or write position of the stream. 
	#      The size of data actually read can be designated in outReadSize.
	#
	#  Parameters:
	#       In:    inStreamRef - The reference of the stream or image.
	#              inReadSize -  The number of bytes to read.
	#      Out:    outBuffer - Pointer to the user-supplied buffer that is to receive
	#                          the data read from the stream. 
	#              outReadSize - The actually read number of bytes.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsRead(self, inStreamRef, inReadSize):
		outBuffer = c_void_p()
		outReadSize = c_uint64()
		err = self.dll.EdsRead(inStreamRef, c_uint64(inReadSize), byref(outBuffer), byref(outReadSize))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return {"buffer": outBuffer, "readSize": outReadSize}
	
	##############################################################################
	#  Function:   EdsWrite
	#
	#  Description:
	#      Writes data of a designated buffer 
	#          to the current read or write position of the stream. 
	#
	#  Parameters:
	#       In:    inStreamRef  - The reference of the stream or image.
	#              inWriteSize - The number of bytes to write.
	#              inBuffer - A pointer to the user-supplied buffer that contains 
	#                         the data to be written to the stream.
	#      Out:    outWrittenSize - The actually written-in number of bytes.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsWrite(self, inStreamRef, inWriteSize, inBuffer):
		outWrittenSize = c_uint()
		err = self.dll.EdsWrite(inStreamRef, c_uint64(inWriteSize), c_void_p(inBuffer), byref(outWrittenSize))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outWrittenSize
	
	##############################################################################
	#  Function:   EdsSeek
	#
	#  Description:
	#      Moves the read or write position of the stream
	#            (that is, the file position indicator).
	#
	#  Parameters:
	#       In:    inStreamRef  - The reference of the stream or image. 
	#              inSeekOffset - Number of bytes to move the pointer. 
	#              inSeekOrigin - Pointer movement mode. Must be one of the following 
	#                             values.
	#                  kEdsSeek_Cur     Move the stream pointer inSeekOffset bytes 
	#                                   from the current position in the stream. 
	#                  kEdsSeek_Begin   Move the stream pointer inSeekOffset bytes
	#                                   forward from the beginning of the stream. 
	#                  kEdsSeek_End     Move the stream pointer inSeekOffset bytes
	#                                   from the end of the stream. 
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	#def EdsSeek(IntPtr inStreamRef, Int64 inSeekOffset, EdsSeekOrigin inSeekOrigin):
	
	##############################################################################
	#  Function:   EdsGetPosition
	#
	#  Description:
	#       Gets the current read or write position of the stream
	#          (that is, the file position indicator).
	#
	#  Parameters:
	#       In:    inStreamRef - The reference of the stream or image.
	#      Out:    outPosition - The current stream pointer.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsGetPosition(self, inStreamRef):
		outPosition = c_uint64()
		err = self.dll.EdsGetPosition(inStreamRef, byref(outPosition))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outPosition
	
	##############################################################################
	#  Function:   EdsGetLength
	#
	#  Description:
	#      Gets the stream size.
	#
	#  Parameters:
	#       In:    inStreamRef - The reference of the stream or image.
	#      Out:    outLength - The length of the stream.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsGetLength(self, inStreamRef):
		outLength = c_uint64(0)
		err = self.dll.EdsGetLength(inStreamRef, byref(outLength))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outLength
	
	##############################################################################
	#  Function:   EdsCopyData
	#
	#  Description:
	#      Copies data from the copy source stream to the copy destination stream. 
	#      The read or write position of the data to copy is determined from 
	#          the current file read or write position of the respective stream. 
	#      After this API is executed, the read or write positions of the copy source 
	#          and copy destination streams are moved an amount corresponding to 
	#          inWriteSize in the positive direction. 
	#
	#  Parameters:
	#       In:    inStreamRef - The reference of the stream or image.
	#              inWriteSize - The number of bytes to copy.
	#      Out:    outStreamRef - The reference of the stream or image.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsCopyData(self, inStreamRef, inWriteSize):
		outStreamRef = c_void_p()
		err = self.dll.EdsCopyData(inStreamRef, c_uint64(inWriteSize), byref(outStreamRef))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outStreamRef
	
	##############################################################################
	#  Function:   EdsSetProgressCallback
	#
	#  Description:
	#      Register a progress callback function. 
	#      An event is received as notification of progress during processing that 
	#          takes a relatively long time, such as downloading files from a
	#          remote camera. 
	#      If you register the callback function, the EDSDK calls the callback
	#          function during execution or on completion of the following APIs. 
	#      This timing can be used in updating on-screen progress bars, for example.
	#
	#  Parameters:
	#       In:    inRef - The reference of the stream or image.
	#              inProgressCallback - Pointer to a progress callback function.
	#              inProgressOption - The option about progress is specified.
	#                              Must be one of the following values.
	#                         kEdsProgressOption_Done 
	#                             When processing is completed,a callback function
	#                             is called only at once.
	#                         kEdsProgressOption_Periodically
	#                             A callback function is performed periodically.
	#              inContext - Application information, passed in the argument 
	#                      when the callback function is called. Any information 
	#                      required for your program may be added. 
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	#def EdsSetProgressCallback( IntPtr inRef, EdsProgressCallback inProgressFunc, EdsProgressOption inProgressOption, IntPtr inContext):
	
	##############################################################################
	#  Function:   EdsCreateImageRef
	#
	#  Description:
	#      Creates an image object from an image file. 
	#      Without modification, stream objects cannot be worked with as images. 
	#      Thus, when extracting images from image files, 
	#          you must use this API to create image objects. 
	#      The image object created this way can be used to get image information 
	#          (such as the height and width, number of color components, and
	#           resolution), thumbnail image data, and the image data itself.
	#
	#  Parameters:
	#       In:    inStreamRef - The reference of the stream.
	#
	#       Out:    outImageRef - The reference of the image.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsCreateImageRef(self, inStreamRef):
		outImageRef = c_void_p()
		err = self.dll.EdsCreateImageRef(inStreamRef, byref(outImageRef))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outImageRef
	
	##############################################################################
	#  Function:   EdsGetImageInfo
	#
	#  Description:
	#      Gets image information from a designated image object. 
	#      Here, image information means the image width and height, 
	#          number of color components, resolution, and effective image area.
	#
	#  Parameters:
	#       In:    inImageRef - Designate the object for which to get image information. 
	#              inImageSource - Of the various image data items in the image file,
	#                  designate the type of image data representing the 
	#                  information you want to get. Designate the image as
	#                  defined in Enum EdsImageSource. 
	#
	#                      kEdsImageSrc_FullView
	#                                  The image itself (a full-sized image) 
	#                      kEdsImageSrc_Thumbnail
	#                                  A thumbnail image 
	#                      kEdsImageSrc_Preview
	#                                  A preview image
	#       Out:    outImageInfo - Stores the image data information designated 
	#                      in inImageSource. 
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsGetImageInfo(self, inImageRef, inImageSource):
		outImageInfo = EdsImageInfo()
		err = self.dll.EdsGetImageInfo(inImageRef, inImageSource, byref(outImageInfo))

		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outImageInfo

	##############################################################################
	#  Function:   EdsGetImage                         
	#
	#  Description:
	#      Gets designated image data from an image file, in the form of a
	#          designated rectangle. 
	#      Returns uncompressed results for JPEGs and processed results 
	#          in the designated pixel order (RGB, Top-down BGR, and so on) for
	#           RAW images. 
	#      Additionally, by designating the input/output rectangle, 
	#          it is possible to get reduced, enlarged, or partial images. 
	#      However, because images corresponding to the designated output rectangle 
	#          are always returned by the SDK, the SDK does not take the aspect 
	#          ratio into account. 
	#      To maintain the aspect ratio, you must keep the aspect ratio in mind 
	#          when designating the rectangle. 
	#
	#  Parameters:
	#      In:     
	#              inImageRef - Designate the image object for which to get 
	#                      the image data.
	#              inImageSource - Designate the type of image data to get from
	#                      the image file (thumbnail, preview, and so on). 
	#                      Designate values as defined in Enum EdsImageSource. 
	#              inImageType - Designate the output image type. Because
	#                      the output format of EdGetImage may only be RGB, only
	#                      kEdsTargetImageType_RGB or kEdsTargetImageType_RGB16
	#                      can be designated. 
	#                      However, image types exceeding the resolution of 
	#                      inImageSource cannot be designated. 
	#              inSrcRect - Designate the coordinates and size of the rectangle
	#                      to be retrieved (processed) from the source image. 
	#              inDstSize - Designate the rectangle size for output. 
	#
	#      Out:    
	#              outStreamRef - Designate the memory or file stream for output of
	#                      the image.
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsGetImage(self, inImageRef, inImageSource, inImageType, inSrcRect, inDstSize):
		outStreamRef = c_void_p()
		err = self.dll.EdsGetImage(inImageRef, inImageSource, inImageType, inSrcRect, inDstSize)
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outStreamRef
	
	##################### Event handler registering functions ####################
	##############################################################################
	#  Function:   EdsSetCameraAddedHandler
	#
	#  Description:
	#      Registers a callback function for when a camera is detected.
	#
	#  Parameters:
	#       In:    inCameraAddedHandler - Pointer to a callback function
	#                          called when a camera is connected physically
	#              inContext - Specifies an application-defined value to be sent to
	#                          the callback function pointed to by CallBack parameter.
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	############################################################################## 
	def EdsSetCameraAddedHandler(self, inCameraAddedHandler, inContext):
		err = self.dll.EdsSetCameraAddedHandler(inCameraAddedHandler, inContext)
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsSetPropertyEventHandler
	#              
	#  Description:
	#       Registers a callback function for receiving status 
	#          change notification events for property states on a camera.
	#
	#  Parameters:
	#       In:    inCameraRef - Designate the camera object. 
	#              inEvent - Designate one or all events to be supplemented.
	#              inPropertyEventHandler - Designate the pointer to the callback
	#                      function for receiving property-related camera events.
	#              inContext - Designate application information to be passed by 
	#                      means of the callback function. Any data needed for
	#                      your application can be passed. 
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsSetPropertyEventHandler(self, inCameraRef, inEvnet, inPropertyEventHandler, inContext):
		err = self.dll.EdsSetPropertyEventHandler(inCameraRef, inEvnet, inPropertyEventHandler, inContext)
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsSetObjectEventHandler
	#              
	#  Description:
	#       Registers a callback function for receiving status 
	#          change notification events for objects on a remote camera. 
	#      Here, object means volumes representing memory cards, files and directories, 
	#          and shot images stored in memory, in particular. 
	#
	#  Parameters:
	#       In:    inCameraRef - Designate the camera object. 
	#              inEvent - Designate one or all events to be supplemented.
	#                  To designate all events, use kEdsObjectEvent_All. 
	#              inObjectEventHandler - Designate the pointer to the callback function
	#                  for receiving object-related camera events.
	#              inContext - Passes inContext without modification,
	#                  as designated as an EdsSetObjectEventHandler argument. 
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsSetObjectEventHandler(self,  inCameraRef, inEvnet, inObjectEventHandler, inContext):
		err = self.dll.EdsSetObjectEventHandler(inCameraRef, inEvnet, inObjectEventHandler, inContext)
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:  EdsSetCameraStateEventHandler
	#              
	#  Description:
	#      Registers a callback function for receiving status 
	#          change notification events for property states on a camera.
	#
	#  Parameters:
	#       In:    inCameraRef - Designate the camera object. 
	#              inEvent - Designate one or all events to be supplemented.
	#                  To designate all events, use kEdsStateEvent_All. 
	#              inStateEventHandler - Designate the pointer to the callback function
	#                  for receiving events related to camera object states.
	#              inContext - Designate application information to be passed
	#                  by means of the callback function. Any data needed for
	#                  your application can be passed. 
	#      Out:    None
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsSetCameraStateEventHandler(self, inCameraRef, inEvnet, inStateEventHandler, inContext):
		err = self.dll.EdsSetCameraStateEventHandler(inCameraRef, inEvnet, inStateEventHandler, inContext)
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
	
	##############################################################################
	#  Function:   EdsCreateEvfImageRef         
	#  Description:
	#       Creates an object used to get the live view image data set. 
	#
	#  Parameters:
	#      In:     inStreamRef - The stream reference which opened to get EVF JPEG image.
	#      Out:    outEvfImageRef - The EVFData reference.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsCreateEvfImageRef(self, inStreamRef):
		outEvfImageRef = c_void_p()
		err = self.dll.EdsCreateEvfImageRef(inStreamRef, byref(outEvfImageRef))
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))
		return outEvfImageRef
	
	##############################################################################
	#  Function:   EdsDownloadEvfImage         
	#  Description:
	#		Downloads the live view image data set for a camera currently in live view mode.
	#		Live view can be started by using the property ID:kEdsPropertyID_Evf_OutputDevice and
	#		data:EdsOutputDevice_PC to call EdsSetPropertyData.
	#		In addition to image data, information such as zoom, focus position, and histogram data
	#		is included in the image data set. Image data is saved in a stream maintained by EdsEvfImageRef.
	#		EdsGetPropertyData can be used to get information such as the zoom, focus position, etc.
	#		Although the information of the zoom and focus position can be obtained from EdsEvfImageRef,
	#		settings are applied to EdsCameraRef.
	#
	#  Parameters:
	#      In:     inCameraRef - The Camera reference.
	#      In:     inEvfImageRef - The EVFData reference.
	#
	#  Returns:    Any of the sdk errors.
	##############################################################################
	def EdsDownloadEvfImage(self, inCameraRef, inEvfImageRef):
		err = self.dll.EdsDownloadEvfImage(inCameraRef, inEvfImageRef)
		if err != EdsErrorCodes.EDS_ERR_OK.value:
			raise Exception(self.errorFormat.format(hex(err), EdsErrorCodes(err).name))

class EdsPoint(Structure):
	_fields_ = [("x", c_int),
			 ("y", c_int)]
	
class EdsSize(Structure):
	_fields_ = [("width", c_int),
			 ("height", c_int)]

class EdsRect(Structure):
	_fields_ = [("point", EdsPoint),
			 ("size", EdsSize)]
		
class EdsFocusPoint(Structure):
	_fields_ = [("valid", c_uint),
			 ("selected", c_uint),
			 ("justFocus", c_uint),
			 ("rect", EdsRect),
			 ("reserved", c_uint)]

class EdsFocusInfo(Structure):
	_fields_ = [("imageRect", EdsRect),
			 ("pointNumber", c_uint),
			 ("executeMode", c_uint),
			 ("focusPoint", POINTER(EdsFocusPoint))]

class EdsPropertyDesc(Structure):
	_fields_ = [("form", c_int),
			 ("access", c_uint),
			 ("numElements", c_int),
			 ("propDesc", POINTER(c_int))]

class DirectoryItemInfo(Structure):
	_fields_ = [("size", c_int),
			 ("isFolder", c_bool),
			 ("groupID", c_int),
			 ("option", c_int),
			 ("szFileName", c_char*256),
			 ("format", c_int)]

class EdsCapacity(Structure):
	_fields_ = [("numberOfFreeClusters", c_int),
				("bytesPerSector", c_int),
				("reset", c_int)]

class EdsImageInfo(Structure):
	_fields_ = [("width", c_uint),
			 ("height", c_uint),
			 ("numOfComponents", c_uint),
			 ("componentDepth", c_uint),
			 ("effectiveRect", EdsRect),
			 ("reserved", c_uint)]

class EdsDeviceInfo(Structure):
	_fields_ = [("szPortName", c_char*256),
			("szDeviceDescription", c_char*256),
			("deviceSubType", c_uint),
			("reserved", c_uint)]

class EdsVolumeInfo(Structure):
	_fields_ = [("storageType", c_uint),
			 ("edsAccess", c_uint),
			 ("maxCapacity", c_uint64),
			 ("freeSpaceInBytes", c_uint64),
			 ("szVolumeLabel", c_char*256),
			 ("volumeRef", c_void_p)]

	@property
	def storage_type(self):
		return EdsStorageType(self.storageType)

	@property
	def access(self):
		return EdsAccess(self.edsAccess)

	@property
	def label(self):
		return self.szVolumeLabel.decode('utf-8')

	@property
	def ref(self):
		return c_void_p(self.volumeRef)

	@ref.setter
	def ref(self, value):
		self.volumeRef = value

class EvfDataSet(Structure):
	_fields_ = [
		('stream', c_void_p),
		('zoom', c_uint),
		('zoomRect', EdsRect),
		('imagePosition', EdsPoint),
		('sizeJpgLarge', EdsSize)]


#################### Enum Classes ####################
class EdsDataType(Enum):
	Unknown     = 0    
	Bool        = 1   
	String      = 2   
	Int8        = 3   
	UInt8       = 6  
	Int16       = 4    
	UInt16      = 7    
	Int32       = 8    
	UInt32      = 9    
	Int64       = 10    
	UInt64      = 11   
	Float       = 12
	Double      = 13
	ByteBlock   = 14   
	Rational    = 20   
	Point       = 21  
	Rect        = 22
	Time        = 23
	
	Bool_Array   = 30    
	Int8_Array   = 31    
	Int16_Array  = 32    
	Int32_Array  = 33    
	UInt8_Array  = 34    
	UInt16_Array = 35    
	UInt32_Array = 36     
	Rational_Array = 37      
	
	FocusInfo		= 101 

class EdsEvfAf(Enum):
	CameraCommand_EvfAf_OFF	= 0
	CameraCommand_EvfAf_ON	= 1

class EdsShutterButton(Enum):
	CameraCommand_ShutterButton_OFF					= 0x00000000
	CameraCommand_ShutterButton_Halfway				= 0x00000001
	CameraCommand_ShutterButton_Completely			= 0x00000003
	CameraCommand_ShutterButton_Halfway_NonAF		= 0x00010001
	CameraCommand_ShutterButton_Completely_NonAF	= 0x00010003

class EdsSeekOrigin(Enum):
	Cur = 0

class EdsAccess(Enum):
	Read = 0
	Write = 1
	ReadWrite = 2
	Error = 0xFFFFFFFF

class EdsFileCreateDisposition(Enum):
	CreateNew = 0

class EdsTargetImageType(Enum):
	Unknown = 0x00000000
	Jpeg    = 0x00000001
	TIFF    = 0x00000007
	TIFF16  = 0x00000008
	RGB     = 0x00000009
	RGB16   = 0x0000000A

class EdsImageSource(Enum):
	FullView = 0
	Thumbnail = 1  
	Preview = 2   
	RAWThumbnail = 3
	RAWFullView = 4

class EdsProgrssOption(Enum):
	NoReport = 0

class EdsFileAttribute(Enum):
	Normal     = 0x00000000
	ReadOnly   = 0x00000001
	Hidden     = 0x00000002
	System     = 0x00000004
	Archive    = 0x00000020

class EdsSaveTo(Enum): 
	Camera  =  1
	Host    =  2
	Both    =  3
	
class EdsStorageType(Enum): 
	Non = 0
	CF  = 1
	SD  = 2

class EdsTransferOption(Enum):
	ByDirectTransfer    = 1
	ByRelease           = 2
	ToDesktop           = 0x00000100

class EdsMirrorLockupState(Enum):
	Disable = 0
	Enable = 1
	DuringShooting = 2
	
class EdsMirrorUpSetting(Enum):
	Off = 0
	On = 1

class EdsEvfAFMode(Enum):
	Evf_AFMode_Quick    = 0
	Evf_AFMode_Live     = 1
	Evf_AFMode_LiveFace = 2
	Evf_AFMode_LiveMulti = 3
	Evf_AFMode_LiveZone = 4
	Evf_AFMode_LiveCatchAF = 9
	Evf_AFMode_LiveSpotAF = 10

class EdsStroboMode(Enum):
	kEdsStroboModeInternal = 0
	kEdsStroboModeExternalETTL = 1
	kEdsStroboModeExternalATTL = 2
	kEdsStroboModeExternalTTL = 3
	kEdsStroboModeExternalAuto = 4
	kEdsStroboModeExternalManual = 5
	kEdsStroboModeManual = 6

class EdsETTL2Mode(Enum):
	kEdsETTL2ModeEvaluative		= 0
	kEdsETTL2ModeAverage		= 1

class DcStrobe(Enum):
	DcStrobeAuto         = 0
	DcStrobeOn			 = 1
	DcStrobeSlowsynchro	 = 2
	DcStrobeOff			 = 3

class DcLensBarrelState(Enum):
	DcLensBarrelStateInner = 0
	DcLensBarrelStateOuter = 1

class DcRemoteShootingMode(Enum):
	DcRemoteShootingModeStop	 = 0
	DcRemoteShootingModeStart	 = 1

class ImageQuality(Enum):
	## Jpeg Only 
	EdsImageQuality_LJ = 0x0010ff0f		## Jpeg Large 
	EdsImageQuality_M1J = 0x0510ff0f	## Jpeg Middle1 
	EdsImageQuality_M2J = 0x0610ff0f	## Jpeg Middle2 
	EdsImageQuality_SJ = 0x0210ff0f		## Jpeg Small 
	EdsImageQuality_LJF = 0x0013ff0f	## Jpeg Large Fine 
	EdsImageQuality_LJN = 0x0012ff0f	## Jpeg Large Normal 
	EdsImageQuality_MJF = 0x0113ff0f	## Jpeg Middle Fine 
	EdsImageQuality_MJN = 0x0112ff0f	## Jpeg Middle Normal 
	EdsImageQuality_SJF = 0x0213ff0f	## Jpeg Small Fine 
	EdsImageQuality_SJN = 0x0212ff0f	## Jpeg Small Normal 
	EdsImageQuality_S1JF = 0x0E13ff0f	## Jpeg Small1 Fine 
	EdsImageQuality_S1JN = 0x0E12ff0f	## Jpeg Small1 Normal 
	EdsImageQuality_S2JF = 0x0F13ff0f	## Jpeg Small2 
	EdsImageQuality_S3JF = 0x1013ff0f	## Jpeg Small3 

	## RAW + Jpeg 
	EdsImageQuality_LR = 0x0064ff0f	## RAW 
	EdsImageQuality_LRLJF = 0x00640013	## RAW + Jpeg Large Fine 
	EdsImageQuality_LRLJN = 0x00640012	## RAW + Jpeg Large Normal 
	EdsImageQuality_LRMJF = 0x00640113	## RAW + Jpeg Middle Fine 
	EdsImageQuality_LRMJN = 0x00640112	## RAW + Jpeg Middle Normal 
	EdsImageQuality_LRSJF = 0x00640213	## RAW + Jpeg Small Fine 
	EdsImageQuality_LRSJN = 0x00640212	## RAW + Jpeg Small Normal 
	EdsImageQuality_LRS1JF = 0x00640E13	## RAW + Jpeg Small1 Fine 
	EdsImageQuality_LRS1JN = 0x00640E12	## RAW + Jpeg Small1 Normal 
	EdsImageQuality_LRS2JF = 0x00640F13	## RAW + Jpeg Small2 
	EdsImageQuality_LRS3JF = 0x00641013	## RAW + Jpeg Small3 
	EdsImageQuality_LRLJ = 0x00640010	## RAW + Jpeg Large 
	EdsImageQuality_LRM1J = 0x00640510	## RAW + Jpeg Middle1 
	EdsImageQuality_LRM2J = 0x00640610	## RAW + Jpeg Middle2 
	EdsImageQuality_LRSJ = 0x00640210	## RAW + Jpeg Small 

	## MRAW(SRAW1) + Jpeg 
	EdsImageQuality_MR = 0x0164ff0f	## MRAW(SRAW1) 
	EdsImageQuality_MRLJF = 0x01640013	## MRAW(SRAW1) + Jpeg Large Fine 
	EdsImageQuality_MRLJN = 0x01640012	## MRAW(SRAW1) + Jpeg Large Normal 
	EdsImageQuality_MRMJF = 0x01640113	## MRAW(SRAW1) + Jpeg Middle Fine 
	EdsImageQuality_MRMJN = 0x01640112	## MRAW(SRAW1) + Jpeg Middle Normal 
	EdsImageQuality_MRSJF = 0x01640213	## MRAW(SRAW1) + Jpeg Small Fine 
	EdsImageQuality_MRSJN = 0x01640212	## MRAW(SRAW1) + Jpeg Small Normal 
	EdsImageQuality_MRS1JF = 0x01640E13	## MRAW(SRAW1) + Jpeg Small1 Fine 
	EdsImageQuality_MRS1JN = 0x01640E12	## MRAW(SRAW1) + Jpeg Small1 Normal 
	EdsImageQuality_MRS2JF = 0x01640F13	## MRAW(SRAW1) + Jpeg Small2 
	EdsImageQuality_MRS3JF = 0x01641013	## MRAW(SRAW1) + Jpeg Small3 
	EdsImageQuality_MRLJ = 0x01640010	## MRAW(SRAW1) + Jpeg Large 
	EdsImageQuality_MRM1J = 0x01640510	## MRAW(SRAW1) + Jpeg Middle1 
	EdsImageQuality_MRM2J = 0x01640610	## MRAW(SRAW1) + Jpeg Middle2 
	EdsImageQuality_MRSJ = 0x01640210	## MRAW(SRAW1) + Jpeg Small 

	## SRAW(SRAW2) + Jpeg 
	EdsImageQuality_SR = 0x0264ff0f	## SRAW(SRAW2) 
	EdsImageQuality_SRLJF = 0x02640013	## SRAW(SRAW2) + Jpeg Large Fine 
	EdsImageQuality_SRLJN = 0x02640012	## SRAW(SRAW2) + Jpeg Large Normal 
	EdsImageQuality_SRMJF = 0x02640113	## SRAW(SRAW2) + Jpeg Middle Fine 
	EdsImageQuality_SRMJN = 0x02640112	## SRAW(SRAW2) + Jpeg Middle Normal 
	EdsImageQuality_SRSJF = 0x02640213	## SRAW(SRAW2) + Jpeg Small Fine 
	EdsImageQuality_SRSJN = 0x02640212	## SRAW(SRAW2) + Jpeg Small Normal 
	EdsImageQuality_SRS1JF = 0x02640E13	## SRAW(SRAW2) + Jpeg Small1 Fine 
	EdsImageQuality_SRS1JN = 0x02640E12	## SRAW(SRAW2) + Jpeg Small1 Normal 
	EdsImageQuality_SRS2JF = 0x02640F13	## SRAW(SRAW2) + Jpeg Small2 
	EdsImageQuality_SRS3JF = 0x02641013	## SRAW(SRAW2) + Jpeg Small3 
	EdsImageQuality_SRLJ = 0x02640010	## SRAW(SRAW2) + Jpeg Large 
	EdsImageQuality_SRM1J = 0x02640510	## SRAW(SRAW2) + Jpeg Middle1 
	EdsImageQuality_SRM2J = 0x02640610	## SRAW(SRAW2) + Jpeg Middle2 
	EdsImageQuality_SRSJ = 0x02640210	## SRAW(SRAW2) + Jpeg Small 

	## CRAW + Jpeg 
	EdsImageQuality_CR		=	0x0063ff0f	## CRAW 
	EdsImageQuality_CRLJF	=	0x00630013	## CRAW + Jpeg Large Fine 
	EdsImageQuality_CRMJF	=	0x00630113	## CRAW + Jpeg Middle Fine  
	EdsImageQuality_CRM1JF	=	0x00630513	## CRAW + Jpeg Middle1 Fine  
	EdsImageQuality_CRM2JF	=	0x00630613	## CRAW + Jpeg Middle2 Fine  
	EdsImageQuality_CRSJF	=	0x00630213	## CRAW + Jpeg Small Fine  
	EdsImageQuality_CRS1JF	=	0x00630E13	## CRAW + Jpeg Small1 Fine  
	EdsImageQuality_CRS2JF	=	0x00630F13	## CRAW + Jpeg Small2 Fine  
	EdsImageQuality_CRS3JF	=	0x00631013	## CRAW + Jpeg Small3 Fine  
	EdsImageQuality_CRLJN	=	0x00630012	## CRAW + Jpeg Large Normal 
	EdsImageQuality_CRMJN	=	0x00630112	## CRAW + Jpeg Middle Normal 
	EdsImageQuality_CRM1JN	=	0x00630512	## CRAW + Jpeg Middle1 Normal 
	EdsImageQuality_CRM2JN	=	0x00630612	## CRAW + Jpeg Middle2 Normal 
	EdsImageQuality_CRSJN	=	0x00630212	## CRAW + Jpeg Small Normal 
	EdsImageQuality_CRS1JN	=	0x00630E12	## CRAW + Jpeg Small1 Normal 
	EdsImageQuality_CRLJ	=	0x00630010	## CRAW + Jpeg Large 
	EdsImageQuality_CRM1J	=	0x00630510	## CRAW + Jpeg Middle1 
	EdsImageQuality_CRM2J	=	0x00630610	## CRAW + Jpeg Middle2 
	EdsImageQuality_CRSJ	=	0x00630210	## CRAW + Jpeg Small 
	EdsImageQuality_Unknown =	0xffffffff


class EdsErrorCodes(Enum):
	######################### ED-SDK Error Code Masks #########################
	EDS_ISSPECIFIC_MASK =                                 0x80000000
	EDS_COMPONENTID_MASK =                                0x7F000000
	EDS_RESERVED_MASK =                                   0x00FF0000
	EDS_ERRORID_MASK =                                    0x0000FFFF
	
	######################## ED-SDK Base Component IDs ########################
	EDS_CMP_ID_CLIENT_COMPONENTID =                       0x01000000
	EDS_CMP_ID_LLSDK_COMPONENTID =                        0x02000000
	EDS_CMP_ID_HLSDK_COMPONENTID =                        0x03000000
	
	####################### ED-SDK Functin Success Code #######################
	EDS_ERR_OK =                                          0x00000000
	
	######################### ED-SDK Generic Error IDs ########################
	## Miscellaneous errors 
	EDS_ERR_UNIMPLEMENTED =                               0x00000001  
	EDS_ERR_INTERNAL_ERROR =                              0x00000002
	EDS_ERR_MEM_ALLOC_FAILED =                            0x00000003
	EDS_ERR_MEM_FREE_FAILED =                             0x00000004
	EDS_ERR_OPERATION_CANCELLED =                         0x00000005
	EDS_ERR_INCOMPATIBLE_VERSION =                        0x00000006
	EDS_ERR_NOT_SUPPORTED =                               0x00000007
	EDS_ERR_UNEXPECTED_EXCEPTION =                        0x00000008
	EDS_ERR_PROTECTION_VIOLATION =                        0x00000009
	EDS_ERR_MISSING_SUBCOMPONENT =                        0x0000000A
	EDS_ERR_SELECTION_UNAVAILABLE =                       0x0000000B
	
	## File errors 
	EDS_ERR_FILE_IO_ERROR =                               0x00000020
	EDS_ERR_FILE_TOO_MANY_OPEN =                          0x00000021
	EDS_ERR_FILE_NOT_FOUND =                              0x00000022
	EDS_ERR_FILE_OPEN_ERROR =                             0x00000023
	EDS_ERR_FILE_CLOSE_ERROR =                            0x00000024
	EDS_ERR_FILE_SEEK_ERROR =                             0x00000025
	EDS_ERR_FILE_TELL_ERROR =                             0x00000026
	EDS_ERR_FILE_READ_ERROR =                             0x00000027
	EDS_ERR_FILE_WRITE_ERROR =                            0x00000028
	EDS_ERR_FILE_PERMISSION_ERROR =                       0x00000029
	EDS_ERR_FILE_DISK_FULL_ERROR =                        0x0000002A
	EDS_ERR_FILE_ALREADY_EXISTS =                         0x0000002B
	EDS_ERR_FILE_FORMAT_UNRECOGNIZED =                    0x0000002C
	EDS_ERR_FILE_DATA_CORRUPT =                           0x0000002D
	EDS_ERR_FILE_NAMING_NA =                              0x0000002E
	
	## Directory errors           
	EDS_ERR_DIR_NOT_FOUND =                               0x00000040
	EDS_ERR_DIR_IO_ERROR =                                0x00000041
	EDS_ERR_DIR_ENTRY_NOT_FOUND =                         0x00000042
	EDS_ERR_DIR_ENTRY_EXISTS =                            0x00000043
	EDS_ERR_DIR_NOT_EMPTY =                               0x00000044
	
	## Property errors 
	EDS_ERR_PROPERTIES_UNAVAILABLE =                      0x00000050
	EDS_ERR_PROPERTIES_MISMATCH =                         0x00000051
	EDS_ERR_PROPERTIES_NOT_LOADED =                       0x00000053
	
	## Function Parameter errors      
	EDS_ERR_INVALID_PARAMETER =                           0x00000060
	EDS_ERR_INVALID_HANDLE =                              0x00000061
	EDS_ERR_INVALID_POINTER =                             0x00000062
	EDS_ERR_INVALID_INDEX =                               0x00000063
	EDS_ERR_INVALID_LENGTH =                              0x00000064
	EDS_ERR_INVALID_FN_POINTER =                          0x00000065
	EDS_ERR_INVALID_SORT_FN =                             0x00000066
	
	## Device errors 
	EDS_ERR_DEVICE_NOT_FOUND =                            0x00000080
	EDS_ERR_DEVICE_BUSY =                                 0x00000081
	EDS_ERR_DEVICE_INVALID =                              0x00000082
	EDS_ERR_DEVICE_EMERGENCY =                            0x00000083
	EDS_ERR_DEVICE_MEMORY_FULL =                          0x00000084
	EDS_ERR_DEVICE_INTERNAL_ERROR =                       0x00000085
	EDS_ERR_DEVICE_INVALID_PARAMETER =                    0x00000086
	EDS_ERR_DEVICE_NO_DISK =                              0x00000087
	EDS_ERR_DEVICE_DISK_ERROR =                           0x00000088
	EDS_ERR_DEVICE_CF_GATE_CHANGED =                      0x00000089
	EDS_ERR_DEVICE_DIAL_CHANGED =                         0x0000008A
	EDS_ERR_DEVICE_NOT_INSTALLED =                        0x0000008B
	EDS_ERR_DEVICE_STAY_AWAKE =                           0x0000008C
	EDS_ERR_DEVICE_NOT_RELEASED =                         0x0000008D
	
	## Stream errors 
	EDS_ERR_STREAM_IO_ERROR =                             0x000000A0
	EDS_ERR_STREAM_NOT_OPEN =                             0x000000A1
	EDS_ERR_STREAM_ALREADY_OPEN =                         0x000000A2
	EDS_ERR_STREAM_OPEN_ERROR =                           0x000000A3
	EDS_ERR_STREAM_CLOSE_ERROR =                          0x000000A4
	EDS_ERR_STREAM_SEEK_ERROR =                           0x000000A5
	EDS_ERR_STREAM_TELL_ERROR =                           0x000000A6
	EDS_ERR_STREAM_READ_ERROR =                           0x000000A7
	EDS_ERR_STREAM_WRITE_ERROR =                          0x000000A8
	EDS_ERR_STREAM_PERMISSION_ERROR =                     0x000000A9
	EDS_ERR_STREAM_COULDNT_BEGIN_THREAD =                 0x000000AA
	EDS_ERR_STREAM_BAD_OPTIONS =                          0x000000AB
	EDS_ERR_STREAM_END_OF_STREAM =                        0x000000AC
	
	## Communications errors 
	EDS_ERR_COMM_PORT_IS_IN_USE =                         0x000000C0
	EDS_ERR_COMM_DISCONNECTED =                           0x000000C1
	EDS_ERR_COMM_DEVICE_INCOMPATIBLE =                    0x000000C2
	EDS_ERR_COMM_BUFFER_FULL =                            0x000000C3
	EDS_ERR_COMM_USB_BUS_ERR =                            0x000000C4
	
	## Lock/Unlock 
	EDS_ERR_USB_DEVICE_LOCK_ERROR =                       0x000000D0
	EDS_ERR_USB_DEVICE_UNLOCK_ERROR =                     0x000000D1
	
	## STI/WIA 
	EDS_ERR_STI_UNKNOWN_ERROR =                           0x000000E0
	EDS_ERR_STI_INTERNAL_ERROR =                          0x000000E1
	EDS_ERR_STI_DEVICE_CREATE_ERROR =                     0x000000E2
	EDS_ERR_STI_DEVICE_RELEASE_ERROR =                    0x000000E3
	EDS_ERR_DEVICE_NOT_LAUNCHED =                         0x000000E4
	
	EDS_ERR_ENUM_NA =                                     0x000000F0
	EDS_ERR_INVALID_FN_CALL =                             0x000000F1
	EDS_ERR_HANDLE_NOT_FOUND =                            0x000000F2
	EDS_ERR_INVALID_ID =                                  0x000000F3
	EDS_ERR_WAIT_TIMEOUT_ERROR =                          0x000000F4
	
	## PTP 
	EDS_ERR_SESSION_NOT_OPEN =                            0x00002003
	EDS_ERR_INVALID_TRANSACTIONID =                       0x00002004
	EDS_ERR_INCOMPLETE_TRANSFER =                         0x00002007
	EDS_ERR_INVALID_STRAGEID =                            0x00002008
	EDS_ERR_DEVICEPROP_NOT_SUPPORTED =                    0x0000200A
	EDS_ERR_INVALID_OBJECTFORMATCODE =                    0x0000200B
	EDS_ERR_SELF_TEST_FAILED =                            0x00002011
	EDS_ERR_PARTIAL_DELETION =                            0x00002012
	EDS_ERR_SPECIFICATION_BY_FORMAT_UNSUPPORTED =         0x00002014
	EDS_ERR_NO_VALID_OBJECTINFO =                         0x00002015
	EDS_ERR_INVALID_CODE_FORMAT =                         0x00002016
	EDS_ERR_UNKNOWN_VENDER_CODE =                         0x00002017
	EDS_ERR_CAPTURE_ALREADY_TERMINATED =                  0x00002018
	EDS_ERR_INVALID_PARENTOBJECT =                        0x0000201A
	EDS_ERR_INVALID_DEVICEPROP_FORMAT =                   0x0000201B
	EDS_ERR_INVALID_DEVICEPROP_VALUE =                    0x0000201C
	EDS_ERR_SESSION_ALREADY_OPEN =                        0x0000201E
	EDS_ERR_TRANSACTION_CANCELLED =                       0x0000201F
	EDS_ERR_SPECIFICATION_OF_DESTINATION_UNSUPPORTED =    0x00002020
	EDS_ERR_UNKNOWN_COMMAND =                             0x0000A001
	EDS_ERR_OPERATION_REFUSED =                           0x0000A005
	EDS_ERR_LENS_COVER_CLOSE =                            0x0000A006
	EDS_ERR_LOW_BATTERY =									0x0000A101
	EDS_ERR_OBJECT_NOTREADY =								0x0000A102
	
	## Capture Error 
	EDS_ERR_TAKE_PICTURE_AF_NG =							0x00008D01
	EDS_ERR_TAKE_PICTURE_RESERVED =						0x00008D02
	EDS_ERR_TAKE_PICTURE_MIRROR_UP_NG =					0x00008D03
	EDS_ERR_TAKE_PICTURE_SENSOR_CLEANING_NG =				0x00008D04
	EDS_ERR_TAKE_PICTURE_SILENCE_NG =						0x00008D05
	EDS_ERR_TAKE_PICTURE_NO_CARD_NG =						0x00008D06
	EDS_ERR_TAKE_PICTURE_CARD_NG =						0x00008D07
	EDS_ERR_TAKE_PICTURE_CARD_PROTECT_NG =				0x00008D08
	
	EDS_ERR_LAST_GENERIC_ERROR_PLUS_ONE =                 0x000000F5

	###########################################################################
