from Canon.EDSDKLib import *
import wx
from leftPanel import LeftPanel
from rightPanel import RightPanel
from camera import *
import random
from ctypes import *
import canvas

class MyPopupMenu(wx.Menu):
    def __init__(self, parent):
        super(MyPopupMenu, self).__init__()
        self.parent = parent

        mmi = wx.MenuItem(self, wx.NewId(), 'Minimize')
        self.Append(mmi)
        self.Bind(wx.EVT_MENU, self.minimize, mmi)

        cmi = wx.MenuItem(self, wx.NewId(), 'Close')
        self.Append(cmi)
        self.Bind(wx.EVT_MENU, self.close, cmi)

    def minimize(self, e):
        self.parent.Iconize()

    def close(self, e):
        self.parent.Close()
        

class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs, style = wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE, title = "COPIS")

        ## set minimum size to show whole interface properly
        self.SetMinSize(wx.Size(1352, 850))

        ## initialize menu bar
        self.initMenubar()

        ## initialize tool bar
        self.initToolbar()

        ## initialize status bar
        self.initStatusbar()

        ## split the window in a half
        self.splitter = wx.SplitterWindow(self)
        self.panelLeft = LeftPanel(self.splitter)
        self.panelRight = RightPanel(self.splitter)

        self.splitter.SplitVertically(self.panelLeft, self.panelRight)
        self.panelLeft.SetFocus()
        self.Centre()

        self.cam_list = []

    def initToolbar(self):
        toolbar = self.CreateToolBar()

        ## port and baud options
        ## TO DO: it should detect ports and baud options when the machine is connected
        toolbar.AddStretchableSpace()
        portLabel = wx.StaticText(toolbar, id = wx.ID_ANY, label = "Port: ", style = wx.ALIGN_LEFT)
        toolbar.AddControl(portLabel)
        portCombo = wx.ComboBox(toolbar, wx.ID_ANY, value = "", choices = ["Port 1", "Port 2", "Port 3"])
        toolbar.AddControl(portCombo)
        baudLabel = wx.StaticText(toolbar, id = wx.ID_ANY, label = " Baud: ", style = wx.ALIGN_RIGHT)
        toolbar.AddControl(baudLabel)
        baudCombo = wx.ComboBox(toolbar, wx.ID_ANY, value = "", choices = ["Baud 1", "Baud 2", "Baud 3"])
        toolbar.AddControl(baudCombo)

        ## connect and disconnect to the port buttons
        ## TO DO: create and bind functions
        connectBtn = wx.Button(toolbar, wx.ID_ANY, label = "Connect")
        toolbar.AddControl(connectBtn)

        disconnectBtn = wx.Button(toolbar, wx.ID_ANY, label = "Disconnect")
        toolbar.AddControl(disconnectBtn)

        ## play, pause and stop buttons to animate the commands
        ## TO DO: create and bind functions
        toolbar.AddStretchableSpace()
        playImg = wx.Image('img/play.png')
        playImg = playImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        toolbar.AddTool(1, 'Play', wx.BitmapFromImage(playImg))

        pauseImg = wx.Image('img/pause.png')
        pauseImg = pauseImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        toolbar.AddTool(1, 'Pause', wx.BitmapFromImage(pauseImg))
        
        stopImg = wx.Image('img/stop.png')
        stopImg = stopImg.Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        toolbar.AddTool(1, 'Stop', wx.BitmapFromImage(stopImg))

        ## import file
        ## TO DO: create and bind function to "Browse" button
        toolbar.AddStretchableSpace()
        fileLabel = wx.StaticText(toolbar, id = wx.ID_ANY, label = "File: ", style = wx.ALIGN_LEFT)
        toolbar.AddControl(fileLabel)
        fileBox = wx.TextCtrl(toolbar)
        toolbar.AddControl(fileBox)
        loadBtn = wx.Button(toolbar, wx.ID_ANY, label = "Browse")
        toolbar.AddControl(loadBtn)

        ## setting options
        ## TO DO: figure out what settings are needed and create a popup box with setting options
        toolbar.AddStretchableSpace()
        settingImg = wx.Image('img/setting.png')
        settingImg = settingImg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        toolbar.AddTool(1, 'Setting', wx.BitmapFromImage(settingImg))
        
        toolbar.Realize()

    def initMenubar(self):
        menubar = wx.MenuBar()

        ## view menu that shows view options
        viewMenu = wx.Menu()
        ## add statusbar show option to view menu
        self.shst = viewMenu.Append(wx.ID_ANY, 'Show statusbar', 'Show Statusbar', kind=wx.ITEM_CHECK)
        ## set default true
        viewMenu.Check(self.shst.GetId(), True)
        self.Bind(wx.EVT_MENU, self.toggleStatusbar, self.shst)

        ## add view menu to menu bar
        menubar.Append(viewMenu, '&View')
        ## set menu bar to the frame
        self.SetMenuBar(menubar)

    def initStatusbar(self):
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('Ready')

    def quit(self, e):
        self.Close()

    def toggleStatusbar(self, e):
        if self.shst.IsChecked():
            self.statusbar.Show()
        else:
            self.statusbar.Hide()

    def rightClick(self, e):
        self.PopupMenu(MyPopupMenu(self), e.GetPosition())

    def deleteCamera(self):
        if self.selected_cam:
            self.cam_list.cam_model_list.remove(self.selected_cam)
            del self.selected_cam
            self.selected_cam = None

    def initEDSDK(self):
        self.cam_list = CameraList()
        cam_count = self.cam_list.get_count()

        message = str(cam_count)
        if cam_count < 2:
            message += " cameara is "
        else:
            message += " cameras are "
        message += "connected."
        print(message)

        for i in range(cam_count):
            x = float(random.randrange(-100, 100)) / 100
            y = float(random.randrange(-100, 100)) / 100
            z = float(random.randrange(-100, 100)) / 100
            b = random.randrange(0, 360, 5)
            c = random.randrange(0, 360, 5)
            
            cam_3d = canvas.Camera3D(i, x, y, z, b, c)
            self.cam_list.cam_model_list.append(cam_3d)
            self.panelRight.canvas.OnDrawCamera(i, x, y, z, b, c)
            self.panelLeft.masterCombo.Append("camera " + str(i + 1))
        
    