"""TODO"""

import wx

from enums import CamAxis
from util.Canon.EDSDKLib import *
from utils import set_dialog


class ControllerPanel(wx.VScrolledWindow):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, style=wx.BORDER_DEFAULT)

        self.parent = parent
        self.init_panel()

    def init_panel(self):
        vboxLeft = wx.BoxSizer(wx.VERTICAL)

        # header font
        self.font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(15)

        # positioning section starts
        positioning_vbox = self.InitPositioning()
        vboxLeft.Add(positioning_vbox, 0.5, flag=wx.LEFT|wx.TOP, border=5)

        # camera control section
        cam_control_vbox = self.InitCamControl()
        vboxLeft.Add(cam_control_vbox, 0.5, flag=wx.LEFT|wx.TOP, border=5)

        self.SetSizerAndFit(vboxLeft)

    @property
    def visualizer_panel(self):
        return self.parent.visualizer_panel

    @property
    def timeline_panel(self):
        return self.parent.timeline_panel

    def InitPositioning(self):
        vboxPositioning = wx.BoxSizer(wx.VERTICAL)
        self.hboxCameraInfo = wx.BoxSizer()
        vboxPositioning.Add(self.hboxCameraInfo, 0.5, wx.EXPAND)

        positionLabel = wx.StaticText(self, wx.ID_ANY, label='Positioning', style=wx.ALIGN_LEFT)
        positionLabel.SetFont(self.font)
        vboxPositioning.Add(positionLabel, 0.5, flag=wx.BOTTOM|wx.TOP, border=10)

        hboxTop = wx.BoxSizer()
        camLabel = wx.StaticText(self, wx.ID_ANY, label='Camera: ', style=wx.ALIGN_LEFT)
        hboxTop.Add(camLabel)
        self.masterCombo = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY, size=(80, -1))
        self.masterCombo.Bind(wx.EVT_COMBOBOX, self.OnMasterCombo)
        hboxTop.Add(self.masterCombo)
        # self.setCenterBtn = wx.Button(self, wx.ID_ANY, label='Set Center')
        # hboxTop.Add(self.setCenterBtn, 1, flag=wx.LEFT, border=5)

        self.refreshBtn = wx.Button(self, wx.ID_ANY, label='&Refresh', size=(65, -1))
        self.refreshBtn.Bind(wx.EVT_BUTTON, self.onRefresh)
        hboxTop.Add(self.refreshBtn)
        hboxTop.AddStretchSpacer()

        self.createVCamBtn = wx.Button(self, wx.ID_ANY, label='&Create 3D camera')
        self.createVCamBtn.Bind(wx.EVT_BUTTON, self.onCreateVirtualCam)
        hboxTop.Add(self.createVCamBtn)
        vboxPositioning.Add(hboxTop, 0.5 , flag=wx.LEFT|wx.BOTTOM|wx.EXPAND, border=15)

        hboxXyzbc = wx.BoxSizer()
        vboxXyz = wx.BoxSizer(wx.VERTICAL)
        xyzLabel = wx.StaticText(self, wx.ID_ANY, label='XYZ Step Size', style=wx.ALIGN_LEFT)
        vboxXyz.Add(xyzLabel, 1, flag=wx.BOTTOM, border=10)

        hboxXyzSize = wx.BoxSizer()
        self.xyzSc = wx.SpinCtrl(self, value='0', size=(60, -1), min=0, max=100)
        hboxXyzSize.Add(self.xyzSc, 1, flag=wx.RIGHT|wx.BOTTOM, border=5)
        mmLabel = wx.StaticText(self, wx.ID_ANY, label='mm', style=wx.ALIGN_LEFT)
        hboxXyzSize.Add(mmLabel)
        vboxXyz.Add(hboxXyzSize)

        hboxYzInc = wx.BoxSizer()
        self.yiBtn = wx.Button(self, wx.ID_ANY, label='Y+', style=wx.BU_EXACTFIT)
        self.yiBtn.axis = CamAxis.Y
        self.yiBtn.direction = CamAxis.PLUS
        hboxYzInc.Add(self.yiBtn, 1, flag=wx.LEFT|wx.RIGHT, border=28)
        self.yiBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.ziBtn = wx.Button(self, wx.ID_ANY, label='Z+', style=wx.BU_EXACTFIT)
        self.ziBtn.axis = CamAxis.Z
        self.ziBtn.direction = CamAxis.PLUS
        hboxYzInc.Add(self.ziBtn)
        self.ziBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxXyz.Add(hboxYzInc)

        hboxX = wx.BoxSizer()
        self.xrBtn = wx.Button(self, wx.ID_ANY, label='X-', style=wx.BU_EXACTFIT)
        self.xrBtn.axis = CamAxis.X
        self.xrBtn.direction = CamAxis.MINUS
        hboxX.Add(self.xrBtn)
        self.xrBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.xiBtn = wx.Button(self, wx.ID_ANY, label='X+', style=wx.BU_EXACTFIT)
        self.xiBtn.axis = CamAxis.X
        self.xiBtn.direction = CamAxis.PLUS
        hboxX.Add(self.xiBtn, 1, flag=wx.LEFT, border=25)
        self.xiBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxXyz.Add(hboxX)

        hboxYzDec = wx.BoxSizer()
        self.yrBtn = wx.Button(self, wx.ID_ANY, label='Y-', style=wx.BU_EXACTFIT)
        self.yrBtn.axis = CamAxis.Y
        self.yrBtn.direction = CamAxis.MINUS
        hboxYzDec.Add(self.yrBtn, 1, flag=wx.LEFT|wx.RIGHT, border=28)
        self.yrBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.zrBtn = wx.Button(self, wx.ID_ANY, label='Z-', style=wx.BU_EXACTFIT)
        self.zrBtn.axis = CamAxis.Z
        self.zrBtn.direction = CamAxis.MINUS
        hboxYzDec.Add(self.zrBtn)
        self.zrBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxXyz.Add(hboxYzDec)
        hboxXyzbc.Add(vboxXyz)

        vboxBc = wx.BoxSizer(wx.VERTICAL)
        bcLabel = wx.StaticText(self, wx.ID_ANY, label='BC Step Size', style=wx.ALIGN_LEFT)
        vboxBc.Add(bcLabel, 1, flag=wx.BOTTOM, border=10)

        hboxBcSize = wx.BoxSizer()
        self.bcSc = wx.SpinCtrl(self, value='0', size=(60, -1), min=0, max=100)
        hboxBcSize.Add(self.bcSc, 1, flag=wx.RIGHT|wx.BOTTOM, border=0)
        ddLabel = wx.StaticText(self, wx.ID_ANY, label='dd', style=wx.ALIGN_LEFT)
        hboxBcSize.Add(ddLabel)
        vboxBc.Add(hboxBcSize)
        self.ciBtn = wx.Button(self, wx.ID_ANY, label='Tilt+', style=wx.BU_EXACTFIT)
        self.ciBtn.axis = CamAxis.C
        self.ciBtn.direction = CamAxis.PLUS
        vboxBc.Add(self.ciBtn, 1, flag=wx.LEFT, border=65)
        self.ciBtn.Bind(wx.EVT_BUTTON, self.OnMove)

        hboxB = wx.BoxSizer()
        self.brBtn = wx.Button(self, wx.ID_ANY, label='Pan-', style=wx.BU_EXACTFIT)
        self.brBtn.axis = CamAxis.B
        self.brBtn.direction = CamAxis.MINUS
        hboxB.Add(self.brBtn)
        self.brBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.cBtn = wx.Button(self, wx.ID_ANY, label='Center')
        hboxB.Add(self.cBtn)
        self.cBtn.Bind(wx.EVT_BUTTON, self.OnFocusCenter)
        self.biBtn = wx.Button(self, wx.ID_ANY, label='Pan+', style=wx.BU_EXACTFIT)
        self.biBtn.axis = CamAxis.B
        self.biBtn.direction = CamAxis.PLUS
        hboxB.Add(self.biBtn)
        self.biBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxBc.Add(hboxB)
        self.crBtn = wx.Button(self, wx.ID_ANY, label='Tilt-', style=wx.BU_EXACTFIT)
        self.crBtn.axis = CamAxis.C
        self.crBtn.direction = CamAxis.MINUS
        vboxBc.Add(self.crBtn, 1, flag=wx.LEFT, border=65)
        self.crBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        hboxXyzbc.Add(vboxBc, flag=wx.LEFT, border=25)

        vboxPositioning.Add(hboxXyzbc, 1, flag=wx.LEFT, border=15)
        return vboxPositioning

    def InitCamControl(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        cameraControlLabel = wx.StaticText(self, wx.ID_ANY, label='Camera Control', style=wx.ALIGN_LEFT)
        cameraControlLabel.SetFont(self.font)
        vbox.Add(cameraControlLabel, 0, flag=wx.TOP | wx.BOTTOM, border=10)

        hbox = wx.BoxSizer()
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.remoteRb = wx.RadioButton(self, label='Remote Shutter', style=wx.RB_GROUP)
        vbox1.Add(self.remoteRb)

        vboxAFShutter = wx.BoxSizer()
        self.afBtn = wx.Button(self, wx.ID_ANY, label='A/F')
        vboxAFShutter.Add(self.afBtn)
        self.shutterBtn = wx.Button(self, wx.ID_ANY, label='Shutter')
        vboxAFShutter.Add(self.shutterBtn)
        vbox1.Add(vboxAFShutter, 1, flag=wx.LEFT, border=5)

        self.usbRb = wx.RadioButton(self, label='USB')
        vbox1.Add(self.usbRb)
        self.Bind(wx.EVT_RADIOBUTTON, self.onRemoteUSBRadioGroup)

        self.edsdkRb = wx.RadioButton(self, label='EDSDK', style=wx.RB_GROUP)
        vbox1.Add(self.edsdkRb, flag=wx.LEFT | wx.TOP, border=10)
        self.edsdkRb.SetValue(False)
        self.edsdkRb.Disable()

        self.ptpRb = wx.RadioButton(self, label='PTP')
        vbox1.Add(self.ptpRb, flag=wx.LEFT | wx.TOP, border=10)
        self.ptpRb.Disable()

        hboxF = wx.BoxSizer()
        self.frBtn = wx.Button(self, wx.ID_ANY, label='Focus-')
        hboxF.Add(self.frBtn)
        self.fiBtn = wx.Button(self, wx.ID_ANY, label='Focus+')
        hboxF.Add(self.fiBtn)
        vbox1.Add(hboxF, 1, flag=wx.TOP, border=15)
        hbox.Add(vbox1, 1, flag=wx.LEFT, border=30)

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        self.takePictureBtn = wx.Button(self, wx.ID_ANY, label='Take Picture')
        vbox2.Add(self.takePictureBtn)
        self.takePictureBtn.Bind(wx.EVT_BUTTON, self.OnTakePicture)

        self.startEvfBtn = wx.Button(self, wx.ID_ANY, label='Start Liveview')
        vbox2.Add(self.startEvfBtn)
        self.startEvfBtn.Bind(wx.EVT_BUTTON, self.onStartEvf)
        hbox.Add(vbox2, 1, flag=wx.LEFT, border=10)
        vbox.Add(hbox, 1, flag=wx.LEFT)

        return vbox

    def OnMove(self, event):
        cam_id = self.masterCombo.GetSelection()
        if cam_id != -1:
            axis = event.GetEventObject().axis
            direction = event.GetEventObject().direction

            if axis in [CamAxis.X, CamAxis.Y, CamAxis.Z]:
                cmdbox = self.timeline_panel.cmd
                size = self.xyzSc.GetValue()

                if direction == CamAxis.MINUS:
                    size = -size
            else:
                size = self.bcSc.GetValue()

                if direction == CamAxis.MINUS:
                    size = -size

            cam = self.visualizer_panel.get_camera_by_id(cam_id)
            if cam:
                cam.on_move(axis, size)
            self.visualizer_panel.dirty = True
        else:
            set_dialog('Please select the camera to control.')

    def OnFocusCenter(self, event):
        if self.parent.selected_cam is not None:
            self.visualizer_panel.get_camera_by_id(self.parent.selected_cam.cam_id).on_focus_center()
        else:
            set_dialog('Please select the camera to control.')

    def OnMasterCombo(self, event):
        cam_id = self.masterCombo.GetSelection()
        self.parent.set_selected_camera(cam_id)

    def OnTakePicture(self, event):
        cam_id = self.masterCombo.GetSelection()
        if self.parent.get_selected_camera() is not None:
            self.parent.get_selected_camera().shoot()
        else:
            set_dialog('Please select the camera to take a picture.')

    def onRemoteUSBRadioGroup(self, event):
        rb = event.GetEventObject()

        self.visualizer_panel.on_clear_cameras()
        self.masterCombo.Clear()

        if rb.Label == 'USB':
            self.edsdkRb.Enable()
            self.ptpRb.Enable()
        elif rb.Label == 'Remote Shutter':
            self.edsdkRb.SetValue(False)
            self.ptpRb.SetValue(False)
            self.edsdkRb.Disable()
            self.ptpRb.Disable()

            if self.parent.is_edsdk_on:
                self.parent.terminate_edsdk()
        elif rb.Label == 'EDSDK':
            self.parent.initEDSDK()
        else:
            if self.parent.is_edsdk_on:
                self.parent.terminate_edsdk()

    def onStartEvf(self, event):
        if self.parent.get_selected_camera() is not None:
            self.parent.get_selected_camera().startEvf()
            self.parent.add_evf_pane()
        else:
            set_dialog('Please select the camera to start live view.')

    def onRefresh(self, event):
        self.visualizer_panel.on_clear_cameras()
        self.masterCombo.Clear()

        if self.edsdkRb.GetValue():
            self.parent.is_edsdk_on = False
            self.parent.get_camera_list()

    def onCreateVirtualCam(self, event):
        cam_id = self.visualizer_panel.add_camera()
        self.parent.controller_panel.masterCombo.Append('camera ' + cam_id)
