import wx
from ctypes import *
from controller.auiManager import AuiManager
from components.toolBar import ToolBarPanel
from components.menuBar import MenuBar
from components.statusBar import StatusBar

class MyPopupMenu(wx.Menu):
    def __init__(self, parent, *args, **kwargs):
        super(MyPopupMenu, self).__init__()
        self.parent = parent

        mmi = wx.MenuItem(self, wx.NewId(), 'Minimize')
        self.Append(mmi)
        self.Bind(wx.EVT_MENU, self.minimize, mmi)

        cmi = wx.MenuItem(self, wx.NewId(), 'Close')
        self.Append(cmi)
        self.Bind(wx.EVT_MENU, self.close, cmi)

    def minimize(self, event):
        self.parent.Iconize()

    def close(self, event):
        self.parent.Close()


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)

        self.cam_list = []
        self.selected_cam = None
        self.is_edsdk_on = False
        self.edsdkObject = None

        ## set minimum size to show whole interface properly
        self.SetMinSize(wx.Size(1000, 900))

        ## initialize menu bar
        self.SetMenuBar(MenuBar(self))

        ## initialize status bar
        self.SetStatusBar(StatusBar(self))

        ## initialize advanced user interface manager and panes
        self.auiManager = AuiManager(self)
        self.toolbar_panel = self.auiManager.GetPane("ToolBar").window
        self.console_panel = self.auiManager.GetPane("Console").window
        self.visualizer_panel = self.auiManager.GetPane('Visualizer').window
        self.controller_panel = self.auiManager.GetPane('Controller').window


        self.Centre()
        #self.Bind(wx.EVT_CLOSE, self.quit)


    def quit(self, event):
        self._mgr.UnInit()
        self.Close()

    def rightClick(self, event):
        self.PopupMenu(MyPopupMenu(self), event.GetPosition())

    def initEDSDK(self):
        if self.is_edsdk_on:
            return

        import controller.edsdkObject

        self.edsdkObject = controller.edsdkObject
        self.edsdkObject.initialize(self.console_panel)
        self.is_edsdk_on = True
        self.getCameraList()

    def getCameraList(self):
        self.cam_list = self.edsdkObject.CameraList()
        cam_count = self.cam_list.get_count()

        message = str(cam_count)
        if cam_count == 0:
            message = "There is no camera "

        elif cam_count == 1:
            message += " camera is "
        else:
            message += " cameras are "
        message += "connected."

        self.console_panel.print(message)

        for i in range(cam_count):
            camid = self.visualizer_panel.add_camera(camid=i)
            self.controller_panel.masterCombo.Append("camera " + camid)

    def get_selected_camera(self):
        if self.selected_cam:
            return self.selected_cam
        return None

    def set_selected_camera(self, id):
        # Check if selection is the same as previous selection
        new_selected = self.visualizer_panel.get_camera_by_id(id)
        last_selected = self.get_selected_camera()

        if new_selected == last_selected:
            return 0

        # reset previously selected camera
        if last_selected:
            last_selected.is_selected = False

        # update new selected camera
        self.selected_cam = new_selected
        self.selected_cam.is_selected = True

        # connect to physical camera
        if self.cam_list:
            if self.cam_list[id]:
                self.parent.cam_list.set_selected_cam_by_id(id)

        # refresh canvas
        self.visualizer_panel.set_dirty()

        # refresh combobox
        self.controller_panel.masterCombo.SetSelection(id)

    def terminateEDSDK(self):
        if not self.is_edsdk_on:
            return

        self.is_edsdk_on = False

        if self.cam_list:
            self.cam_list.terminate()
            self.cam_list = []
