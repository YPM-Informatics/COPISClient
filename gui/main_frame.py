#!/usr/bin/env python3

import wx
import wx.lib.agw.aui as aui
from ctypes import *

from gui.panels.cmd import CommandPanel
from gui.panels.console import ConsolePanel
from gui.panels.controller import ControllerPanel
from gui.panels.evf import EvfPanel
from gui.panels.paths import PathPanel
from gui.panels.properties import PropertiesPanel
from gui.panels.toolbar import ToolbarPanel
from gui.panels.visualizer import VisualizerPanel

# from gui.auimanager import AuiManager
from gui.pathgen_frame import *
from gui.preferences import *
from gui.about import *


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)

        self.menubar = None

        self._mgr = None

        # TODO: turn this into a dictionary?
        self.panels = {}
        self.menuitems = {}
        self.command_panel = None
        self.console_panel = None
        self.controller_panel = None
        self.evf_panel = None
        self.path_panel = None
        self.properties_panel = None
        self.toolbar_panel = None
        self.visualizer_panel = None

        self.preference_frame = None
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

        # initialize aui manager and panes
        self.init_mgr()

        self.Centre()
        self._mgr.Bind(aui.EVT_AUI_PANE_CLOSE, self.on_pane_close)
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
        self.Bind(wx.EVT_MENU, self.on_exit, file_menu.Append(wx.ID_EXIT, 'E&xit\tAlt+F4', 'Close the program'))

        # Edit menu
        edit_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, None, edit_menu.Append(wx.ID_ANY, '&Keyboard Shortcuts...', 'Open keyboard shortcuts'))
        edit_menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, self.open_preferences_dialog, edit_menu.Append(wx.ID_ANY, '&Preferences', 'Open preferences'))

        # View menu
        view_menu = wx.Menu()
        self.statusbar_menuitem = view_menu.Append(wx.ID_ANY, 'Status Bar', 'Toggle status bar visibility', wx.ITEM_CHECK)
        view_menu.Check(self.statusbar_menuitem.GetId(), True)
        self.Bind(wx.EVT_MENU, self.update_statusbar, self.statusbar_menuitem)

        # Tools menu
        tools_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, self.open_pathgen_frame, tools_menu.Append(wx.ID_ANY, 'Generate Path', 'Open path generator window'))

        # Window menu
        window_menu = wx.Menu()
        self.evf_menuitem = window_menu.Append(wx.ID_ANY, 'Camera EVF', 'Toggle visibility of camera EVF window', wx.ITEM_CHECK)
        window_menu.Check(self.evf_menuitem.GetId(), False)
        self.Bind(wx.EVT_MENU, self.update_evf_panel, self.evf_menuitem)
        self.command_menuitem = window_menu.Append(wx.ID_ANY, 'Command', 'Toggle visibility of command window', wx.ITEM_CHECK)
        window_menu.Check(self.command_menuitem.GetId(), True)
        self.Bind(wx.EVT_MENU, self.update_command_panel, self.command_menuitem)
        self.console_menuitem = window_menu.Append(wx.ID_ANY, 'Console', 'Toggle visibility of console window', wx.ITEM_CHECK)
        window_menu.Check(self.console_menuitem.GetId(), True)
        self.Bind(wx.EVT_MENU, self.update_console_panel, self.console_menuitem)
        self.controller_menuitem = window_menu.Append(wx.ID_ANY, 'Controller', 'Toggle visibility of controller window', wx.ITEM_CHECK)
        window_menu.Check(self.controller_menuitem.GetId(), True)
        self.Bind(wx.EVT_MENU, self.update_controller_panel, self.controller_menuitem)
        self.path_menuitem = window_menu.Append(wx.ID_ANY, 'Paths', 'Toggle visibility of paths window', wx.ITEM_CHECK)
        window_menu.Check(self.path_menuitem.GetId(), True)
        self.Bind(wx.EVT_MENU, self.update_path_panel, self.path_menuitem)
        self.properties_menuitem = window_menu.Append(wx.ID_ANY, 'Properties', 'Toggle visibility of camera properties window', wx.ITEM_CHECK)
        window_menu.Check(self.properties_menuitem.GetId(), True)
        self.Bind(wx.EVT_MENU, self.update_properties_panel, self.properties_menuitem)
        self.visualizer_menuitem = window_menu.Append(wx.ID_ANY, 'Visualizer', 'Toggle visibility of visualizer window', wx.ITEM_CHECK)
        window_menu.Check(self.visualizer_menuitem.GetId(), True)
        self.Bind(wx.EVT_MENU, self.update_visualizer_panel, self.visualizer_menuitem)
        window_menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, None, window_menu.Append(wx.ID_ANY, 'Window Preferences...', 'Open window preferences', wx.ITEM_NORMAL))

        # Help menu
        help_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, None, help_menu.Append(wx.ID_ANY, 'COPIS &Help...\tF1', 'Open COPIS help menu', wx.ITEM_NORMAL))
        help_menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, self.open_copis_website, help_menu.Append(wx.ID_ANY, '&Visit COPIS website\tCtrl+F1', 'Open www.copis3d.org', wx.ITEM_NORMAL))
        self.Bind(wx.EVT_MENU, self.open_about_dialog, help_menu.Append(wx.ID_ANY, '&About COPIS...', 'Show about dialog', wx.ITEM_NORMAL))

        self.menubar.Append(file_menu, '&File')
        self.menubar.Append(edit_menu, '&Edit')
        self.menubar.Append(view_menu, '&View')
        self.menubar.Append(tools_menu, '&Tools')
        self.menubar.Append(window_menu, '&Window')
        self.menubar.Append(help_menu, '&Help')

        self.SetMenuBar(self.menubar)

    def update_menubar(self):
        pass

    def init_mgr(self):
        if self._mgr is not None:
            return

        # create auimanager and set flags
        self._mgr = aui.AuiManager(managed_window=self, agwFlags=
            aui.AUI_MGR_ALLOW_FLOATING |
            aui.AUI_MGR_ALLOW_ACTIVE_PANE |
            aui.AUI_MGR_TRANSPARENT_DRAG |
            aui.AUI_MGR_TRANSPARENT_HINT |
            aui.AUI_MGR_HINT_FADE |
            aui.AUI_MGR_LIVE_RESIZE)

        # set auto notebook style
        self._mgr.SetAutoNotebookStyle(
            aui.AUI_NB_BOTTOM |
            aui.AUI_NB_SCROLL_BUTTONS |
            aui.AUI_NB_MIDDLE_CLICK_CLOSE |
            aui.AUI_NB_CLOSE_ON_ALL_TABS)

        # set panel colors and style
        dockart = aui.AuiDefaultDockArt()
        dockart.SetMetric(aui.AUI_DOCKART_SASH_SIZE, 2)
        dockart.SetMetric(aui.AUI_DOCKART_CAPTION_SIZE, 18)
        dockart.SetMetric(aui.AUI_DOCKART_PANE_BUTTON_SIZE, 16)
        dockart.SetColour(aui.AUI_DOCKART_ACTIVE_CAPTION_COLOUR, wx.Colour(100, 100, 100))
        dockart.SetColour(aui.AUI_DOCKART_INACTIVE_CAPTION_COLOUR, wx.Colour(210, 210, 210))
        dockart.SetColour(aui.AUI_DOCKART_BORDER_COLOUR, wx.Colour(140, 140, 140))
        dockart.SetMetric(aui.AUI_DOCKART_GRADIENT_TYPE, aui.AUI_GRADIENT_NONE)
        self._mgr.SetArtProvider(dockart)

        # add visualizer panel
        self.visualizer_panel = VisualizerPanel(self)
        self._mgr.AddPane(self.visualizer_panel, aui.AuiPaneInfo(). \
            Name('visualizer_panel').Caption('Visualizer'). \
            Dock().Center().MaximizeButton().MinimizeButton(). \
            DefaultPane().MinSize(150, 200))

        # add console and command panel
        self.console_panel = ConsolePanel(self)
        # self.panels['console_panel'] = ConsolePanel(self)
        console_paneinfo = aui.AuiPaneInfo(). \
            Name('console_panel').Caption('Console'). \
            Dock().Bottom().PinButton(). \
            Position(0).Layer(0).MinSize(50, 150)
        self.command_panel = CommandPanel(self)
        command_paneinfo = aui.AuiPaneInfo(). \
            Name('command_panel').Caption('Send Command'). \
            Dock().Bottom().PinButton(). \
            Position(1).Layer(0).MinSize(50, 150)
        self._mgr.AddPane(self.console_panel, console_paneinfo)
        self._mgr.AddPane(self.command_panel, command_paneinfo, target=console_paneinfo)

        # add controller and properties panel
        self.controller_panel = ControllerPanel(self)
        controller_paneinfo = aui.AuiPaneInfo(). \
            Name('controller_panel').Caption('Controller'). \
            Dock().Right().PinButton(). \
            Position(0).Layer(1).MinSize(200, 420)
        self.properties_panel = PropertiesPanel(self)
        properties_paneinfo = aui.AuiPaneInfo(). \
            Name('properties_panel').Caption('Properties'). \
            Dock().Right().PinButton(). \
            Position(1).Layer(1).MinSize(200, 50)
        self._mgr.AddPane(self.controller_panel, controller_paneinfo)
        self._mgr.AddPane(self.properties_panel, properties_paneinfo, target=controller_paneinfo)

        # set first tab of all auto notebooks as selected
        notebooks = self._mgr.GetNotebooks()
        for i in notebooks:
            i.SetSelection(0)

        # add path panel
        self.path_panel = PathPanel(self)
        self._mgr.AddPane(self.path_panel, aui.AuiPaneInfo(). \
            Name('path_panel').Caption('Paths'). \
            Dock().Right().PinButton(). \
            Position(2).Layer(1).MinSize(200, 50))

        # add toolbar panel
        self.toolbar_panel = ToolbarPanel(self)
        # self.toolbar_panel.Realize()
        self._mgr.AddPane(self.toolbar_panel, aui.AuiPaneInfo().
            Name('toolbar_panel').Caption('Toolbar'). \
            ToolbarPane().DockFixed(True). \
            Top().DestroyOnClose())

        # add camera evf panel
        self.evf_panel = None

        self._mgr.Update()

    def update_mgr(self):
        notebooks = self._mgr.GetNotebooks()

    def open_preferences_dialog(self, event):
        preferences_dialog = PreferenceDialog(self)
        preferences_dialog.Show()

    def update_statusbar(self, event):
        if self.statusbar_menuitem.IsChecked():
            self.init_statusbar()
        else:
            if self.GetStatusBar() is not None:
                self.GetStatusBar().Destroy()

    def open_pathgen_frame(self, event):
        pathgen_frame = PathGeneratorFrame(self)
        pathgen_frame.Show()

    def update_evf_panel(self, event):
        pass

    def update_command_panel(self, event):
        self._mgr.ShowPane(self.command_panel, self.command_menuitem.IsChecked())

    def update_console_panel(self, event):
        self._mgr.ShowPane(self.console_panel, self.console_menuitem.IsChecked())

    def update_controller_panel(self, event):
        self._mgr.ShowPane(self.controller_panel, self.controller_menuitem.IsChecked())

    def update_path_panel(self, event):
        self._mgr.ShowPane(self.path_panel, self.path_menuitem.IsChecked())

    def update_properties_panel(self, event):
        self._mgr.ShowPane(self.properties_panel, self.properties_menuitem.IsChecked())

    def update_visualizer_panel(self, event):
        self._mgr.ShowPane(self.visualizer_panel, self.visualizer_menuitem.IsChecked())

    def open_copis_website(self, event):
        wx.LaunchDefaultBrowser('http://www.copis3d.org/')

    def open_about_dialog(self, event):
        about = AboutDialog(self)
        about.Show()

    def on_pane_close(self, event):
        pane_list = ()
        # pane = event.GetPane()
        # # print(self._mgr.GetAttributes(event.GetPane()))
        # # print(type(pane.window) == 'wx.lib.agw.aui.auibook.AuiNotebook')
        # if isinstance(pane.window, aui.auibook.AuiNotebook):
        #     notebook = self._mgr.GetPane(pane.window)
        #     print(notebook.IsNotebookControl())
        #     print(notebook.GetPage(0))
        # else:
        #     if pane.name == 'command_panel':
        #         self.command_menuitem.Check(False)
        #     elif pane.name == 'console_panel':
        #         self.console_menuitem.Check(False)
        #     elif pane.name == 'controller_panel':
        #         self.controller_menuitem.Check(False)
        #     elif pane.name == 'evf_panel':
        #         self.evf_menuitem.Check(False)
        #     elif pane.name == 'path_panel':
        #         self.path_menuitem.Check(False)
        #     elif pane.name == 'properties_panel':
        #         self.properties_menuitem.Check(False)
        #     elif pane.name == 'toolbar_panel':
        #         self.toolbar_menuitem.Check(False)
        #     elif pane.name == 'visualizer_panel':
        #         self.visualizer_menuitem.Check(False)
        #     else:
        #         pass

    def quit(self, event):
        self._mgr.UnInit()
        self.Destroy()

    # TODO: figure out what this method does
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

    def on_exit(self, event):
        self.Close()

    def __del__(self):
        pass
