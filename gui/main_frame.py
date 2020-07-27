#!/usr/bin/env python3

import wx
import wx.svg as svg
import wx.lib.agw.aui as aui
from ctypes import *

from utils import svgbmp

from gui.panels.console import ConsolePanel
from gui.panels.controller import ControllerPanel
from gui.panels.evf import EvfPanel
from gui.panels.paths import PathPanel
from gui.panels.properties import PropertiesPanel
from gui.panels.timeline import TimelinePanel
from gui.panels.toolbar import ToolbarPanel
from gui.panels.visualizer import VisualizerPanel

from gui.pathgen_frame import *
from gui.pref_frame import *
# from gui.preferences import *
from gui.about import *


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)

        # set minimum size to show whole interface properly
        self.SetMinSize(wx.Size(800, 575))

        self.menubar = None
        self._mgr = None

        # dictionary of panels and menu items
        self.panels = {}
        self.menuitems = {}

        self.cam_list = []
        self.selected_cam = None
        self.is_edsdk_on = False
        self.edsdk_object = None
        self.project_dirty = False

        # initialize statusbar and menubar
        self.init_statusbar()
        self.init_menubar()

        # initialize aui manager
        self.init_mgr()

        self.Centre()
        self._mgr.Bind(aui.EVT_AUI_PANE_CLOSE, self.on_pane_close)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def init_statusbar(self):
        """Initialize statusbar."""
        if self.GetStatusBar() is not None:
            return

        self.CreateStatusBar(1, id=wx.ID_ANY)
        self.SetStatusText('Ready')

    def init_menubar(self):
        """Initialize menubar. Menu tree:

        - &Files
            - &New Project              Ctrl+N
            - &Open...                  Ctrl+O
              ---
            - &Save                     Ctrl+S
            - &Save As...               Ctrl+Shift+S
              ---
            - &Import GCODE...
            - &Generate GCODE...        F8
              ---
            - E&xit                     Alt+F4
        - &Edit
            - &Keyboard Shortcuts...
              ---
            - &Preferences
        - &View
            - [x] &Status Bar
        - &Tools
            - &Generate Path...
              ---
            - &Preferences
        - &Window
            - [ ] Camera EVF
            - [x] Console
            - [x] Controller
            - [x] Paths
            - [x] Properties
            - [x] Timeline
            - [x] Visualizer
              ---
            - Window &Preferences...
        - Help
            - COPIS &Help...            F1
              ---
            - &Visit COPIS website      Ctrl+F1
            - &About COPIS...
        """
        if self.menubar is not None:
            return

        self.menubar = wx.MenuBar(0)

        # File menu
        file_menu = wx.Menu()

        _item = wx.MenuItem(None, wx.ID_ANY, '&New Project\tCtrl+N', 'Create new project')
        _item.SetBitmap(svgbmp('img/add-24px.svg', 16))
        self.Bind(wx.EVT_MENU, self.on_new_project, file_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, '&Open...\tCtrl+O', 'Open project')
        _item.SetBitmap(svgbmp('img/open_in_new-24px.svg', 16))
        self.Bind(wx.EVT_MENU, self.on_open, file_menu.Append(_item))
        file_menu.AppendSeparator()

        _item = wx.MenuItem(None, wx.ID_ANY, '&Save\tCtrl+S', 'Save project')
        _item.SetBitmap(svgbmp('img/save-24px.svg', 16))
        self.Bind(wx.EVT_MENU, self.on_save, file_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, 'Save &As...\tCtrl+Shift+S', 'Save project as')
        self.Bind(wx.EVT_MENU, self.on_save_as, file_menu.Append(_item))
        file_menu.AppendSeparator()

        _item = wx.MenuItem(None, wx.ID_ANY, '&Import GCODE...', '')
        _item.SetBitmap(svgbmp('img/get_app-24px.svg', 16))
        self.Bind(wx.EVT_MENU, None, file_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, 'E&xport GCODE\tF8', '')
        _item.SetBitmap(svgbmp('img/publish-24px.svg', 16))
        self.Bind(wx.EVT_MENU, None, file_menu.Append(_item))
        file_menu.AppendSeparator()

        _item = wx.MenuItem(None, wx.ID_ANY, 'E&xit\tAlt+F4', 'Close the program')
        _item.SetBitmap(svgbmp('img/exit_to_app-24px.svg', 16))
        self.Bind(wx.EVT_MENU, self.on_exit, file_menu.Append(_item))

        # Edit menu
        edit_menu = wx.Menu()
        _item = wx.MenuItem(None, wx.ID_ANY, '&Keyboard Shortcuts...', 'Open keyboard shortcuts')
        self.Bind(wx.EVT_MENU, None, edit_menu.Append(_item))
        edit_menu.AppendSeparator()

        _item = wx.MenuItem(None, wx.ID_ANY, '&Preferences', 'Open preferences')
        _item.SetBitmap(svgbmp('img/tune-24px.svg', 16))
        self.Bind(wx.EVT_MENU, self.open_preferences_dialog, edit_menu.Append(_item))

        # View menu
        view_menu = wx.Menu()
        self.statusbar_menuitem = view_menu.Append(wx.ID_ANY, '&Status &Bar', 'Toggle status bar visibility', wx.ITEM_CHECK)
        view_menu.Check(self.statusbar_menuitem.GetId(), True)
        self.Bind(wx.EVT_MENU, self.update_statusbar, self.statusbar_menuitem)

        # Tools menu
        tools_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, self.open_pathgen_frame, tools_menu.Append(wx.ID_ANY, '&Generate Path...', 'Open path generator window'))

        # Window menu
        window_menu = wx.Menu()
        self.menuitems['evf'] = window_menu.Append(wx.ID_ANY, 'Camera EVF', 'Show/hide camera EVF window', wx.ITEM_CHECK)
        self.menuitems['evf'].Enable(False)
        self.Bind(wx.EVT_MENU, self.update_evf_panel, self.menuitems['evf'])
        self.menuitems['console'] = window_menu.Append(wx.ID_ANY, 'Console', 'Show/hide console window', wx.ITEM_CHECK)
        self.menuitems['console'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_console_panel, self.menuitems['console'])
        self.menuitems['controller'] = window_menu.Append(wx.ID_ANY, 'Controller', 'Show/hide controller window', wx.ITEM_CHECK)
        self.menuitems['controller'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_controller_panel, self.menuitems['controller'])
        self.menuitems['path'] = window_menu.Append(wx.ID_ANY, 'Paths', 'Show/hide paths window', wx.ITEM_CHECK)
        self.menuitems['path'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_path_panel, self.menuitems['path'])
        self.menuitems['properties'] = window_menu.Append(wx.ID_ANY, 'Properties', 'Show/hide camera properties window', wx.ITEM_CHECK)
        self.menuitems['properties'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_properties_panel, self.menuitems['properties'])
        self.menuitems['timeline'] = window_menu.Append(wx.ID_ANY, 'Timeline', 'Show/hide timeline window', wx.ITEM_CHECK)
        self.menuitems['timeline'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_timeline_panel, self.menuitems['timeline'])
        self.menuitems['visualizer'] = window_menu.Append(wx.ID_ANY, 'Visualizer', 'Show/hide visualizer window', wx.ITEM_CHECK)
        self.menuitems['visualizer'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_visualizer_panel, self.menuitems['visualizer'])
        window_menu.AppendSeparator()

        _item = wx.MenuItem(None, wx.ID_ANY, 'Window &Preferences...', 'Open window preferences')
        _item.SetBitmap(svgbmp('img/tune-24px.svg', 16))
        self.Bind(wx.EVT_MENU, None, window_menu.Append(_item))

        # Help menu
        help_menu = wx.Menu()
        _item = wx.MenuItem(None, wx.ID_ANY, 'COPIS &Help...\tF1', 'Open COPIS help menu')
        _item.SetBitmap(svgbmp('img/help_outline-24px.svg', 16))
        self.Bind(wx.EVT_MENU, None, help_menu.Append(_item))
        help_menu.AppendSeparator()

        _item = wx.MenuItem(None, wx.ID_ANY, '&Visit COPIS website\tCtrl+F1', 'Open www.copis3d.org')
        _item.SetBitmap(svgbmp('img/open_in_new-24px.svg', 16))
        self.Bind(wx.EVT_MENU, self.open_copis_website, help_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, '&About COPIS...', 'Show about dialog')
        _item.SetBitmap(svgbmp('img/info-24px.svg', 16))
        self.Bind(wx.EVT_MENU, self.open_about_dialog, help_menu.Append(_item))

        self.menubar.Append(file_menu, '&File')
        self.menubar.Append(edit_menu, '&Edit')
        self.menubar.Append(view_menu, '&View')
        self.menubar.Append(tools_menu, '&Tools')
        self.menubar.Append(window_menu, '&Window')
        self.menubar.Append(help_menu, '&Help')
        self.SetMenuBar(self.menubar)

    def on_new_project(self, event):
        pass

    def on_open(self, event):
        if self.project_dirty:
            if wx.MessageBox('Current project has not been saved. Proceed?', 'Please confirm',
                             wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
                return

        with wx.FileDialog(self, 'Open Project File', wildcard='XYZ files (*.xyz)|*.xyz',
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            path = fileDialog.GetPath()
            try:
                with open(path, 'r') as file:
                    self.do_load_project(file)
            except IOError:
                wx.LogError("Could not open file '%s'." % path)

    def on_save(self, event):
        pass

    def on_save_as(self, event):
        with wx.FileDialog(self, 'Save Project As', wildcard='XYZ files (*.xyz)|*.xyz',
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            # save the current contents in the file
            path = file_dialog.GetPath()
            try:
                with open(path, 'w') as file:
                    self.do_save_project(file)
            except IOError:
                wx.LogError("Could not save in file '%s'." % path)

    def do_save_project(self, file):
        self.project_dirty = False
        print(file)

    def do_load_project(self, file):
        print(file)

    def update_menubar(self):
        pass

    def open_preferences_dialog(self, _):
        # preferences_dialog = PreferenceDialog(self)
        preferences_dialog = PreferenceFrame(self)
        preferences_dialog.Show()

    def update_statusbar(self, event):
        if event.IsChecked():
            self.GetStatusBar().Show()
        else:
            self.GetStatusBar().Hide() # or .Show(False)
        self._mgr.Update()

    def open_pathgen_frame(self, _):
        pathgen_frame = PathgenFrame(self)
        pathgen_frame.Show()

    def open_copis_website(self, _):
        wx.LaunchDefaultBrowser('http://www.copis3d.org/')

    def open_about_dialog(self, _):
        about = AboutDialog(self)
        about.Show()

    def init_mgr(self):
        """Initialize AuiManager and attach panes.

        NOTE: We are NOT USING wx.aui, but wx.lib.agw.aui, a pure Python implementation of aui.
        As such, the correct documentation on wxpython.org should begin with
        https://wxpython.org/Phoenix/docs/html/wx.lib.agw.aui, rather than
        https://wxpython.org/Phoenix/docs/html/wx.aui.
        """
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
            aui.AUI_NB_TAB_MOVE |
            aui.AUI_NB_SCROLL_BUTTONS |
            aui.AUI_NB_MIDDLE_CLICK_CLOSE |
            aui.AUI_NB_CLOSE_ON_ALL_TABS)

        # set panel colors and style
        dockart = aui.AuiDefaultDockArt()
        dockart.SetMetric(aui.AUI_DOCKART_SASH_SIZE, 2)
        dockart.SetMetric(aui.AUI_DOCKART_CAPTION_SIZE, 18)
        dockart.SetMetric(aui.AUI_DOCKART_PANE_BUTTON_SIZE, 16)
        dockart.SetColour(aui.AUI_DOCKART_ACTIVE_CAPTION_COLOUR, wx.Colour(110, 110, 110))
        dockart.SetColour(aui.AUI_DOCKART_INACTIVE_CAPTION_COLOUR, wx.Colour(210, 210, 210))
        dockart.SetColour(aui.AUI_DOCKART_BORDER_COLOUR, wx.Colour(140, 140, 140))
        dockart.SetMetric(aui.AUI_DOCKART_GRADIENT_TYPE, aui.AUI_GRADIENT_NONE)
        self._mgr.SetArtProvider(dockart)

        # tabart = aui.AuiSimpleTabArt()
        tabart = aui.VC71TabArt()
        self._mgr.SetAutoNotebookTabArt(tabart)

        # initialize relevant panels
        self.panels['visualizer'] = VisualizerPanel(self)
        self.panels['console'] = ConsolePanel(self)
        self.panels['timeline'] = TimelinePanel(self)
        self.panels['controller'] = ControllerPanel(self)
        self.panels['properties'] = PropertiesPanel(self)
        self.panels['toolbar'] = ToolbarPanel(self)

        # add visualizer panel
        self._mgr.AddPane(self.panels['visualizer'], aui.AuiPaneInfo(). \
            Name('visualizer').Caption('Visualizer'). \
            Dock().Center().MaximizeButton().MinimizeButton(). \
            DefaultPane().MinSize(380, 250))

        # add console, timeline panel
        self._mgr.AddPane(self.panels['console'], aui.AuiPaneInfo(). \
            Name('console').Caption('Console'). \
            Dock().Bottom().Position(0).Layer(0). \
            MinSize(50, 150).Show(True))
        self._mgr.AddPane(self.panels['timeline'], aui.AuiPaneInfo(). \
            Name('timeline').Caption('Timeline'). \
            Dock().Bottom().Position(1).Layer(0). \
            MinSize(50, 150).Show(True),
            target=self._mgr.GetPane('console'))

        # add controller, properties, path panel
        self._mgr.AddPane(self.panels['controller'], aui.AuiPaneInfo(). \
            Name('controller').Caption('Controller'). \
            Dock().Right().Position(0).Layer(1). \
            MinSize(325, 420).Show(True))
        self._mgr.AddPane(self.panels['properties'], aui.AuiPaneInfo(). \
            Name('properties').Caption('Properties'). \
            Dock().Right().Position(1).Layer(1). \
            MinSize(200, 50).Show(True))
        self.panels['path'] = PathPanel(self)
        self._mgr.AddPane(self.panels['path'], aui.AuiPaneInfo(). \
            Name('path').Caption('Paths'). \
            Dock().Right().Position(2).Layer(1). \
            MinSize(200, 50).Show(True),
            target=self._mgr.GetPane('properties'))

        # set first tab of all auto notebooks as the one selected
        for notebook in self._mgr.GetNotebooks():
            notebook.SetSelection(0)

        # add toolbar panel
        self.panels['toolbar'].Realize()
        self._mgr.AddPane(self.panels['toolbar'], aui.AuiPaneInfo().
            Name('toolbar').Caption('Toolbar'). \
            ToolbarPane().BottomDockable(False). \
            Top().Layer(10))

        self._mgr.Update()

    def add_evf_pane(self):
        self.panels['evf'] = EvfPanel(self)
        self.AddPane(self.panels['evf'], aui.AuiPaneInfo(). \
            Name('Evf').Caption('Live View'). \
            Float().Right().Position(1).Layer(0). \
            MinSize(600, 420).MinimizeButton(True).DestroyOnClose(True).MaximizeButton(True))
        self.Update()

    def update_console_panel(self, event):
        self._mgr.ShowPane(self.console_panel, event.IsChecked())

    def update_controller_panel(self, event):
        self._mgr.ShowPane(self.controller_panel, event.IsChecked())

    def update_evf_panel(self, event):
        self._mgr.ShowPane(self.evf_panel, event.IsChecked())

    def update_path_panel(self, event):
        self._mgr.ShowPane(self.path_panel, event.IsChecked())

    def update_properties_panel(self, event):
        self._mgr.ShowPane(self.properties_panel, event.IsChecked())

    def update_timeline_panel(self, event):
        self._mgr.ShowPane(self.timeline_panel, event.IsChecked())

    def update_visualizer_panel(self, event):
        self._mgr.ShowPane(self.visualizer_panel, event.IsChecked())

    def on_pane_close(self, event):
        """Update ITEM_CHECK menuitems in the Window menu when a pane has been closed."""
        pane = event.GetPane()

        # if closed pane is a notebook, process and hide all pages in the notebook
        if pane.IsNotebookControl():
            notebook = pane.window
            for i in range(notebook.GetPageCount()):
                pane = self._mgr.GetPane(notebook.GetPage(i))
                self._mgr.ShowPane(self.panels[pane.name], False)
                self.menuitems[pane.name].Check(False)
        else:
            self.menuitems[pane.name].Check(False)

        # if pane.name == 'Evf':
        #     pane.window.timer.Stop()
        #     pane.window.on_destroy()
        #     self.DetachPane(pane.window)
        #     pane.window.Destroy()

    @property
    def console_panel(self):
        return self.panels['console']

    @property
    def controller_panel(self):
        return self.panels['controller']

    @property
    def evf_panel(self):
        return self.panels['evf']

    @property
    def path_panel(self):
        return self.panels['path']

    @property
    def properties_panel(self):
        return self.panels['properties']

    @property
    def timeline_panel(self):
        return self.panels['timeline']

    @property
    def toolbar_panel(self):
        return self.panels['toolbar']

    @property
    def visualizer_panel(self):
        return self.panels['visualizer']

    def initEDSDK(self):
        if self.is_edsdk_on:
            return

        import util.edsdk_object

        self.edsdk_object = util.edsdk_object
        self.edsdk_object.initialize(self.console_panel)
        self.is_edsdk_on = True
        self.get_camera_list()

    def get_camera_list(self):
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
        # check if selection is the same as previous selection
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

        # refresh canvas and combobox
        self.visualizer_panel.dirty = True
        self.controller_panel.masterCombo.SetSelection(camid)

    def terminate_edsdk(self):
        if not self.is_edsdk_on:
            return

        self.is_edsdk_on = False

        if self.cam_list:
            self.cam_list.terminate()
            self.cam_list = []

    def on_close(self, event):
        event.StopPropagation()
        if self.project_dirty:
            if wx.MessageBox('Current project has not been saved. Proceed?', 'Please confirm',
                             wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
                return

        self._mgr.UnInit()
        self.Destroy()

    def on_exit(self, event):
        self.Close()

    def __del__(self):
        pass
