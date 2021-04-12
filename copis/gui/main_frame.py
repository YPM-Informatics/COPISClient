# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

"""MainWindow class."""

from ctypes import *
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import wx
import wx.lib.agw.aui as aui
import wx.svg as svg
from pydispatch import dispatcher
from wx.lib.agw.aui.aui_constants import *
from wx.lib.agw.aui.aui_utilities import (ChopText, GetBaseColour,
                                          IndentPressedBitmap, StepColour,
                                          TakeScreenShot)

from gui.about import *
from gui.panels.console import ConsolePanel
from gui.panels.controller import ControllerPanel
from gui.panels.evf import EvfPanel
from gui.panels.properties import PropertiesPanel
from gui.panels.timeline import TimelinePanel
from gui.panels.toolbar import ToolbarPanel
from gui.panels.visualizer import VisualizerPanel
from gui.pathgen_frame import *
from gui.pref_frame import *
from gui.wxutils import create_scaled_bitmap, set_dialog
from helpers import Point3, Point5
from store import Store

class MainWindow(wx.Frame):
    """Main window.

    Manages menubar, statusbar, and aui manager.

    Attributes:
        console_panel: A pointer to the console panel.
        controller_panel: A pointer to the controller panel.
        evf_panel: A pointer to the electronic viewfinder panel.
        properties_panel: A pointer to the properties panel.
        timeline_panel: A pointer to the timeline management panel.
        toolbar_panel: A pointer to the toolbar panel.
        visualizer_panel: A pointer to the visualizer panel.
    """

    _FILE_DIALOG_WILDCARD = 'COPIS Files (*.copis)|*.copis|All Files (*.*)|*.*'

    def __init__(self, *args, **kwargs) -> None:
        """Inits MainWindow with constructors."""
        super(MainWindow, self).__init__(*args, **kwargs)
        self.core = wx.GetApp().core
        # set minimum size to show whole interface properly
        self.MinSize = wx.Size(800, 575)

        # project saving
        self.project_dirty = False
        self._menubar = None
        self._mgr = None

        # dictionary of panels and menu items
        self.panels = {}
        self.menuitems = {}

        # initialize gui
        self.init_statusbar()
        self.init_menubar()
        self.init_mgr()

        self._store = Store()

        # TODO: re-enable liveview
        # self.add_evf_pane()

        self.Centre()
        self._mgr.Bind(aui.EVT_AUI_PANE_CLOSE, self.on_pane_close)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def init_statusbar(self) -> None:
        """Initialize statusbar."""
        if self.StatusBar is not None:
            return

        self.CreateStatusBar(1)
        self.SetStatusText('Ready')

    # --------------------------------------------------------------------------
    # Menubar related methods
    # --------------------------------------------------------------------------

    def init_menubar(self) -> None:
        """Initialize menubar.

        Menu tree:
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
        if self._menubar is not None:
            return

        self._menubar = wx.MenuBar(0)

        # File menu
        file_menu = wx.Menu()

        _item = wx.MenuItem(None, wx.ID_ANY, '&New Project\tCtrl+N', 'Create new project')
        _item.Bitmap = create_scaled_bitmap('add', 16)
        self.Bind(wx.EVT_MENU, self.on_new_project, file_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, '&Open...\tCtrl+O', 'Open project')
        _item.Bitmap = create_scaled_bitmap('open_in_new', 16)
        self.Bind(wx.EVT_MENU, self.on_open, file_menu.Append(_item))
        file_menu.AppendSeparator()

        _item = wx.MenuItem(None, wx.ID_ANY, '&Save\tCtrl+S', 'Save project')
        _item.Bitmap = create_scaled_bitmap('save', 16)
        self.Bind(wx.EVT_MENU, self.on_save, file_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, 'Save &As...\tCtrl+Shift+S', 'Save project as')
        self.Bind(wx.EVT_MENU, self.on_save_as, file_menu.Append(_item))
        file_menu.AppendSeparator()

        _item = wx.MenuItem(None, wx.ID_ANY, '&Import GCODE...', '')
        _item.Bitmap = create_scaled_bitmap('get_app', 16)
        self.Bind(wx.EVT_MENU, None, file_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, 'E&xport GCODE\tF8', '')
        _item.Bitmap = create_scaled_bitmap('publish', 16)
        self.Bind(wx.EVT_MENU, None, file_menu.Append(_item))
        file_menu.AppendSeparator()

        _item = wx.MenuItem(None, wx.ID_ANY, 'E&xit\tAlt+F4', 'Close the program')
        _item.Bitmap = create_scaled_bitmap('exit_to_app', 16)
        self.Bind(wx.EVT_MENU, self.on_exit, file_menu.Append(_item))

        # Edit menu
        edit_menu = wx.Menu()
        _item = wx.MenuItem(None, wx.ID_ANY, '&Keyboard Shortcuts...', 'Open keyboard shortcuts')
        self.Bind(wx.EVT_MENU, None, edit_menu.Append(_item))
        edit_menu.AppendSeparator()

        _item = wx.MenuItem(None, wx.ID_ANY, '&Preferences', 'Open preferences')
        _item.Bitmap = create_scaled_bitmap('tune', 16)
        self.Bind(wx.EVT_MENU, self.open_preferences_frame, edit_menu.Append(_item))

        # View menu
        view_menu = wx.Menu()
        self.statusbar_menuitem = view_menu.Append(wx.ID_ANY, '&Status &Bar', 'Toggle status bar visibility', wx.ITEM_CHECK)
        view_menu.Check(self.statusbar_menuitem.Id, True)
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
        _item.Bitmap = create_scaled_bitmap('tune', 16)
        self.Bind(wx.EVT_MENU, None, window_menu.Append(_item))

        # Help menu
        help_menu = wx.Menu()
        _item = wx.MenuItem(None, wx.ID_ANY, 'COPIS &Help...\tF1', 'Open COPIS help menu')
        _item.Bitmap = create_scaled_bitmap('help_outline', 16)
        self.Bind(wx.EVT_MENU, None, help_menu.Append(_item))
        help_menu.AppendSeparator()

        _item = wx.MenuItem(None, wx.ID_ANY, '&Visit COPIS website\tCtrl+F1', 'Open www.copis3d.org')
        _item.Bitmap = create_scaled_bitmap('open_in_new', 16)
        self.Bind(wx.EVT_MENU, self.open_copis_website, help_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, '&About COPIS...', 'Show about dialog')
        _item.Bitmap = create_scaled_bitmap('info', 16)
        self.Bind(wx.EVT_MENU, self.open_about_dialog, help_menu.Append(_item))

        self._menubar.Append(file_menu, '&File')
        self._menubar.Append(edit_menu, '&Edit')
        self._menubar.Append(view_menu, '&View')
        self._menubar.Append(tools_menu, '&Tools')
        self._menubar.Append(window_menu, '&Window')
        self._menubar.Append(help_menu, '&Help')
        self.SetMenuBar(self._menubar)

    def on_new_project(self, event: wx.CommandEvent) -> None:
        """TODO: Implement project file/directory creation
        """
        pass

    def on_open(self, event: wx.CommandEvent) -> None:
        """Open 'open' dialog.

        TODO: Implement reading file/directory
        """
        if self.project_dirty:
            if wx.MessageBox('Current project has not been saved. Proceed?', 'Please confirm',
                             wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
                return

        with wx.FileDialog(self, 'Open Project File', wildcard = self._FILE_DIALOG_WILDCARD,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            path = fileDialog.Path
            try:
                self.do_load_project(path)
            except Exception as e:
                wx.LogError(str(e))

    def on_save(self, event: wx.CommandEvent) -> None:
        """Open 'save' dialog.

        TODO: Implement saving file/directory to disk
        """

    def on_save_as(self, event: wx.CommandEvent) -> None:
        """Open 'save as' dialog.

         TODO: Implement saving as file/directory to disk
        """
        with wx.FileDialog(
            self, 'Save Project As', wildcard = self._FILE_DIALOG_WILDCARD,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            # save the current contents in the file
            path = file_dialog.Path
            try:
                with open(path, 'w') as file:
                    self.do_save_project(file)
            except IOError:
                wx.LogError(f'Could not save in file "{path}".')

    def do_save_project(self, file: Path) -> None:
        """Save project to file Path. TODO: Implement"""
        self.project_dirty = False
        print(file)

    def do_load_project(self, file: Path) -> None:
        """Load project from file Path. TODO: Implement"""
        script = {
            'actions': [],
            'devices': []
        }

        script = self._store.load(file, script)
        self.core.actions.clear()
        self.core.devices.clear()
        self.core.actions.extend(script['actions'])
        self.core.devices.extend(script['devices'])

    def update_statusbar(self, event: wx.CommandEvent) -> None:
        """Update status bar visibility based on menu item."""
        if event.IsChecked():
            self.StatusBar.Show()
        else:
            self.StatusBar.Hide() # or .Show(False)
        self._mgr.Update()

    def update_menubar(self) -> None:
        pass

    def open_preferences_frame(self, _) -> None:
        preferences_dialog = PreferenceFrame(self)
        preferences_dialog.Show()

    def open_pathgen_frame(self, _) -> None:
        pathgen_frame = PathgenFrame(self)
        pathgen_frame.Show()

    def open_copis_website(self, _) -> None:
        wx.LaunchDefaultBrowser('http://www.copis3d.org/')

    def open_about_dialog(self, _) -> None:
        about = AboutDialog(self)
        about.Show()

    def on_exit(self, event: wx.CommandEvent) -> None:
        """On menu close, exit application."""
        self.Close()

    # --------------------------------------------------------------------------
    # AUI related methods
    # --------------------------------------------------------------------------

    def init_mgr(self) -> None:
        """Initialize AuiManager and attach panes.

        NOTE: We are NOT USING wx.aui, but wx.lib.agw.aui, a pure Python
        implementation of wx.aui. As such, the correct documentation on
        wxpython.org should begin with
        https://wxpython.org/Phoenix/docs/html/wx.lib.agw.aui rather than
        https://wxpython.org/Phoenix/docs/html/wx.aui.
        """
        if self._mgr is not None:
            return

        # create auimanager and set flags
        self._mgr = aui.AuiManager(self, agwFlags=
            aui.AUI_MGR_ALLOW_FLOATING |
            aui.AUI_MGR_TRANSPARENT_DRAG |
            aui.AUI_MGR_TRANSPARENT_HINT |
            aui.AUI_MGR_HINT_FADE |
            aui.AUI_MGR_LIVE_RESIZE |
            aui.AUI_MGR_AUTONB_NO_CAPTION)

        # set auto notebook style
        self._mgr.SetAutoNotebookStyle(
            aui.AUI_NB_TOP |
            aui.AUI_NB_TAB_SPLIT |
            aui.AUI_NB_TAB_MOVE |
            aui.AUI_NB_SCROLL_BUTTONS |
            aui.AUI_NB_WINDOWLIST_BUTTON |
            aui.AUI_NB_MIDDLE_CLICK_CLOSE |
            aui.AUI_NB_CLOSE_ON_ACTIVE_TAB |
            aui.AUI_NB_TAB_FLOAT)

        # set aui colors and style
        # see https://wxpython.org/Phoenix/docs/html/wx.lib.agw.aui.dockart.AuiDefaultDockArt.html
        dockart = aui.AuiDefaultDockArt()
        dockart.SetMetric(aui.AUI_DOCKART_SASH_SIZE, 3)
        dockart.SetMetric(aui.AUI_DOCKART_CAPTION_SIZE, 18)
        dockart.SetMetric(aui.AUI_DOCKART_PANE_BUTTON_SIZE, 16)
        dockart.SetColor(aui.AUI_DOCKART_BACKGROUND_COLOUR, wx.SystemSettings().GetColour(wx.SYS_COLOUR_MENU))
        dockart.SetColor(aui.AUI_DOCKART_BACKGROUND_GRADIENT_COLOUR, wx.SystemSettings().GetColour(wx.SYS_COLOUR_MENU))
        dockart.SetColor(aui.AUI_DOCKART_SASH_COLOUR, wx.SystemSettings().GetColour(wx.SYS_COLOUR_MENU))
        dockart.SetColor(aui.AUI_DOCKART_ACTIVE_CAPTION_COLOUR, '#FFFFFF')
        dockart.SetColor(aui.AUI_DOCKART_INACTIVE_CAPTION_COLOUR, '#FFFFFF')
        dockart.SetMetric(aui.AUI_DOCKART_GRADIENT_TYPE, aui.AUI_GRADIENT_NONE)
        self._mgr.SetArtProvider(dockart)

        tabart = CustomAuiTabArt()
        self._mgr.SetAutoNotebookTabArt(tabart)

        # initialize relevant panels
        self.panels['visualizer'] = VisualizerPanel(self)
        self.panels['console'] = ConsolePanel(self)
        self.panels['timeline'] = TimelinePanel(self)
        self.panels['controller'] = ControllerPanel(self)
        self.panels['properties'] = PropertiesPanel(self)
        self.panels['toolbar'] = ToolbarPanel(self)

        # add visualizer panel
        self._mgr.AddPane(
            self.panels['visualizer'], aui.AuiPaneInfo(). \
            Name('visualizer').Caption('Visualizer'). \
            Dock().Center().MaximizeButton().MinimizeButton(). \
            DefaultPane().MinSize(350, 250))

        # add console, timeline panel
        self._mgr.AddPane(
            self.panels['console'], aui.AuiPaneInfo(). \
            Name('console').Caption('Console'). \
            Dock().Bottom().Position(0).Layer(0). \
            MinSize(280, 180).Show(True))
        self._mgr.AddPane(
            self.panels['timeline'], aui.AuiPaneInfo(). \
            Name('timeline').Caption('Timeline'). \
            Dock().Bottom().Position(1).Layer(0). \
            MinSize(280, 180).Show(True),
            target=self._mgr.GetPane('console'))

        # add properties and controller panel
        self._mgr.AddPane(
            self.panels['properties'], aui.AuiPaneInfo(). \
            Name('properties').Caption('Properties'). \
            Dock().Right().Position(0).Layer(1). \
            MinSize(280, 200).Show(True))
        self._mgr.AddPane(
            self.panels['controller'], aui.AuiPaneInfo(). \
            Name('controller').Caption('Controller'). \
            Dock().Right().Position(1).Layer(1). \
            MinSize(280, 200).Show(True))

        # set first tab of all auto notebooks as the one selected
        for notebook in self._mgr.GetNotebooks():
            notebook.SetSelection(0)

        # add toolbar panel
        self.panels['toolbar'].Realize()
        self._mgr.AddPane(
            self.panels['toolbar'], aui.AuiPaneInfo().
            Name('toolbar').Caption('Toolbar'). \
            ToolbarPane().BottomDockable(False). \
            Top().Layer(10))

        self._mgr.Update()

    def add_evf_pane(self) -> None:
        """Initialize camera liveview panel.

        TODO!
        """
        if self.core.edsdk.num_cams == 0:
            return

        self.panels['evf'] = EvfPanel(self)
        self._mgr.AddPane(
            self.panels['evf'], aui.AuiPaneInfo(). \
            Name('Evf').Caption('Live View'). \
            Float().Right().Position(1).Layer(0). \
            MinSize(600, 420).MinimizeButton(True).DestroyOnClose(True).MaximizeButton(True))
        self.Update()

    def update_console_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide console panel."""
        self._mgr.ShowPane(self.console_panel, event.IsChecked())

    def update_controller_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide controller panel."""
        self._mgr.ShowPane(self.controller_panel, event.IsChecked())

    def update_evf_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide evf panel."""
        self._mgr.ShowPane(self.evf_panel, event.IsChecked())

    def update_properties_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide properties panel."""
        self._mgr.ShowPane(self.properties_panel, event.IsChecked())

    def update_timeline_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide timeline panel."""
        self._mgr.ShowPane(self.timeline_panel, event.IsChecked())

    def update_visualizer_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide visualizer panel."""
        self._mgr.ShowPane(self.visualizer_panel, event.IsChecked())

    def on_pane_close(self, event: aui.framemanager.AuiManagerEvent) -> None:
        """Update menu itmes in the Window menu when a pane has been closed."""
        pane = event.GetPane()

        # if closed pane is a notebook, process and hide all pages in the notebook
        if pane.IsNotebookControl():
            notebook = pane.window
            for i in range(notebook.GetPageCount()):
                nb_pane = self._mgr.GetPane(notebook.GetPage(i))
                self._mgr.ShowPane(self.panels[nb_pane.name], False)
                self.menuitems[nb_pane.name].Check(False)
        else:
            self._mgr.ShowPane(self.panels[pane.name], False)
            self.menuitems[pane.name].Check(False)

        # if pane.name == 'Evf':
        #     pane.window.timer.Stop()
        #     pane.window.on_destroy()
        #     self.DetachPane(pane.window)
        #     pane.window.Destroy()

        print('hidden', pane.name)


    # --------------------------------------------------------------------------
    # Accessor methods
    # --------------------------------------------------------------------------

    @property
    def console_panel(self) -> ConsolePanel:
        return self.panels['console']

    @property
    def controller_panel(self) -> ControllerPanel:
        return self.panels['controller']

    @property
    def evf_panel(self) -> EvfPanel:
        return self.panels['evf']

    @property
    def properties_panel(self) -> PropertiesPanel:
        return self.panels['properties']

    @property
    def timeline_panel(self) -> TimelinePanel:
        return self.panels['timeline']

    @property
    def toolbar_panel(self) -> ToolbarPanel:
        return self.panels['toolbar']

    @property
    def visualizer_panel(self) -> VisualizerPanel:
        return self.panels['visualizer']

    def on_close(self, event: wx.CloseEvent) -> None:
        """On EVT_CLOSE, exit application."""
        event.StopPropagation()

        if self.project_dirty:
            if wx.MessageBox('Current project has not been saved. Proceed?', 'Please confirm',
                             wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
                return

        self._mgr.UnInit()
        self.Destroy()

    def __del__(self) -> None:
        pass


class CustomAuiTabArt(aui.AuiDefaultTabArt):
    """Custom tab art for SetAutoNotebookTabArt.

    Derived from
    https://github.com/wxWidgets/Phoenix/blob/master/wx/lib/agw/aui/tabart.py.
    """

    def __init__(self):
        """ Default class constructor. """
        aui.AuiDefaultTabArt.__init__(self)

        self._normal_font.PointSize -= 1
        self._selected_font.PointSize -= 1
        self._measuring_font.PointSize -= 1

    def SetDefaultColours(self, base_colour=None):
        """
        Sets the default colours, which are calculated from the given base colour.
        :param `base_colour`: an instance of :class:`wx.Colour`. If defaulted to ``None``, a colour
         is generated accordingly to the platform and theme.
        """
        if base_colour is None:
            base_colour = GetBaseColour()

        self.SetBaseColour(base_colour)
        self._border_colour = StepColour(base_colour, 80)
        self._border_pen = wx.Pen(StepColour(self._border_colour, 130))

        self._background_top_colour = StepColour(base_colour, 170)
        self._background_bottom_colour = StepColour(base_colour, 170)

        self._tab_top_colour =  wx.WHITE
        self._tab_bottom_colour = wx.WHITE
        self._tab_gradient_highlight_colour = wx.WHITE

        self._tab_inactive_top_colour = self._background_top_colour
        self._tab_inactive_bottom_colour = self._background_bottom_colour

        self._tab_text_colour = lambda page: page.text_colour
        self._tab_disabled_text_colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)

    def DrawBackground(self, dc, wnd, rect):
        """
        Draws the tab area background.
        :param `dc`: a :class:`wx.DC` device context;
        :param `wnd`: a :class:`wx.Window` instance object;
        :param wx.Rect `rect`: the tab control rectangle.
        """

        self._buttonRect = wx.Rect()

        # draw background
        agwFlags = self.GetAGWFlags()
        if agwFlags & AUI_NB_BOTTOM:
            r = wx.Rect(rect.x-1, rect.y-1, rect.width+2, rect.height+2)
        else: #for AUI_NB_TOP
            r = wx.Rect(rect.x-1, rect.y-1, rect.width+2, rect.height+2)

        dc.SetBrush(wx.Brush(self._background_top_colour))
        dc.DrawRectangle(r)

        dc.SetPen(self._border_pen)
        dc.DrawLine(0, rect.GetHeight()-1, rect.GetWidth(), rect.GetHeight()-1)

    def GetTabSize(self, dc, wnd, caption, bitmap, active, close_button_state, control=None):
        tab_size, x_extent = aui.AuiDefaultTabArt.GetTabSize(self, dc, wnd, caption, bitmap,
                                                             active, close_button_state, control)

        tab_width, tab_height = tab_size

        # modify tab height
        tab_height -= 6
        tab_width += 4
        x_extent += 4

        return (tab_width, tab_height), x_extent

    def DrawTab(self, dc, wnd, page, in_rect, close_button_state, paint_control=False):
        """
        Draws a single tab.
        :param `dc`: a :class:`wx.DC` device context;
        :param `wnd`: a :class:`wx.Window` instance object;
        :param `page`: the tab control page associated with the tab;
        :param wx.Rect `in_rect`: rectangle the tab should be confined to;
        :param integer `close_button_state`: the state of the close button on the tab;
        :param bool `paint_control`: whether to draw the control inside a tab (if any) on a :class:`MemoryDC`.
        """

        # a flat, minimal style

        # if the caption is empty, measure some temporary text
        caption = page.caption
        if not caption:
            caption = "Xj"

        dc.SetFont(self._normal_font)
        normal_textx, normal_texty, dummy = dc.GetFullMultiLineTextExtent(caption)

        control = page.control

        # figure out the size of the tab
        tab_size, x_extent = self.GetTabSize(dc, wnd, page.caption, page.bitmap,
                                             page.active, close_button_state, control)

        tab_height = tab_size[1] + 6
        tab_width = tab_size[0]
        tab_x = in_rect.x - 6
        tab_y = in_rect.y + in_rect.height - tab_height + 3

        caption = page.caption

        # select pen, brush and font for the tab to be drawn
        dc.SetFont(self._normal_font)
        textx, texty = normal_textx, normal_texty

        if not page.enabled:
            dc.SetTextForeground(self._tab_disabled_text_colour)
            pagebitmap = page.dis_bitmap
        else:
            dc.SetTextForeground(self._tab_text_colour(page))
            pagebitmap = page.bitmap

        # create points that will make the tab outline

        clip_width = tab_width
        if tab_x + clip_width > in_rect.x + in_rect.width:
            clip_width = in_rect.x + in_rect.width - tab_x

        # since the above code above doesn't play well with WXDFB or WXCOCOA,
        # we'll just use a rectangle for the clipping region for now --
        dc.SetClippingRegion(tab_x, tab_y, clip_width+1, tab_height-3)

        agwFlags = self.GetAGWFlags()

        wxPoint = wx.Point  # local opt
        if agwFlags & AUI_NB_BOTTOM:
            border_points = [wxPoint(tab_x,             tab_y),
                             wxPoint(tab_x,             tab_y+tab_height-4),
                             wxPoint(tab_x+tab_width,   tab_y+tab_height-4),
                             wxPoint(tab_x+tab_width,   tab_y)]

        else: #if (agwFlags & AUI_NB_TOP)
            border_points = [wxPoint(tab_x,             tab_y+tab_height-4),
                             wxPoint(tab_x,             tab_y),
                             wxPoint(tab_x+tab_width,   tab_y),
                             wxPoint(tab_x+tab_width,   tab_y+tab_height-4)]

        drawn_tab_yoff = border_points[1].y
        drawn_tab_height = border_points[0].y - border_points[1].y

        if page.active:
            # draw active tab
            r = wx.Rect(tab_x, tab_y, tab_width, tab_height)

            dc.SetPen(wx.Pen(self._tab_top_colour))
            dc.SetBrush(wx.Brush(self._tab_top_colour))
            dc.DrawRectangle(r)

        else:
            # draw inactive tab
            r = wx.Rect(tab_x, tab_y, tab_width, tab_height)

            dc.SetPen(wx.Pen(self._tab_inactive_top_colour))
            dc.SetBrush(wx.Brush(self._tab_inactive_top_colour))
            dc.DrawRectangle(r)

        # draw tab outline
        dc.SetPen(self._border_pen)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawPolygon(border_points)

        # remove bottom border of active tab
        if page.active:
            dc.SetPen(wx.Pen(self._tab_bottom_colour))
            dc.DrawLine(border_points[0].x+1, border_points[0].y,
                        border_points[3].x, border_points[3].y)

        text_offset = tab_x + 4
        close_button_width = 0

        if close_button_state != AUI_BUTTON_STATE_HIDDEN:
            close_button_width = self._active_close_bmp.GetWidth()

            if agwFlags & AUI_NB_CLOSE_ON_TAB_LEFT:
                text_offset += close_button_width - 5

        bitmap_offset = 0

        if pagebitmap.IsOk():

            bitmap_offset = tab_x + 8
            if agwFlags & AUI_NB_CLOSE_ON_TAB_LEFT and close_button_width:
                bitmap_offset += close_button_width - 5

            # draw bitmap
            dc.DrawBitmap(pagebitmap,
                          bitmap_offset,
                          drawn_tab_yoff + (drawn_tab_height/2) - (pagebitmap.GetHeight()/2),
                          True)

            text_offset = bitmap_offset + pagebitmap.GetWidth()
            text_offset += 3 # bitmap padding

        else:

            if agwFlags & AUI_NB_CLOSE_ON_TAB_LEFT == 0 or not close_button_width:
                text_offset = tab_x + 8

        draw_text = ChopText(dc, caption, tab_width - (text_offset-tab_x) - close_button_width)

        ypos = drawn_tab_yoff + (drawn_tab_height)/2 - (texty/2) + 1

        offset_focus = text_offset
        if control:
            if control.GetPosition() != wxPoint(text_offset+1, ypos):
                control.SetPosition(wxPoint(text_offset+1, ypos))

            if not control.IsShown():
                control.Show()

            if paint_control:
                bmp = TakeScreenShot(control.GetScreenRect())
                dc.DrawBitmap(bmp, text_offset+1, ypos, True)

            controlW, controlH = control.GetSize()
            text_offset += controlW + 4
            textx += controlW + 4

        # draw tab text
        rectx, recty, dummy = dc.GetFullMultiLineTextExtent(draw_text)
        dc.DrawLabel(draw_text, wx.Rect(text_offset, ypos, rectx, recty))

        out_button_rect = wx.Rect()

        # draw close button if necessary
        if close_button_state != AUI_BUTTON_STATE_HIDDEN:

            bmp = self._disabled_close_bmp

            if close_button_state == AUI_BUTTON_STATE_HOVER:
                bmp = self._hover_close_bmp
            elif close_button_state == AUI_BUTTON_STATE_PRESSED:
                bmp = self._pressed_close_bmp

            shift = (agwFlags & AUI_NB_BOTTOM and [1] or [0])[0]

            if agwFlags & AUI_NB_CLOSE_ON_TAB_LEFT:
                rect = wx.Rect(tab_x + 4, tab_y + (tab_height - bmp.GetHeight())/2 - shift,
                               close_button_width, tab_height)
            else:
                rect = wx.Rect(tab_x + tab_width - close_button_width - 1,
                               tab_y + (tab_height - bmp.GetHeight())/2 - shift,
                               close_button_width, tab_height)

            rect = IndentPressedBitmap(rect, close_button_state)
            dc.DrawBitmap(bmp, rect.x, rect.y-1, True)

            out_button_rect = rect

        out_tab_rect = wx.Rect(tab_x, tab_y, tab_width, tab_height)

        dc.DestroyClippingRegion()

        return out_tab_rect, out_button_rect, x_extent
