import wx
from enums import Axis
from Canon.EDSDKLib import *
import util

class ControllerPanel(wx.Panel):
    def __init__(self, parent, aui_manager, *args, **kwargs):
        super(ControllerPanel, self).__init__(parent, style = wx.BORDER_SUNKEN)
        self.parent = parent
        self.auiManager = aui_manager
        self.visualizer_panel = self.auiManager.GetPane('Visualizer').window
        self.InitPanel()
        self.canvas = ""

    def InitPanel(self):
        vboxLeft = wx.BoxSizer(wx.VERTICAL)

        ## header font
        self.font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(15)

        ## Positioning section starts
        positioning_vbox = self.InitPositioning()
        vboxLeft.Add(positioning_vbox, 0.5, flag = wx.LEFT|wx.TOP, border = 5)

        ## Circular path generator section
        ##circular_path_hbox = self.InitCircularPathGenerator()
        ##vboxLeft.Add(circular_path_hbox, 0.5, flag = wx.LEFT|wx.TOP, border = 5)

        ## camera control section
        cam_control_vbox = self.InitCamControl()
        vboxLeft.Add(cam_control_vbox, 0.5, flag = wx.LEFT|wx.TOP, border = 5)

        self.SetSizerAndFit(vboxLeft)

    def InitPositioning(self):
        ## LAYOUT

	    ####################################################################################################
        ##                                                                                                ##
        ## vbox        ---------------------------------------------------------------------------------- ##
        ## Positioning | self.hbox  ------------------------------------------------------------------- | ##
	    ##             | CameraInfo |                                                                 | | ##
	    ##             |            ------------------------------------------------------------------- | ##
	    ##             | Positioning                                                                    | ##
	    ##             | hboxTop ---------------------------------------------------------------------- | ##
        ##             |         | -----------  ------------------  --------------------  ----------- | | ##
        ##             |         | | camList |  |   Set Center   |  |Refresh From COPIS|  |  slider | | | ##
        ##             |         | -----------  ------------------  --------------------  ----------- | | ##
        ##             |         ---------------------------------------------------------------------- | ##
        ##             | hbox  ------------------------------------------------------------------------ | ##
        ##             | Xyzpt | vbox ----------------------------- vbox ---------------------------- | | ##
        ##             |       | Xyz  | XYZ Increment Size        | Pt   | PT Increment Size        | | | ##
        ##             |       |      | hboxXyz ----------------- |      | hboxPt ----------------- | | | ##
        ##             |       |      | Size    |  ________ mm  | |      | Size   |  ________ dd  | | | | ##
        ##             |       |      |         ----------------- |      |        ----------------- | | | ##
        ##             |       |      -----------------------------      ---------------------------- | | ##
	    ##             |       | hbox  ----------------------------                                   | | ##
	    ##             |       | YzInc |         Y+          Z+   |                   T+              | | ##
	    ##             |       |       ----------------------------                                   | | ##
	    ##             |       | hboxX ---------------------------- hboxP --------------------------- | | ##
	    ##             |       |       |    X-          X+        |       |     P-     c      P+    | | | ##
	    ##             |       |       ----------------------------       --------------------------- | | ##
	    ##             |       | hbox  ----------------------------                                   | | ##
	    ##             |       | YzDec |         Y-          Z-   |                   T-              | | ##
	    ##             |       |       ----------------------------                                   | | ##
	    ##             |       ------------------------------------------------------------------------ | ##
	    ##             | hbox  ------------------------------------------------------------------------ | ##
	    ##             | Extra |  Enable Motors   Disable Motors   Record Position   Home   Set Home  | | ##
	    ##             |       ------------------------------------------------------------------------ | ##
        ##             ---------------------------------------------------------------------------------- ##
        ##                                                                                                ##
        ####################################################################################################
        vboxPositioning = wx.BoxSizer(wx.VERTICAL)
        self.hboxCameraInfo = wx.BoxSizer()
        vboxPositioning.Add(self.hboxCameraInfo, 0.5, wx.EXPAND)

        positionLabel = wx.StaticText(self, wx.ID_ANY, label = 'Positioning', style = wx.ALIGN_LEFT)
        positionLabel.SetFont(self.font)
        vboxPositioning.Add(positionLabel, 0.5, flag = wx.BOTTOM|wx.TOP, border = 10)

        hboxTop = wx.BoxSizer()
        camLabel = wx.StaticText(self, wx.ID_ANY, label="Camera: ", style=wx.ALIGN_LEFT)
        hboxTop.Add(camLabel)
        self.masterCombo = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        self.masterCombo.Bind(wx.EVT_COMBOBOX, self.OnMasterCombo)
        hboxTop.Add(self.masterCombo)
        ## self.setCenterBtn = wx.Button(self, wx.ID_ANY, label = 'Set Center')
        ## hboxTop.Add(self.setCenterBtn, 1, flag = wx.LEFT, border = 5)

        self.refreshBtn = wx.Button(self, wx.ID_ANY, label = 'Refresh')
        self.refreshBtn.Bind(wx.EVT_BUTTON, self.onRefresh)
        hboxTop.Add(self.refreshBtn)
        hboxTop.AddStretchSpacer()

        self.createVCamBtn = wx.Button(self, wx.ID_ANY, label = "Create 3D camera")
        self.createVCamBtn.Bind(wx.EVT_BUTTON, self.onCreateVirtualCam)
        hboxTop.Add(self.createVCamBtn)
        vboxPositioning.Add(hboxTop, 0.5 , flag = wx.LEFT|wx.BOTTOM|wx.EXPAND, border = 15)

        hboxXyzbc = wx.BoxSizer()
        vboxXyz = wx.BoxSizer(wx.VERTICAL)
        xyzLabel = wx.StaticText(self, wx.ID_ANY, label = 'XYZ Increment Size', style = wx.ALIGN_LEFT)
        vboxXyz.Add(xyzLabel, 1, flag = wx.BOTTOM, border = 10)

        hboxXyzSize = wx.BoxSizer()
        self.xyzSc = wx.SpinCtrl(self, value = '0')
        self.xyzSc.SetRange(0, 100)
        hboxXyzSize.Add(self.xyzSc, 1, flag = wx.RIGHT|wx.BOTTOM, border = 5)
        mmLabel = wx.StaticText(self, wx.ID_ANY, label = 'mm', style = wx.ALIGN_LEFT)
        hboxXyzSize.Add(mmLabel)
        vboxXyz.Add(hboxXyzSize)

        hboxYzInc = wx.BoxSizer()
        self.yiBtn = wx.Button(self, wx.ID_ANY, label = 'Y+')
        self.yiBtn.axis = Axis.Y
        self.yiBtn.direction = Axis.Plus
        hboxYzInc.Add(self.yiBtn, 1, flag = wx.LEFT|wx.RIGHT, border = 55)
        self.yiBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.ziBtn = wx.Button(self, wx.ID_ANY, label = 'Z+')
        self.ziBtn.axis = Axis.Z
        self.ziBtn.direction = Axis.Plus
        hboxYzInc.Add(self.ziBtn)
        self.ziBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxXyz.Add(hboxYzInc)

        hboxX = wx.BoxSizer()
        self.xrBtn = wx.Button(self, wx.ID_ANY, label = 'X-')
        self.xrBtn.axis = Axis.X
        self.xrBtn.direction = Axis.Minus
        hboxX.Add(self.xrBtn)
        self.xrBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.xiBtn = wx.Button(self, wx.ID_ANY, label = 'X+')
        self.xiBtn.axis = Axis.X
        self.xiBtn.direction = Axis.Plus
        hboxX.Add(self.xiBtn, 1, flag = wx.LEFT, border = 20)
        self.xiBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxXyz.Add(hboxX)

        hboxYzDec = wx.BoxSizer()
        self.yrBtn = wx.Button(self, wx.ID_ANY, label = 'Y-')
        self.yrBtn.axis = Axis.Y
        self.yrBtn.direction = Axis.Minus
        hboxYzDec.Add(self.yrBtn, 1, flag = wx.LEFT|wx.RIGHT, border = 55)
        self.yrBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.zrBtn = wx.Button(self, wx.ID_ANY, label = 'Z-')
        self.zrBtn.axis = Axis.Z
        self.zrBtn.direction = Axis.Minus
        hboxYzDec.Add(self.zrBtn)
        self.zrBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxXyz.Add(hboxYzDec)
        hboxXyzbc.Add(vboxXyz)

        vboxBc = wx.BoxSizer(wx.VERTICAL)
        bcLabel = wx.StaticText(self, wx.ID_ANY, label = 'BC Increment Size', style = wx.ALIGN_LEFT)
        vboxBc.Add(bcLabel, 1, flag = wx.BOTTOM, border = 10)

        hboxBcSize = wx.BoxSizer()
        self.bcSc = wx.SpinCtrl(self, value = '0')
        self.bcSc.SetRange(0, 100)
        hboxBcSize.Add(self.bcSc, 1, flag = wx.RIGHT|wx.BOTTOM, border = 5)
        ddLabel = wx.StaticText(self, wx.ID_ANY, label = 'dd', style = wx.ALIGN_LEFT)
        hboxBcSize.Add(ddLabel)
        vboxBc.Add(hboxBcSize)
        self.ciBtn = wx.Button(self, wx.ID_ANY, label = 'T+')
        self.ciBtn.axis = Axis.C
        self.ciBtn.direction = Axis.Plus
        vboxBc.Add(self.ciBtn, 1, flag = wx.LEFT, border = 88)
        self.ciBtn.Bind(wx.EVT_BUTTON, self.OnMove)

        hboxB = wx.BoxSizer()
        self.brBtn = wx.Button(self, wx.ID_ANY, label = 'P-')
        self.brBtn.axis = Axis.B
        self.brBtn.direction = Axis.Minus
        hboxB.Add(self.brBtn)
        self.brBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.cBtn = wx.Button(self, wx.ID_ANY, label = 'center')
        hboxB.Add(self.cBtn)
        self.cBtn.Bind(wx.EVT_BUTTON, self.OnFocusCenter)
        self.biBtn = wx.Button(self, wx.ID_ANY, label = 'P+')
        self.biBtn.axis = Axis.B
        self.biBtn.direction = Axis.Plus
        hboxB.Add(self.biBtn)
        self.biBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxBc.Add(hboxB)
        self.crBtn = wx.Button(self, wx.ID_ANY, label = 'T-')
        self.crBtn.axis = Axis.C
        self.crBtn.direction = Axis.Minus
        vboxBc.Add(self.crBtn, 1, flag = wx.LEFT, border = 88)
        self.crBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        hboxXyzbc.Add(vboxBc)

        vboxPositioning.Add(hboxXyzbc, 1, flag = wx.LEFT, border = 15)

        return vboxPositioning


    def InitCamControl(self):
        ## LAYOUT

        ##########################################################################################################
        ##                                                                                                      ##
        ## hbox ----------------------------------------------------------------------------------------------- ##
        ##      | vbox1  ----------------------------------  vbox2 ------------------------------------------ | ##
        ##      |        | Z Stack Generator              |        |  Camera Control                        | | ##
    	##      |        | hbox  ------------------------ |        |  hbox   ------------------------------ | | ##
	    ##      |        | Focal | No.Focal Steps: ____ | |        |  Remote | Remote   vboxAF  --------- | | | ##
	    ##      |        | Steps ------------------------ |        |         | Shutter  Shutter |  A/F  | | | | ##
	    ##      |        | hbox   -------------------     |        |         |                  |Shutter| | | | ##
	    ##      |        | StartZ | Start Z: ___    |     |        |         |                  --------- | | | ##
	    ##      |        |        -------------------     |        |         ------------------------------ | | ##
	    ##      |        | hbox ------------------------- |        | hboxUSB ---------------------------    | | ##
	    ##      |        | ZInc | Z Increment (mm): ____| |        |         | USB/PTP  vboxF -------- |    | | ##
	    ##      |        |      ------------------------- |        |         |                |  F-  | |    | | ##
	    ##      |        | ------------                   |        |         |                |  F+  | |    | | ##
	    ##      |        | | Generate |                   |        |         |                -------- |    | | ##
	    ##      |        | ------------                   |        |         ---------------------------    | | ##
	    ##      |        ----------------------------------        ------------------------------------------ | ##
        ##      ----------------------------------------------------------------------------------------------- ##
        ##                                                                                                      ##
        ##########################################################################################################
        vbox = wx.BoxSizer(wx.VERTICAL)
        cameraControlLabel = wx.StaticText(self, wx.ID_ANY, label = 'Camera Control', style = wx.ALIGN_LEFT)
        cameraControlLabel.SetFont(self.font)
        vbox.Add(cameraControlLabel, 0, flag = wx.TOP | wx.BOTTOM, border = 10)

        hbox = wx.BoxSizer()
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.remoteRb = wx.RadioButton(self, label = 'Remote Shutter', style=wx.RB_GROUP)
        vbox1.Add(self.remoteRb)

        vboxAFShutter = wx.BoxSizer()
        self.afBtn = wx.Button(self, wx.ID_ANY, label = 'A/F')
        vboxAFShutter.Add(self.afBtn)
        self.shutterBtn = wx.Button(self, wx.ID_ANY, label = 'Shutter')
        vboxAFShutter.Add(self.shutterBtn)
        vbox1.Add(vboxAFShutter, 1, flag = wx.LEFT, border = 5)

        self.usbRb = wx.RadioButton(self, label = 'USB')
        vbox1.Add(self.usbRb)
        self.Bind(wx.EVT_RADIOBUTTON, self.onRemoteUSBRadioGroup)

        self.edsdkRb = wx.RadioButton(self, label = 'EDSDK', style=wx.RB_GROUP)
        vbox1.Add(self.edsdkRb, flag = wx.LEFT | wx.TOP, border = 10)
        self.edsdkRb.SetValue(False)
        self.edsdkRb.Disable()

        self.ptpRb = wx.RadioButton(self, label = 'PTP')
        vbox1.Add(self.ptpRb, flag = wx.LEFT | wx.TOP, border = 10)
        self.ptpRb.Disable()

        hboxF = wx.BoxSizer()
        self.frBtn = wx.Button(self, wx.ID_ANY, label = 'F-')
        hboxF.Add(self.frBtn)
        self.fiBtn = wx.Button(self, wx.ID_ANY, label = 'F+')
        hboxF.Add(self.fiBtn)
        vbox1.Add(hboxF, 1, flag = wx.TOP, border = 15)
        hbox.Add(vbox1, 1, flag = wx.LEFT, border = 30)

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        self.takePictureBtn = wx.Button(self, wx.ID_ANY, label = 'Take Picture')
        vbox2.Add(self.takePictureBtn)
        self.takePictureBtn.Bind(wx.EVT_BUTTON, self.OnTakePicture)

        self.startEvfBtn = wx.Button(self, wx.ID_ANY, label = 'Start Liveview')
        vbox2.Add(self.startEvfBtn)
        self.startEvfBtn.Bind(wx.EVT_BUTTON, self.onStartEvf)
        hbox.Add(vbox2, 1, flag = wx.LEFT, border = 10)
        vbox.Add(hbox, 1, flag = wx.LEFT)

        return vbox

    def OnMove(self, event):
        if self.canvas == "":
            self.canvas = self.visualizer_panel.canvas

        camId = self.masterCombo.GetSelection()
        if camId != -1:
            axis = event.GetEventObject().axis
            direction = event.GetEventObject().direction

            if axis in [Axis.X, Axis.Y, Axis.Z]:
                cmdBox = self.auiManager.GetPane('Command').window.cmd
                size = self.xyzSc.GetValue()


                if direction == Axis.Minus:
                    size = -size

                size = size / 100
            else:
                size = self.bcSc.GetValue()

                if direction == Axis.Minus:
                    size = -size

            cam = self.parent.visualizer_panel.getCamById(camId)
            if cam:
                cam.onMove(axis, size)
            self.canvas.OnDraw()
        else:
            util.set_dialog("Please select the camera to control.")

    def OnFocusCenter(self, event):
        if self.canvas == "":
            self.canvas = self.visualizer_panel.canvas

        if self.parent.selected_cam is not None:
            self.parent.visualizer_panel.getCamById(self.parent.selected_cam.id).onFocusCenter()
        else:
            util.set_dialog("Please select the camera to control.")

    def OnMasterCombo(self, event):
        choice = self.masterCombo.GetStringSelection()
        id = int(choice[-1])

        if self.parent.cam_list:
            self.parent.cam_list.set_selected_cam_by_id(id)

    def OnTakePicture(self, event):
        camId = self.masterCombo.GetSelection()
        if self.parent.cam_list.selected_camera is not None:
            self.parent.cam_list.selected_camera.shoot()
        else:
            util.set_dialog("Please select the camera to take a picture.")

    def onRemoteUSBRadioGroup(self, event):
        rb = event.GetEventObject()

        self.visualizer_panel.canvas.camera_objects = []
        self.visualizer_panel.canvas.OnDraw()
        self.masterCombo.Clear()

        if rb.Label == "USB":
            self.edsdkRb.Enable()
            self.ptpRb.Enable()
        elif rb.Label == "Remote Shutter":
            self.edsdkRb.SetValue(False)
            self.ptpRb.SetValue(False)
            self.edsdkRb.Disable()
            self.ptpRb.Disable()

            if self.parent.is_edsdk_on:
                self.parent.terminateEDSDK()
        elif rb.Label == "EDSDK":
            self.parent.initEDSDK()
        else:
            if self.parent.is_edsdk_on:
                self.parent.terminateEDSDK()

    def onDecreaseScale(self, event):
        self.visualizer_panel.canvas.scale -= 0.1
        self.visualizer_panel.canvas.OnDraw()

    def onIncreaseScale(self, event):
        self.visualizer_panel.canvas.scale += 0.1
        self.visualizer_panel.canvas.OnDraw()

    def onStartEvf(self, event):
        if self.parent.cam_list.selected_camera is not None:
            self.parent.cam_list.selected_camera.startEvf()
            self.auiManager.addEvfPane()
        else:
            util.set_dialog("Please select the camera to start live view.")

    def onRefresh(self, event):
        self.visualizer_panel.onClearCameras()
        self.masterCombo.Clear()

        if self.edsdkRb.GetValue():
            self.parent.is_edsdk_on = False
            self.parent.getCameraList()

    def onCreateVirtualCam(self, event):
        cam = self.parent.visualizer_panel.onDrawCamera()
        self.parent.controller_panel.masterCombo.Append("camera " + str(cam.id))