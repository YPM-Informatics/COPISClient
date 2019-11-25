import wx
from pygcode import *
from enums import Axis

class LeftPanel(wx.Panel):
    def __init__(self, parent):
        super(LeftPanel, self).__init__(parent, style = wx.BORDER_SUNKEN)
        self.parent = parent
        self.InitPanel()
        self.canvas = ""

    def InitPanel(self):
        vboxLeft = wx.BoxSizer(wx.VERTICAL)
        
        ## header font
        self.font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(15)

        ## Adding camera section
        ## This is just for testing
        add_camera_hbox = self.InitAddCamera()
        vboxLeft.Add(add_camera_hbox, 0.5, wx.LEFT|wx.TOP, border = 5)

        ## Positioning section starts
        positioning_vbox = self.InitPositioning()
        vboxLeft.Add(positioning_vbox, 0.5, flag = wx.LEFT|wx.TOP, border = 5)

        ## Circular path generator section
        circular_path_hbox = self.InitCircularPathGenerator()
        vboxLeft.Add(circular_path_hbox, 0.5, flag = wx.LEFT|wx.TOP, border = 5)

        ## Z stack generator and camera control section
        z_stack_hbox = self.InitZStackAndCamControl()
        vboxLeft.Add(z_stack_hbox, 0.5, flag = wx.LEFT|wx.TOP, border = 5)
        
        self.SetSizerAndFit(vboxLeft)
        
    def InitAddCamera(self):
        ## LAYOUT
        
        ########################################################################################
        ##                                                                                    ##
        ## hbox ----------------------------------------------------------------------------- ##
        ##      | vbox  ------------------------------------------ vbox     --------------- | ##
        ##      | Xyzpt | hbox --------------------------------- | AddClear | ----------- | | ##
        ##      |       | Xyz  |    ------    ------    ------ | |          | |   Add   | | | ##
        ##      |       |      | X: |    | Y: |    | Z: |    | | |          | ----------- | | ##
        ##      |       |      |    ------    ------    ------ | |          | ----------- | | ##
        ##      |       |      --------------------------------- |          | |  Clear  | | | ##
        ##      |       | hbox --------------------------------- |          | ----------- | | ##
        ##      |       | Pt   |    ------    ------           | |          --------------- | ##
        ##      |       |      | P: |    | P: |    |           | |                          | ##
        ##      |       |      |    ------    ------           | |                          | ##
        ##      |       |      --------------------------------- |                          | ##
        ##      |       ------------------------------------------                          | ##
        ##      ----------------------------------------------------------------------------- ##
        ##                                                                                    ##
        ########################################################################################
        hbox = wx.BoxSizer()
        vboxXyzpt = wx.BoxSizer(wx.VERTICAL)
        hboxXyz = wx.BoxSizer()
        xInputLabel = wx.StaticText(self, -1, "X: ")
        hboxXyz.Add(xInputLabel, 1, flag = wx.RIGHT, border = 10)
        self.xTc = wx.TextCtrl(self)
        hboxXyz.Add(self.xTc)
        yInputLabel = wx.StaticText(self, -1, "Y: ")
        hboxXyz.Add(yInputLabel, 1, flag = wx.RIGHT|wx.LEFT, border = 10)
        self.yTc = wx.TextCtrl(self)
        hboxXyz.Add(self.yTc)
        zInputLabel = wx.StaticText(self, -1, "Z: ")
        hboxXyz.Add(zInputLabel, 1, flag = wx.RIGHT|wx.LEFT, border = 10)
        self.zTc = wx.TextCtrl(self)
        hboxXyz.Add(self.zTc)
        vboxXyzpt.Add(hboxXyz)

        hboxBc = wx.BoxSizer()
        bInputLabel = wx.StaticText(self, -1, "B: ")
        hboxBc.Add(bInputLabel, 1, flag = wx.RIGHT, border = 10)
        self.bTc = wx.TextCtrl(self)
        hboxBc.Add(self.bTc)
        cInputLabel = wx.StaticText(self, -1, "C: ")
        hboxBc.Add(cInputLabel, 1, flag = wx.RIGHT|wx.LEFT, border = 10)
        self.cTc = wx.TextCtrl(self)
        hboxBc.Add(self.cTc)
        vboxXyzpt.Add(hboxBc, 1, flag = wx.TOP, border = 2)
        hbox.Add(vboxXyzpt)

        vboxAddClear = wx.BoxSizer(wx.VERTICAL)
        addCamBtn = wx.Button(self, wx.ID_ANY, label = 'Add')
        vboxAddClear.Add(addCamBtn)
        clearCamBtn = wx.Button(self, wx.ID_ANY, label = 'Clear')
        vboxAddClear.Add(clearCamBtn)
        hbox.Add(vboxAddClear, 1, flag = wx.LEFT, border = 10)

        addCamBtn.Bind(wx.EVT_BUTTON, self.OnAddCameraButton)
        
        return hbox

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
	    ##             |       | YzInc |         Y++         Z++  |                   T++             | | ##
	    ##             |       |       ----------------------------                                   | | ##
	    ##             |       | hboxX ---------------------------- hboxP --------------------------- | | ##
	    ##             |       |       |    X-          X++       |       |     P-     c      P++   | | | ##
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
        self.masterCombo = wx.ComboBox(self, wx.ID_ANY, choices = [])
        hboxTop.Add(self.masterCombo)
        ## self.setCenterBtn = wx.Button(self, wx.ID_ANY, label = 'Set Center')
        ## hboxTop.Add(self.setCenterBtn, 1, flag = wx.LEFT, border = 5)
        
        self.setCenterBtn = wx.Button(self, wx.ID_ANY, label = 'Refresh From COPIS')
        hboxTop.Add(self.setCenterBtn)
        ## sld = wx.Slider(self, maxValue = 500, style = wx.SL_HORIZONTAL)
        ## hboxTop.Add(sld)
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
        self.yiBtn = wx.Button(self, wx.ID_ANY, label = 'Y++')
        self.yiBtn.axis = Axis.Y
        self.yiBtn.direction = Axis.Plus
        hboxYzInc.Add(self.yiBtn, 1, flag = wx.LEFT|wx.RIGHT, border = 55)
        self.yiBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.ziBtn = wx.Button(self, wx.ID_ANY, label = 'Z++')
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
        self.xiBtn = wx.Button(self, wx.ID_ANY, label = 'X++')
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
        self.ciBtn = wx.Button(self, wx.ID_ANY, label = 'C++')
        self.ciBtn.axis = Axis.C
        self.ciBtn.direction = Axis.Plus
        vboxBc.Add(self.ciBtn, 1, flag = wx.LEFT, border = 88)
        self.ciBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        
        hboxB = wx.BoxSizer()
        self.brBtn = wx.Button(self, wx.ID_ANY, label = 'B-')
        self.brBtn.axis = Axis.B
        self.brBtn.direction = Axis.Minus
        hboxB.Add(self.brBtn)
        self.brBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        self.cBtn = wx.Button(self, wx.ID_ANY, label = 'center')
        hboxB.Add(self.cBtn)
        self.cBtn.Bind(wx.EVT_BUTTON, self.OnFocusCenter)
        self.biBtn = wx.Button(self, wx.ID_ANY, label = 'B++')
        self.biBtn.axis = Axis.B
        self.biBtn.direction = Axis.Plus
        hboxB.Add(self.biBtn)
        self.biBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        vboxBc.Add(hboxB)
        self.crBtn = wx.Button(self, wx.ID_ANY, label = 'C-')
        self.crBtn.axis = Axis.C
        self.crBtn.direction = Axis.Minus
        vboxBc.Add(self.crBtn, 1, flag = wx.LEFT, border = 88)
        self.crBtn.Bind(wx.EVT_BUTTON, self.OnMove)
        hboxXyzbc.Add(vboxBc)

        vboxPositioning.Add(hboxXyzbc, 1, flag = wx.LEFT, border = 15)

        ## hboxExtra = wx.BoxSizer()
        ## self.eMotorBtn = wx.Button(self, wx.ID_ANY, label = 'Enable Motors')
        ## hboxExtra.Add(self.eMotorBtn, 1, flag = wx.RIGHT, border = 10)
        ## self.dMotorBtn = wx.Button(self, wx.ID_ANY, label = 'Disable Motors')
        ## hboxExtra.Add(self.dMotorBtn, 1, flag = wx.RIGHT, border = 10)
        ## self.recordBtn = wx.Button(self, wx.ID_ANY, label = 'Record Position')
        ## hboxExtra.Add(self.recordBtn, 1, flag = wx.RIGHT, border = 10)
        ## self.homeBtn = wx.Button(self, wx.ID_ANY, label = 'Home')
        ## hboxExtra.Add(self.homeBtn, 1, flag = wx.RIGHT, border = 10)
        ## self.setHomeBtn = wx.Button(self, wx.ID_ANY, label = 'Set Home')
        ## hboxExtra.Add(self.setHomeBtn)
        ## vboxPositioning.Add(hboxExtra, 0.5, flag = wx.LEFT, border = 15)
        
        return vboxPositioning

    def InitCircularPathGenerator(self):
        ## LAYOUT

     	##################################################################################################
        ##                                                                                              ##
        ## hbox --------------------------------------------------------------------------------------- ##
        ##      | vbox1  ------------------------------  vbox2 --------------------  vbox3 ---------- | ##
	    ##      |        | Circular Path Generator    |        |  Take Photo at   |        | rpm:   | | ##
	    ##      |        | hbox   ------------------- |        |  Each Vertex     |        | X:     | | ##
	    ##      |        | Points | No.Points: ____ | |        |                  |        | Y:     | | ##
	    ##      |        |        ------------------- |        |  Generate Circle |        | Z:     | | ##
	    ##      |        | hbox   ------------------- |        |                  |        | P:     | | ##
	    ##      |        | Radius | Radius (mm): ___| |        |  Generate Sphere |        | T:     | | ##
	    ##      |        |        ------------------- |        --------------------        ---------- | ##
	    ##      |        | hbox   ------------------- |                                               | ##
	    ##      |        | StartX | Start X: ____   | |                                               | ##
	    ##      |        |        ------------------- |                                               | ##
	    ##      |        | hbox   ------------------- |                                               | ##
	    ##      |        | StartY | Start Y: ____   | |                                               | ##
	    ##      |        |        ------------------- |                                               | ##
	    ##      |        | hbox   ------------------- |                                               | ##
	    ##      |        | StartZ | Start Z: ____   | |                                               | ##
	    ##      |        |        ------------------- |                                               | ##
        ##      |        | hbox   ------------------- |                                               | ##
        ##      |        | Cameras| No. Cams: ____  | |                                               | ##
        ##      |        |        ------------------- |                                               | ##
        ##      |        ------------------------------                                               | ##
        ##      --------------------------------------------------------------------------------------- ##
        ##                                                                                              ##
        ##################################################################################################
        hbox = wx.BoxSizer()
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        cGeneratorLabel = wx.StaticText(self, wx.ID_ANY, label = 'Circular Path Generator', style = wx.ALIGN_LEFT)
        cGeneratorLabel.SetFont(self.font)
        vbox1.Add(cGeneratorLabel, 1, flag = wx.TOP|wx.BOTTOM, border = 10)
        hboxPoints = wx.BoxSizer()
        noPointsLabel = wx.StaticText(self, wx.ID_ANY, label = 'No. Points: ')
        hboxPoints.Add(noPointsLabel, 1, flag = wx.RIGHT, border = 5)
        self.noPointsSc = wx.SpinCtrl(self, value = '0')
        self.noPointsSc.SetRange(0, 100)
        hboxPoints.Add(self.noPointsSc)
        vbox1.Add(hboxPoints, 1, flag = wx.LEFT, border = 15)

        hboxRadius = wx.BoxSizer()
        radiusLabel = wx.StaticText(self, wx.ID_ANY, label = 'Radius (mm): ')
        hboxRadius.Add(radiusLabel, 1, flag = wx.RIGHT, border = 5)
        self.radiusSc = wx.SpinCtrl(self, value = '0')
        self.radiusSc.SetRange(0, 100)
        hboxRadius.Add(self.radiusSc)
        vbox1.Add(hboxRadius, 1, flag = wx.LEFT, border = 15)

        hboxStartX = wx.BoxSizer()
        startXLabel = wx.StaticText(self, wx.ID_ANY, label = 'Start X: ')
        hboxStartX.Add(startXLabel, 1, flag = wx.RIGHT, border = 5)
        self.startXSc = wx.SpinCtrl(self, value = '0')
        self.startXSc.SetRange(0, 100)
        hboxStartX.Add(self.startXSc)
        vbox1.Add(hboxStartX, 1, flag = wx.LEFT, border = 15)

        hboxStartY = wx.BoxSizer()
        startYLabel = wx.StaticText(self, wx.ID_ANY, label = 'Start Y: ')
        hboxStartY.Add(startYLabel, 1, flag = wx.RIGHT, border = 5)
        self.startYSc = wx.SpinCtrl(self, value = '0')
        self.startYSc.SetRange(0, 100)
        hboxStartY.Add(self.startYSc)
        vbox1.Add(hboxStartY, 1, flag = wx.LEFT, border = 15)

        hboxStartZ = wx.BoxSizer()
        startZLabel = wx.StaticText(self, wx.ID_ANY, label = 'Start Z: ')
        hboxStartZ.Add(startZLabel, 1, flag = wx.RIGHT, border = 5)
        self.startZSc = wx.SpinCtrl(self, value = '0')
        self.startZSc.SetRange(0, 100)
        hboxStartZ.Add(self.startZSc)
        vbox1.Add(hboxStartZ, 1, flag = wx.LEFT, border = 15)

        hboxCameras = wx.BoxSizer()
        noCamsLabel = wx.StaticText(self, wx.ID_ANY, label = 'No. Cams: ')
        hboxCameras.Add(noCamsLabel, 1, flag = wx.RIGHT, border = 5)
        self.noCamsSc = wx.SpinCtrl(self, value = '0')
        self.noCamsSc.SetRange(0, 100)
        hboxCameras.Add(self.noCamsSc)
        vbox1.Add(hboxCameras, 1, flag = wx.LEFT, border = 15)
        hbox.Add(vbox1)
        
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        self.vertextPhotoCb = wx.CheckBox(self, label = 'Take Photo at Each Vertex')
        vbox2.Add(self.vertextPhotoCb)
        self.generateCBtn = wx.Button(self, wx.ID_ANY, label = 'Generate Circle')
        vbox2.Add(self.generateCBtn, 1, flag = wx.TOP, border = 5)
        self.generateSBtn = wx.Button(self, wx.ID_ANY, label = 'Generate Sphere')
        vbox2.Add(self.generateSBtn, 1, flag = wx.TOP, border = 5)
        hbox.Add(vbox2, 1, flag = wx.TOP|wx.LEFT, border = 30)

        vbox3 = wx.BoxSizer(wx.VERTICAL)
        self.rpmLabel = wx.StaticText(self, wx.ID_ANY, label = 'rpm: ')
        vbox3.Add(self.rpmLabel, 1, flag = wx.BOTTOM, border = 10)
        self.xLabel = wx.StaticText(self, wx.ID_ANY, label = 'X: ')
        vbox3.Add(self.xLabel, 1, flag = wx.BOTTOM, border = 10)
        self.yLabel = wx.StaticText(self, wx.ID_ANY, label = 'Y: ')
        vbox3.Add(self.yLabel, 1, flag = wx.BOTTOM, border = 10)
        self.zLabel = wx.StaticText(self, wx.ID_ANY, label = 'Z: ')
        vbox3.Add(self.zLabel, 1, flag = wx.BOTTOM, border = 10)
        self.bLabel = wx.StaticText(self, wx.ID_ANY, label = 'B: ')
        vbox3.Add(self.bLabel, 1, flag = wx.BOTTOM, border = 10)
        self.cLabel = wx.StaticText(self, wx.ID_ANY, label = 'C: ')
        vbox3.Add(self.cLabel)
        hbox.Add(vbox3, 1, flag = wx.TOP|wx.LEFT, border = 30)
        
        return hbox

    def InitZStackAndCamControl(self):
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
	    ##      |        | ------------                   |        |         |                |  F++ | |    | | ##
	    ##      |        | | Generate |                   |        |         |                -------- |    | | ##
	    ##      |        | ------------                   |        |         ---------------------------    | | ##
	    ##      |        ----------------------------------        ------------------------------------------ | ##
        ##      ----------------------------------------------------------------------------------------------- ##
        ##                                                                                                      ##
        ##########################################################################################################
        ## hbox = wx.BoxSizer()
        ## vbox1 = wx.BoxSizer(wx.VERTICAL)
        ## zGeneratorLabel = wx.StaticText(self, wx.ID_ANY, label = 'Z Stack Generator', style = wx.ALIGN_LEFT)
        ## zGeneratorLabel.SetFont(self.font)
        ## vbox1.Add(zGeneratorLabel, 1, flag = wx.TOP|wx.BOTTOM, border = 5)
        ## 
        ## hboxFocalSteps = wx.BoxSizer()
        ## noFocalStepsLabel = wx.StaticText(self, wx.ID_ANY, label = 'No. Focal Steps: ')
        ## hboxFocalSteps.Add(noFocalStepsLabel)
        ## self.noFocalStepsSc = wx.SpinCtrl(self, value = '0')
        ## self.noFocalStepsSc.SetRange(0, 100)
        ## hboxFocalSteps.Add(self.noFocalStepsSc, 1, flag = wx.LEFT, border = 5)
        ## vbox1.Add(hboxFocalSteps, 1, flag = wx.LEFT, border = 15)
        ## 
        ## hboxStartZ = wx.BoxSizer()
        ## startZLabel2 = wx.StaticText(self, wx.ID_ANY, label = 'Start Z: ')
        ## hboxStartZ.Add(startZLabel2)
        ## self.startZSc2 = wx.SpinCtrl(self, value = '0')
        ## self.startZSc2.SetRange(0, 100)
        ## hboxStartZ.Add(self.startZSc2, 1, flag = wx.TOP, border = 5)
        ## vbox1.Add(hboxStartZ, 1, flag = wx.LEFT, border = 15)
        ## 
        ## hboxZInc = wx.BoxSizer()
        ## zIncrementLabel = wx.StaticText(self, wx.ID_ANY, label = 'Z Increment (mm): ')
        ## hboxZInc.Add(zIncrementLabel)
        ## self.zIncrementSc = wx.SpinCtrl(self, value = '0')
        ## self.zIncrementSc.SetRange(0, 100)
        ## hboxZInc.Add(self.zIncrementSc, flag = wx.TOP, border = 5)
        ## vbox1.Add(hboxZInc, 1, flag = wx.LEFT, border = 15)
        ## self.generateBtn = wx.Button(self, wx.ID_ANY, label = 'Generate')
        ## vbox1.Add(self.generateBtn, 1, flag = wx.TOP|wx.LEFT, border = 10)
        ## hbox.Add(vbox1)

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        cameraControlLabel = wx.StaticText(self, wx.ID_ANY, label = 'Camera Control', style = wx.ALIGN_LEFT)
        cameraControlLabel.SetFont(self.font)
        vbox2.Add(cameraControlLabel, 1, flag = wx.TOP, border = 10)

        hboxRemote = wx.BoxSizer()
        self.remoteRb = wx.RadioButton(self, label = 'Remote Shutter')
        hboxRemote.Add(self.remoteRb)

        vboxAFShutter = wx.BoxSizer(wx.VERTICAL)
        self.afBtn = wx.Button(self, wx.ID_ANY, label = 'A/F')
        vboxAFShutter.Add(self.afBtn)
        self.shutterBtn = wx.Button(self, wx.ID_ANY, label = 'Shutter')
        vboxAFShutter.Add(self.shutterBtn)
        hboxRemote.Add(vboxAFShutter, 1, flag = wx.LEFT, border = 5)
        vbox2.Add(hboxRemote)

        hboxUSB = wx.BoxSizer()
        self.usbRb = wx.RadioButton(self, label = 'USB/PTP')
        hboxUSB.Add(self.usbRb)
        
        vboxF = wx.BoxSizer(wx.VERTICAL)
        self.frBtn = wx.Button(self, wx.ID_ANY, label = 'F-')
        vboxF.Add(self.frBtn)
        self.fiBtn = wx.Button(self, wx.ID_ANY, label = 'F++')
        vboxF.Add(self.fiBtn)
        hboxUSB.Add(vboxF, 1, flag = wx.LEFT, border = 5)
        vbox2.Add(hboxUSB, 1, flag = wx.TOP, border = 5)
        
        ##hbox.Add(vbox2, 1, flag = wx.LEFT, border = 30)

        return vbox2

    def OnAddCameraButton(self, event):
        if self.canvas == "":
            self.canvas = self.parent.GetWindow2().canvas
        x = float(self.xTc.GetValue()) / 100
        y = float(self.yTc.GetValue()) / 100
        z = float(self.zTc.GetValue()) / 100
        b = self.bTc.GetValue()
        c = self.cTc.GetValue()

        self.canvas.OnDrawCamera(x, y, z, b, c)
        ## get the camera added
        camera = self.parent.GetWindow2().canvas.cameras[-1]

        ## set the new camera option to positioning DDL
        cameraLabelTxt = "camera" + str(len(self.parent.GetWindow2().canvas.cameras))
        self.masterCombo.Append(cameraLabelTxt)

        ## Display camera name and color before "Positioning" label
        cameraLabel = wx.StaticText(self, wx.ID_ANY, label = cameraLabelTxt, style = wx.ALIGN_LEFT)
        cameraLabel.SetForegroundColour((0, 0, 0))
        cameraLabel.SetBackgroundColour((camera.red, camera.green, camera.blue))
        self.hboxCameraInfo.Add(cameraLabel, 1, wx.SHAPED)
        self.hboxCameraInfo.Layout()
        self.Fit()

    def SetDialog(self, message):
        msg = wx.MessageDialog(self, message, "Confirm Exit", wx.OK)
        msg.ShowModal()
        msg.Destroy()

    def OnMove(self, event):
        if self.canvas == "":
            self.canvas = self.parent.GetWindow2().canvas
            
        cameraOption = self.masterCombo.GetSelection()
        if cameraOption != -1:
            axis = event.GetEventObject().axis
            direction = event.GetEventObject().direction
            
            if axis in [Axis.X, Axis.Y, Axis.Z]:
                cmdBox = self.parent.GetWindow2().cmd
                gcode = ""
                size = self.xyzSc.GetValue()
                
##                if self.parent.gcodeMode != 'G91':
##                    self.parent.gcodeMode = 'G91'
##                    cmdBox.Append('G91')
                    
                if direction == Axis.Minus:
                    size = -size
                    
##                if axis == Axis.X:
##                    gcode = GCodeLinearMove(X=size)
##                elif axis == Axis.Y:
##                    gcode = GCodeLinearMove(Y=size)
##                elif axis == Axis.Z:
##                    gcode = GCodeLinearMove(Z=size)
##                cmdBox.Append(str(gcode))
                
                size = size / 100
            else:
                size = self.bcSc.GetValue()
                
                if direction == Axis.Minus:
                    size = -size
            
                
            self.canvas.cameras[cameraOption].onMove(axis, size)
            self.canvas.OnDraw()
        else:
            self.SetDialog("Please select the camera to control")

    def OnFocusCenter(self, event):
        if self.canvas == "":
            self.canvas = self.parent.GetWindow2().canvas

        cameraOption = self.masterCombo.GetSelection()

        if cameraOption != -1:
            self.canvas.cameras[cameraOption].onFocusCenter()
        else:
            self.SetDialog("Please select the camera to control")
        
