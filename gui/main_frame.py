#!/usr/bin/env python3

import wx
from ctypes import *

from gui.auimanager import AuiManager
from gui.pathgen_frame import *
from gui.config_frame import *


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

        self.menubar = None

        self.preferences_frame = None
        self.pathgen_frame = None

        self.cam_list = []
        self.selected_cam = None
        self.is_edsdk_on = False
        self.edsdk_object = None

        # set minimum size to show whole interface properly
        self.SetMinSize(wx.Size(800, 575))

        # initialize status bar and menu bar
        self.init_statusbar()
        self.init_menubar()

        # initialize advanced user interface manager and panes
        self._mgr = AuiManager(self)
        self.toolbar_panel = self._mgr.GetPane('ToolBar').window
        self.console_panel = self._mgr.GetPane('Console').window
        self.visualizer_panel = self._mgr.GetPane('Visualizer').window
        self.controller_panel = self._mgr.GetPane('Controller').window

        self.Centre()
        self.Bind(wx.EVT_CLOSE, self.quit)

    def init_statusbar(self):
        if self.GetStatusBar() is not None:
            return

        self.CreateStatusBar(1, id=wx.ID_ANY)
        self.SetStatusText('Ready')

    def init_menubar(self):
        if self.menubar is not None:
            return

        self.menubar = wx.MenuBar(0)

        # File menu
        file_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, None, file_menu.Append(wx.ID_ANY, '&New Project\tCtrl+N', ''))
        self.Bind(wx.EVT_MENU, None, file_menu.Append(wx.ID_ANY, '&Open...\tCtrl+O', ''))
        file_menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, None, file_menu.Append(wx.ID_ANY, '&Save\tCtrl+S', ''))
        self.Bind(wx.EVT_MENU, None, file_menu.Append(wx.ID_ANY, 'Save &As...\tCtrl+Shift+S', ''))
        file_menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, None, file_menu.Append(wx.ID_ANY, '&Import GCODE...', ''))
        self.Bind(wx.EVT_MENU, None, file_menu.Append(wx.ID_ANY, '&Generate GCODE\tF8', ''))
        file_menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, None, file_menu.Append(wx.ID_ANY, 'E&xit\tAlt+F4', ''))

        # Edit menu
        edit_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, None, edit_menu.Append(wx.ID_ANY, '&Keyboard Shortcuts...', 'Open keyboard shortcuts'))
        edit_menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, self.open_preferences_frame, edit_menu.Append(wx.ID_ANY, '&Preferences', 'Open preferences'))

        # View menu
        view_menu = wx.Menu()
        self.statusbar_item = view_menu.Append(wx.ID_ANY, 'Status Bar', 'Toggle status bar visibility', wx.ITEM_CHECK)
        view_menu.Check(self.statusbar_item.GetId(), True)
        self.Bind(wx.EVT_MENU, self.update_statusbar, self.statusbar_item)

        # Tools menu
        tools_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, self.open_pathgen_frame, tools_menu.Append(wx.ID_ANY, 'Generate Path', 'Open path generator window'))

        # Window menu
        window_menu = wx.Menu()
        self.cameraevf_item = window_menu.Append(wx.ID_ANY, 'Camera EVF', 'Toggle visibility of camera EVF window', wx.ITEM_CHECK)
        self.command_item = window_menu.Append(wx.ID_ANY, 'Command', 'Toggle visibility of command window', wx.ITEM_CHECK)
        self.console_item = window_menu.Append(wx.ID_ANY, 'Console', 'Toggle visibility of console window', wx.ITEM_CHECK)
        self.controller_item = window_menu.Append(wx.ID_ANY, 'Controller', 'Toggle visibility of controller window', wx.ITEM_CHECK)
        self.visualizer_item = window_menu.Append(wx.ID_ANY, 'Visualizer', 'Toggle visibility of visualizer window', wx.ITEM_CHECK)
        window_menu.Check(self.cameraevf_item.GetId(), False)
        window_menu.Check(self.command_item.GetId(), True)
        window_menu.Check(self.console_item.GetId(), True)
        window_menu.Check(self.controller_item.GetId(), True)
        window_menu.Check(self.visualizer_item.GetId(), True)
        self.Bind(wx.EVT_MENU, self.update_cameraevf_panel, self.cameraevf_item)
        self.Bind(wx.EVT_MENU, self.update_command_panel, self.command_item)
        self.Bind(wx.EVT_MENU, self.update_console_panel, self.console_item)
        self.Bind(wx.EVT_MENU, self.update_controller_panel, self.controller_item)
        self.Bind(wx.EVT_MENU, self.update_visualizer_panel, self.visualizer_item)
        window_menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, None, window_menu.Append(wx.ID_ANY, 'Window Preferences...', 'Open window preferences', wx.ITEM_NORMAL))

        # Help menu
        help_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, None, help_menu.Append(wx.ID_ANY, 'COPIS &Help...\tF1', 'Open COPIS help menu', wx.ITEM_NORMAL))
        help_menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, self.open_copis_website, help_menu.Append(wx.ID_ANY, '&Visit COPIS website\tCtrl+F1', 'Open www.copis3d.org', wx.ITEM_NORMAL))
        self.Bind(wx.EVT_MENU, None, help_menu.Append(wx.ID_ANY, '&About COPIS...', 'Show about dialog', wx.ITEM_NORMAL))

        self.menubar.Append(file_menu, '&File')
        self.menubar.Append(edit_menu, '&Edit')
        self.menubar.Append(view_menu, '&View')
        self.menubar.Append(tools_menu, '&Tools')
        self.menubar.Append(window_menu, '&Window')
        self.menubar.Append(help_menu, '&Help')

        self.SetMenuBar(self.menubar)

    def update_menubar(self):
        pass

    def open_preferences_frame(self, event):
        self.preferences_frame = ConfigPreferenceFrame()
        self.preferences_frame.Show()

    def update_statusbar(self, event):
        if self.statusbar_item.IsChecked():
            self.init_statusbar()
        else:
            if self.GetStatusBar() is not None:
                self.GetStatusBar().Destroy()

    def open_pathgen_frame(self, event):
        self.pathgen_frame = PathGeneratorFrame()
        self.pathgen_frame.Show()

    def update_cameraevf_panel(self, event):
        pass

    def update_command_panel(self, event):
        pass

    def update_console_panel(self, event):
        pass

    def update_controller_panel(self, event):
        pass

    def update_visualizer_panel(self, event):
        pass

    def open_copis_website(self, event):
        wx.LaunchDefaultBrowser('http://www.copis3d.org/')

    def quit(self, event):
        self._mgr.UnInit()
        self.Destroy()

    def rightClick(self, event):
        self.PopupMenu(MyPopupMenu(self), event.GetPosition())

    def initEDSDK(self):
        if self.is_edsdk_on:
            return

        import utils.edsdk_object

        self.edsdk_object = utils.edsdk_object
        self.edsdk_object.initialize(self.console_panel)
        self.is_edsdk_on = True
        self.getCameraList()

    def getCameraList(self):
        self.cam_list = self.edsdk_object.CameraList()
        cam_count = self.cam_list.get_count()

        message = str(cam_count)
        if cam_count == 0:
            message = 'There is no camera '

        elif cam_count == 1:
            message += ' camera is '
        else:
            message += ' cameras are '
        message += 'connected.'

        self.console_panel.print(message)

        for i in range(cam_count):
            camid = self.visualizer_panel.add_camera(camid=i)
            self.controller_panel.masterCombo.Append('camera ' + camid)

    def get_selected_camera(self):
        if self.selected_cam:
            return self.selected_cam
        return None

    def set_selected_camera(self, camid):
        # Check if selection is the same as previous selection
        new_selected = self.visualizer_panel.get_camera_by_id(camid)
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
            if self.cam_list[camid]:
                self.parent.cam_list.set_selected_cam_by_id(camid)

        # refresh canvas
        self.visualizer_panel.set_dirty()

        # refresh combobox
        self.controller_panel.masterCombo.SetSelection(camid)

    def terminateEDSDK(self):
        if not self.is_edsdk_on:
            return

        self.is_edsdk_on = False

        if self.cam_list:
            self.cam_list.terminate()
            self.cam_list = []

    def __del__(self):
        pass
