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
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s (Line: %(lineno)d)',
    datefmt='%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(), logging.FileHandler('main_frame.log', mode='a')]
)

logger = logging.getLogger(__name__)
"""MainWindow class."""

import wx
import wx.lib.agw.aui as aui

from pydispatch import dispatcher
from glm import vec2, vec3

import copis.store as store

from copis.helpers import print_error_msg
from copis.globals import WindowState
from copis.classes import AABoxObject3D, CylinderObject3D, Action, Pose
from .about import AboutDialog
from .panels.console import ConsolePanel
from .panels.evf import EvfPanel
from .panels.machine_toolbar import MachineToolbar
from .panels.pathgen_toolbar import PathgenToolbar
from .panels.imaging_toolbar import ImagingToolbar
from .panels.properties import PropertiesPanel
from .panels.timeline import TimelinePanel
from .panels.viewport import ViewportPanel
from .panels.stats import StatsPanel
from .pref_frame import PreferenceFrame
from .proxy_dialogs import ProxygenCylinder, ProxygenAABB
from .wxutils import create_scaled_bitmap, show_msg_dialog, show_prompt_dialog
from .custom_tab_art import CustomAuiTabArt

from copis.gui import config_dialog
from copis.gui import profile_dialog

class MainWindow(wx.Frame):
    """Main window.
    Manages menubar, statusbar, and aui manager.
    Attributes:
        console_panel: A pointer to the console panel.
        evf_panel: A pointer to the electronic viewfinder panel.
        properties_panel: A pointer to the properties panel.
        timeline_panel: A pointer to the timeline management panel.
        viewport_panel: A pointer to the viewport panel.
        stats_panel: A pointer to the stats panel.
        machine_toolbar: A pointer to the machine toolbar.
        pathgen_toolbar: A pointer to the pathgen toolbar.
    """
    _FILES_WILDCARD = 'All Files (*.*)|*.*'
    _FILES_LEGACY_ACTIONS = 'COPIS legacy actions files (*.copis)|*.copis'
    _FILES_PROJECT = 'COPIS project files (*.cproj)|*.cproj'
    _COPIS_WEBSITE = 'http://www.copis3d.org/'
    _BOTTOM_PANE_MIN_SIZE = wx.Size(280, 150)
    _RIGHT_PANE_MIN_SIZE = wx.Size(280, 145)

    def __init__(self, chamber_dimensions, *args, **kwargs) -> None:
        """Initializes MainWindow with constructors."""
        super().__init__(*args, **kwargs)
        self.core = wx.GetApp().core
        # set minimum size to show whole interface properly
        min_size = self.core.config.application_settings.window_min_size
        self.MinSize = wx.Size(min_size.width, min_size.height)
        self._default_title = self.Title
        self.chamber_dimensions = chamber_dimensions
        #self._keep_last_session_imaging_path = False
        self._file_menu = None
        self._menubar = None
        self._mgr = None
        # dictionary of panels and menu items
        self.panels = {}
        self.menuitems = {}
        # initialize gui
        self.init_mgr()
        self.init_statusbar()
        self.init_menubar()
        self._mgr.Bind(aui.EVT_AUI_PANE_CLOSE, self.on_pane_close)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.numpoints = None
        # Bind listeners.
        dispatcher.connect(self._handle_project_dirty_changed, signal='ntf_project_dirty_changed')



    # --------------------------------------------------------------------------
    # Accessor methods
    # --------------------------------------------------------------------------

    #@property
    #def keep_last_session_imaging_path(self) -> bool:
    #    """Returns a flag indicating whether to keep the last session imaging path."""
    #    return self._keep_last_session_imaging_path

    #@keep_last_session_imaging_path.setter
    #def keep_last_session_imaging_path(self, value) -> None:
    #    self._keep_last_session_imaging_path = value

    @property
    def console_panel(self) -> ConsolePanel:
        """Returns the console panel."""
        return self.panels['console']

    @property
    def evf_panel(self) -> EvfPanel:
        """Returns the EVF panel."""
        return self.panels['evf'] if 'evf' in self.panels else None

    @property
    def properties_panel(self) -> PropertiesPanel:
        """Returns the properties panel."""
        return self.panels['properties']

    @property
    def timeline_panel(self) -> TimelinePanel:
        """Returns the timeline panel."""
        return self.panels['timeline']

    @property
    def viewport_panel(self) -> ViewportPanel:
        """Returns the viewport panel."""
        return self.panels['viewport']

    @property
    def stats_panel(self) -> StatsPanel:
        """Returns the stats panel."""
        return self.panels['stats']

    @property
    def machine_toolbar(self) -> MachineToolbar:
        """Returns the machine toolbar."""
        return self.panels['machine_toolbar']

    @property
    def pathgen_toolbar(self) -> PathgenToolbar:
        """Returns the path generation toolbar."""
        return self.panels['pathgen_toolbar']

    @property
    def imaging_toolbar(self) -> ImagingToolbar:
        """Returns the imaging toolbar."""
        return self.panels['imaging_toolbar']

    def _get_default_dir(self):
        return self.core.config.application_settings.last_output_path

    def _handle_project_dirty_changed(self, is_project_dirty: bool) -> None:
        project_path = self.core.project.path
        has_project_path = project_path is not None and len(project_path.strip()) > 0
        self._file_menu.Enable(wx.ID_NEW, is_project_dirty or has_project_path)
        self._file_menu.Enable(wx.ID_SAVE, is_project_dirty or has_project_path)
        project_name = '' if not project_path else store.get_file_base_name_no_ext(project_path)
        if is_project_dirty:
            project_name = f'*{project_name}'
        if len(project_name) > 0:
            self.Title = f'{project_name} - {self._default_title}'
        elif self.Title != self._default_title:
            self.Title = self._default_title

    def _populate_recent_projects(self):
        proj_list = self.core.config.application_settings.recent_projects
        if proj_list:
            ids = [wx.ID_FILE, wx.ID_FILE1, wx.ID_FILE2, wx.ID_FILE3, wx.ID_FILE4,
                   wx.ID_FILE5, wx.ID_FILE6, wx.ID_FILE7, wx.ID_FILE8, wx.ID_FILE9]
            menu = self._file_menu.FindItemById(wx.ID_JUMP_TO).SubMenu
            for item in menu.GetMenuItems():
                menu.Delete(item)
            for i, proj in enumerate(proj_list):
                rank = i + 1
                _item = wx.MenuItem(None, ids[i], f'&{str(rank)}: {proj}',
                    f'Recent project {rank}')
                self.Bind(wx.EVT_MENU, self.on_project_selected, menu.Append(_item))

            self._file_menu.Enable(wx.ID_JUMP_TO, True)
        else:
            self._file_menu.Enable(wx.ID_JUMP_TO, False)

    def _prompt_saving(self, caption, event):
        proceed = True
        if self.core.project.is_dirty:
            choice = show_prompt_dialog('The project was modified. Would you like to save it first?', caption, True)
            if choice == wx.ID_YES:
                self.on_save(event)
            elif choice == wx.ID_CANCEL:
                proceed = False
        return proceed

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
            - &File
                - &New Project              Ctrl+N
                - &Open Project...          Ctrl+O
                - &Recent Projects           >
                - &Save Project             Ctrl+S
                - Save Project &As...       Ctrl+Shift+S
                ---
                - &Import                    >
                    - Import Legacy Actions Ctrl+I
                ---
                - E&xit                     Alt+F4
            - &Edit
                - &Keyboard Shortcuts...
                ---
                - &Preferences
            - &View
                - [x] &Status Bar
            - &Camera
                - (*) &Perspective Projection
                - ( ) &Orthographic Projection
            - &Tools
                - Add &Cylinder Proxy Object
                - Add &Box Proxy Object
            - &Window
                - [ ] Camera EVF
                - [x] Console
                - [x] Properties
                - [x] Timeline
                - [x] Viewport
                - [x] Statistics
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
        # File menu.
        self._file_menu = wx.Menu()
        # Submenus.
        recent_menu = wx.Menu()
        import_menu = wx.Menu()

        _item = wx.MenuItem(None, wx.ID_ANY, 'Import Poses\tCtrl+I','Import poses')
        _item.Bitmap = create_scaled_bitmap('import', 16)
        self.Bind(wx.EVT_MENU, self.on_import_poses, import_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_NEW, '&New Project\tCtrl+N', 'Create new project')
        _item.Bitmap = create_scaled_bitmap('add_project', 16)
        self.Bind(wx.EVT_MENU, self.on_new_project, self._file_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_OPEN, '&Open Project...\tCtrl+O', 'Open existing project')
        _item.Bitmap = create_scaled_bitmap('open_project', 16)
        self.Bind(wx.EVT_MENU, self.on_open_project, self._file_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_JUMP_TO, '&Recent Projects', 'Open one of recent projects', subMenu=recent_menu)
        self._file_menu.Append(_item)
        _item = wx.MenuItem(None, wx.ID_SAVE, '&Save Project\tCtrl+S', 'Save project')
        _item.Bitmap = create_scaled_bitmap('save', 16)
        self.Bind(wx.EVT_MENU, self.on_save, self._file_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_SAVEAS, 'Save Project &as...\tCtrl+Shift+S','Save project as')
        _item.Bitmap = create_scaled_bitmap('save', 16)
        self.Bind(wx.EVT_MENU, self.on_save_as, self._file_menu.Append(_item))
        self._file_menu.Enable(wx.ID_NEW, False)
        self._file_menu.Enable(wx.ID_SAVE, False)
        self._populate_recent_projects()
        self._file_menu.AppendSeparator()
        _item = wx.MenuItem(None, wx.ID_ADD, '&Import', 'Import files',
            subMenu=import_menu)
        self._file_menu.Append(_item)
        self._file_menu.AppendSeparator()
        _item = wx.MenuItem(None, wx.ID_ANY, 'E&xit\tAlt+F4', 'Close the program')
        _item.Bitmap = create_scaled_bitmap('exit_to_app', 16)
        self.Bind(wx.EVT_MENU, self.on_exit, self._file_menu.Append(_item))
        # Edit menu.
        edit_menu = wx.Menu()
        #_item = wx.MenuItem(None, wx.ID_ANY, '&Keyboard Shortcuts...', 'Open keyboard shortcuts')
        #self.Bind(wx.EVT_MENU, None, edit_menu.Append(_item))
        #edit_menu.AppendSeparator()
        _item = wx.MenuItem(None, wx.ID_ANY, '&Cofiguration', 'Open app config')
        _item.Bitmap = create_scaled_bitmap('tune', 16)
        self.Bind(wx.EVT_MENU, self.open_preferences_frame, edit_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, 'Profile', 'Open profile')
        _item.Bitmap = create_scaled_bitmap('tune', 16)
        self.Bind(wx.EVT_MENU, self.open_profile_frame, edit_menu.Append(_item))

        # View menu.
        view_menu = wx.Menu()
        self.statusbar_menuitem = view_menu.Append(wx.ID_ANY, '&Status &Bar', 'Toggle status bar visibility', wx.ITEM_CHECK)
        view_menu.Check(self.statusbar_menuitem.Id, True)
        self.Bind(wx.EVT_MENU, self.update_statusbar, self.statusbar_menuitem)
        # Camera menu.
        camera_menu = wx.Menu()
        _item = wx.MenuItem(None, wx.ID_ANY, '&Perspective Projection', 'Set viewport projection to perspective', wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.panels['viewport'].set_perspective_projection, camera_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, '&Orthographic Projection', 'Set viewport projection to orthographic', wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.panels['viewport'].set_orthographic_projection, camera_menu.Append(_item))
        # Tools menu.
        tools_menu = wx.Menu()
        _item = wx.MenuItem(None, wx.ID_ANY, 'Add &Cylinder Proxy Object', 'Add a cylinder proxy object to the chamber')
        self.Bind(wx.EVT_MENU, self.add_proxy_cylinder, tools_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, 'Add &Box Proxy Object', 'Add a box proxy object to the chamber')
        self.Bind(wx.EVT_MENU, self.add_proxy_aabb, tools_menu.Append(_item))
        # Window menu.
        window_menu = wx.Menu()
        self.menuitems['evf'] = window_menu.Append(wx.ID_ANY, 'Camera Live View','Show/hide camera live view window', wx.ITEM_CHECK)
        self.menuitems['evf'].Enable(False)
        self.Bind(wx.EVT_MENU, self.update_evf_panel, self.menuitems['evf'])
        self.menuitems['console'] = window_menu.Append(wx.ID_ANY, 'Console', 'Show/hide console window', wx.ITEM_CHECK)
        self.menuitems['console'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_console_panel, self.menuitems['console'])
        self.menuitems['imaging_toolbar'] = window_menu.Append(wx.ID_ANY, 'Imaging Toolbar', 'Show/hide imaging toolbar', wx.ITEM_CHECK)
        self.menuitems['imaging_toolbar'].Enable(False)
        self.Bind(wx.EVT_MENU, self.update_imaging_toolbar, self.menuitems['imaging_toolbar'])
        self.menuitems['machine_toolbar'] = window_menu.Append(wx.ID_ANY, 'Machine Toolbar', 'Show/hide machine toolbar', wx.ITEM_CHECK)
        self.menuitems['machine_toolbar'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_machine_toolbar, self.menuitems['machine_toolbar'])
        self.menuitems['pathgen_toolbar'] = window_menu.Append(wx.ID_ANY, 'Path Generator Toolbar', 'Show/hide path generator toolbar', wx.ITEM_CHECK)
        self.menuitems['pathgen_toolbar'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_pathgen_toolbar, self.menuitems['pathgen_toolbar'])
        self.menuitems['properties'] = window_menu.Append(wx.ID_ANY, 'Properties','Show/hide properties window', wx.ITEM_CHECK)
        self.menuitems['properties'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_properties_panel, self.menuitems['properties'])
        self.menuitems['stats'] = window_menu.Append(wx.ID_ANY, 'Statistics', 'Show/hide statistics window', wx.ITEM_CHECK)
        self.menuitems['stats'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_stats_panel, self.menuitems['stats'])
        self.menuitems['timeline'] = window_menu.Append(wx.ID_ANY, 'Timeline', 'Show/hide timeline window', wx.ITEM_CHECK)
        self.menuitems['timeline'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_timeline_panel, self.menuitems['timeline'])
        self.menuitems['viewport'] = window_menu.Append(wx.ID_ANY,'Viewport','Show/hide viewport window', wx.ITEM_CHECK)
        self.menuitems['viewport'].Check(True)
        self.Bind(wx.EVT_MENU, self.update_viewport_panel, self.menuitems['viewport'])
        #window_menu.AppendSeparator()
        #_item = wx.MenuItem(None, wx.ID_ANY, 'Window &Preferences...', 'Open window preferences')
        #_item.Bitmap = create_scaled_bitmap('tune', 16)
        #self.Bind(wx.EVT_MENU, None, window_menu.Append(_item))
        # Help menu.
        help_menu = wx.Menu()
        #_item = wx.MenuItem(None, wx.ID_ANY, 'COPIS &Help...\tF1', 'Open COPIS help menu')
        #_item.Bitmap = create_scaled_bitmap('help_outline', 16)
        #self.Bind(wx.EVT_MENU, None, help_menu.Append(_item))
        #help_menu.AppendSeparator()
        _item = wx.MenuItem(None, wx.ID_ANY, '&Visit COPIS website\tCtrl+F1', f'Open {self._COPIS_WEBSITE}')
        _item.Bitmap = create_scaled_bitmap('open_in_new', 16)
        self.Bind(wx.EVT_MENU, self.open_copis_website, help_menu.Append(_item))
        _item = wx.MenuItem(None, wx.ID_ANY, '&About COPIS...', 'Show about dialog')
        _item.Bitmap = create_scaled_bitmap('info', 16)
        self.Bind(wx.EVT_MENU, self.open_about_dialog, help_menu.Append(_item))
        self._menubar.Append(self._file_menu, '&File')
        self._menubar.Append(edit_menu, '&Edit')
        self._menubar.Append(view_menu, '&View')
        self._menubar.Append(camera_menu, '&Camera')
        self._menubar.Append(tools_menu, '&Tools')
        self._menubar.Append(window_menu, '&Window')
        self._menubar.Append(help_menu, '&Help')
        self.SetMenuBar(self._menubar)

    def on_new_project(self, _) -> None:
        """Starts a new project with defaults."""
        proceed = self._prompt_saving('New Project', _)
        if proceed:
            self.core.start_new_project()
                
    def on_import_poses(self, _) -> None:
        wildcard = f'{self._FILES_PROJECT}|{self._FILES_WILDCARD}'
        with wx.FileDialog(self, 'Import Project File', wildcard=wildcard, defaultDir=self._get_default_dir(), style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            msg = self.core.append_project(file_dialog.Path)
            if msg:
                show_msg_dialog(f'{msg}.', 'Import Poses')

    def on_project_selected(self, event: wx.CommandEvent):
        """Opens the selected recent project."""
        caption = 'Open Recent Project'
        item_text = event.EventObject.GetLabelText(event.Id)
        path = item_text.split(':', 1)[1].strip()
        if not store.path_exists(path):
            show_msg_dialog('The selected project no longer exists.', caption)
            self.core.config.remove_recent_project(path)
            self._populate_recent_projects()
            return

        if not self._prompt_saving(caption, event):
            return

        msg = self.core.open_project(path)

        if msg:
            show_msg_dialog(f'{msg}.', caption)

    def on_open_project(self, _) -> None:
        """Opens 'open' dialog for existing COPIS projects."""
        if not self._prompt_saving('Open Project', _):
            return
        wildcard = f'{self._FILES_PROJECT}|{self._FILES_WILDCARD}'
        with wx.FileDialog(self, 'Open Project File', wildcard=wildcard, defaultDir=self._get_default_dir(), style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            msg = self.core.open_project(file_dialog.Path)
            if msg:
                show_msg_dialog(f'{msg}.', 'Open Project')
            self._populate_recent_projects()

    def on_save(self, _) -> None:
        """Opens 'save' dialog."""
        project_path = self.core.project.path
        has_project_path = project_path and len(project_path.strip()) > 0
        if has_project_path:
            try:
                self.core.save_project(project_path)
                self._populate_recent_projects()
            except Exception as err:
                wx.LogError('Could not save the project.')
                print_error_msg(self.core.console,
                f'An exception occurred while saving the project: {err.args[0]}')
        else:
            self.on_save_as(_)

    def on_save_as(self, _) -> None:
        """Opens 'save as' dialog."""
        if not self.core.project.is_dirty:
            if show_prompt_dialog(
                'The project was not modified. Would you still like to save it?',
                    'Save Project') == wx.ID_NO:
                return

        with wx.FileDialog(self, 'Save Project As', wildcard=self._FILES_PROJECT, defaultDir=self._get_default_dir(), style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            path = file_dialog.Path
            try:
                self.core.save_project(path)
                self._populate_recent_projects()
            except Exception as err:
                store.delete_path(path)
                wx.LogError(f'Could not save the project as "{path}".')
                print_error_msg(self.core.console,
                f'An exception occurred while saving the project: {err.args[0]}')

    def show_imaging_toolbar(self, position, actions):
        """Shows the imaging toolbar at the given position and executes the given callback
            for the given tool."""
        self.SetStatusText('Active Session No.: ' + str(self.core._session_id))
        pane: aui.AuiPaneInfo = self._mgr.GetPane(self.imaging_toolbar)  
        pane.FloatingPosition(position)
        pane.Show(True)
        self.menuitems['imaging_toolbar'].Enable(True)
        self.menuitems['imaging_toolbar'].Check(True)
        self._mgr.Update()
        pane.window.set_actions(actions)

    def hide_imaging_toolbar(self):
        """Hides the imaging toolbar."""
        self.SetStatusText('Ready')
        pane: aui.AuiPaneInfo = self._mgr.GetPane(self.imaging_toolbar)
        pane.Show(False)

        self.menuitems['imaging_toolbar'].Enable(False)
        self.menuitems['imaging_toolbar'].Check(False)

        # Call the specified function after the current and pending event handlers have been completed.
        # This is good for making GUI method calls from non-GUI threads, in order to prevent hangs.
        wx.CallAfter(self._mgr.Update)

    def update_statusbar(self, event: wx.CommandEvent) -> None:
        """Updates status bar visibility based on menu item."""
        self.StatusBar.Show(event.IsChecked())
        self._mgr.Update()

    def add_proxy_cylinder(self, _) -> None:
        """Opens dialog to generate cylinder proxy object."""
        with ProxygenCylinder(self) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                start = vec3(dlg.start_x_ctrl.num_value, dlg.start_y_ctrl.num_value, dlg.start_z_ctrl.num_value)
                end = vec3(dlg.end_x_ctrl.num_value, dlg.end_y_ctrl.num_value, dlg.end_z_ctrl.num_value)
                radius = dlg.radius_ctrl.num_value
                # TODO: fill name and type fields from
                # defaults for now
                name = dlg.proxy_name_ctrl.GetValue()
                type = "Cylinder"
                id = len(self.core.project.proxies)
                description = dlg.proxy_description_ctrl.GetValue()
                self.core.project.proxies.append(CylinderObject3D(start, end, radius, name, type, description, id = id))

    def add_proxy_aabb(self, _) -> None:
        """Opens dialog to generate box proxy object."""
        with ProxygenAABB(self) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                lower = vec3(dlg.lower_x_ctrl.num_value, dlg.lower_y_ctrl.num_value, dlg.lower_z_ctrl.num_value)
                upper = vec3(dlg.upper_x_ctrl.num_value, dlg.upper_y_ctrl.num_value, dlg.upper_z_ctrl.num_value)
                # TODO: fill name and type fields from
                # defaults for now
                type = "Box"        
                id = len(self.core.project.proxies)
                name = dlg.proxy_name_ctrl.GetValue()
                description = dlg.proxy_description_ctrl.GetValue()
                self.core.project.proxies.append(AABoxObject3D(lower, upper, name, type, description, id = id))

    def open_preferences_frame(self, _) -> None:
        """Opens the preferences frame."""
        cfg_dlg =  config_dialog.dlg_config(self)        
        cfg_dlg.ShowModal()
        cfg_dlg.Destroy()
        #preferences_dialog = PreferenceFrame(self)
        #preferences_dialog.Show()

    def open_profile_frame(self, _) -> None:
        """Opens the preferences frame."""
        pfl_dlg =  profile_dialog.dlg_profile(self)        
        pfl_dlg.ShowModal()
        pfl_dlg.Destroy()

    def open_copis_website(self, _) -> None:
        """Launches the COPIS project's website."""
        wx.LaunchDefaultBrowser(self._COPIS_WEBSITE)

    def open_about_dialog(self, _) -> None:
        """Opens the 'about' dialog."""
        about = AboutDialog(self)
        about.Show()

    def on_exit(self, _) -> None:
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
        # Create AUI manager and set flags.
        self._mgr = aui.AuiManager(self, agwFlags=
            aui.AUI_MGR_ALLOW_FLOATING |
            aui.AUI_MGR_TRANSPARENT_DRAG |
            aui.AUI_MGR_TRANSPARENT_HINT |
            aui.AUI_MGR_HINT_FADE |
            aui.AUI_MGR_LIVE_RESIZE |
            aui.AUI_MGR_AUTONB_NO_CAPTION)
        # Set auto notebook style.
        self._mgr.SetAutoNotebookStyle(
            aui.AUI_NB_TOP |
            aui.AUI_NB_TAB_SPLIT |
            aui.AUI_NB_TAB_MOVE |
            aui.AUI_NB_SCROLL_BUTTONS |
            aui.AUI_NB_WINDOWLIST_BUTTON |
            aui.AUI_NB_MIDDLE_CLICK_CLOSE |
            aui.AUI_NB_CLOSE_ON_ACTIVE_TAB |
            aui.AUI_NB_TAB_FLOAT)
        # Set AUI colors and style.
        # See https://wxpython.org/Phoenix/docs/html/wx.lib.agw.aui.dockart.AuiDefaultDockArt.html
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
        # Initialize relevant panels.
        self.panels['viewport'] = ViewportPanel(self)
        self.panels['console'] = ConsolePanel(self)
        self.panels['timeline'] = TimelinePanel(self)
        self.panels['properties'] = PropertiesPanel(self)
        self.panels['stats'] = StatsPanel(self)
        self.panels['machine_toolbar'] = MachineToolbar(self)
        self.panels['pathgen_toolbar'] = PathgenToolbar(self)
        self.panels['imaging_toolbar'] = ImagingToolbar(self)
        # Add viewport panel.
        self._mgr.AddPane(
            self.panels['viewport'],
            aui.AuiPaneInfo().Name('viewport').Caption('Viewport').
            Dock().Center().MaximizeButton().MinimizeButton().DefaultPane().MinSize(350, 250))
        # Add console, timeline panel.
        self._mgr.AddPane(
            self.panels['console'],
            aui.AuiPaneInfo().Name('console').Caption('Console').
            Dock().Bottom().Position(0).Layer(0).MinSize(self._BOTTOM_PANE_MIN_SIZE).Show(True))
        self._mgr.AddPane(
            self.panels['timeline'],
            aui.AuiPaneInfo().Name('timeline').Caption('Timeline').
            Dock().Bottom().Position(1).Layer(0).MinSize(self._BOTTOM_PANE_MIN_SIZE).Show(True),
            target=self._mgr.GetPane('console'))
        # Add properties and stats panels.
        self._mgr.AddPane(
            self.panels['properties'],
            aui.AuiPaneInfo().Name('properties').Caption('Properties').
            Dock().Right().Position(0).Layer(1).MinSize(self._RIGHT_PANE_MIN_SIZE).Show(True))
        self._mgr.AddPane(
            self.panels['stats'],
            aui.AuiPaneInfo().Name('stats').Caption('Statistics').
            Dock().Bottom().Right().Position(2).Layer(1).MinSize(self._RIGHT_PANE_MIN_SIZE)
            .Show(True))
        # Set first tab of all auto notebooks as the one selected.
        for notebook in self._mgr.GetNotebooks():
            notebook.SetSelection(0)
        # Add toolbar panels.
        self.panels['machine_toolbar'].Realize()
        self._mgr.AddPane(
            self.panels['machine_toolbar'],
            aui.AuiPaneInfo().Name('machine_toolbar').Caption('Machine Toolbar').
            ToolbarPane().BottomDockable(False).Top().Layer(10))
        self.panels['pathgen_toolbar'].Realize()
        self._mgr.AddPane(
            self.panels['pathgen_toolbar'],
            aui.AuiPaneInfo().Name('pathgen_toolbar').Caption('Pathgen Toolbar').
            ToolbarPane().BottomDockable(False).Top().Layer(10))
        self.panels['imaging_toolbar'].Realize()
        self._mgr.AddPane(
            self.panels['imaging_toolbar'],
            aui.AuiPaneInfo().Name('imaging_toolbar').Caption('Imaging Toolbar').
            Float().ToolbarPane().BottomDockable(False).Top().Layer(10).Hide())
        self._mgr.Update()
        self.update_right_dock()

    def update_right_dock(self) -> None:
        """Redraws the right dock pane to fit updated children's contents."""
        panels = [self.properties_panel, self.stats_panel]
        total_height = sum([p.GetVirtualSize()[1] for p in panels])
        stats_height = self.stats_panel.Sizer.ComputeFittingClientSize(self.stats_panel)[1]
        min_size = (self._RIGHT_PANE_MIN_SIZE.width, stats_height)
        stats_proportion = 100 * stats_height / total_height
        other_proportion = (100 - stats_proportion) / (len(panels) / 2)
        stats_proportion = round(stats_proportion, 1)
        other_proportion = round(other_proportion, 1)
        self._mgr.GetPane(self.properties_panel).MinSize(min_size)
        self._mgr.GetPane(self.stats_panel).MinSize(min_size)
        self._mgr.GetPane(self.properties_panel).dock_proportion = other_proportion
        self._mgr.GetPane(self.stats_panel).dock_proportion = stats_proportion
        self._mgr.Update()

    def add_evf_pane(self) -> None:
        """Initialize camera liveview panel."""
        if 'evf' not in self.panels:
            # Live view jpg comes out at (960, 640) on Canon EOS 80D.
            evf_size = (vec2(960, 640) * .75).to_tuple()
            self.panels['evf'] = EvfPanel(self, size=evf_size)
            self._mgr.AddPane(self.panels['evf'],
                aui.AuiPaneInfo().Name('evf').Caption('Live View').
                Float().Right().Position(1).Layer(0).MinSize(evf_size).
                MinimizeButton(True).DestroyOnClose(True).MaximizeButton(True))
            self._mgr.Update()
            self.menuitems['evf'].Enable(True)
            self._mgr.ShowPane(self.evf_panel, True)
        elif not self.evf_panel.IsShownOnScreen():
            self._mgr.ShowPane(self.evf_panel, True)
        self.menuitems['evf'].Check(True)

    def remove_evf_pane(self) -> None:
        """Removes camera liveview panel."""
        if 'evf' in self.panels:
            evf_pane = self._mgr.GetPane(self.evf_panel)
            self._mgr.ShowPane(self.evf_panel, False)
            self.menuitems[evf_pane.name].Check(False)
            evf_pane.window.on_close()
            self._mgr.DetachPane(evf_pane.window)
            self._mgr.Update()
            evf_pane.window.Destroy()
            self.panels.pop('evf')
            self.menuitems['evf'].Enable(False)

    def update_pathgen_toolbar(self, event: wx.CommandEvent) -> None:
        """Show or hide path generator toolbar."""
        self._mgr.ShowPane(self.pathgen_toolbar, event.IsChecked())

    def update_machine_toolbar(self, event: wx.CommandEvent) -> None:
        """Show or hide machine toolbar."""
        self._mgr.ShowPane(self.machine_toolbar, event.IsChecked())

    def update_imaging_toolbar(self, event: wx.CommandEvent) -> None:
        """Show or hide imaging toolbar."""
        self._mgr.ShowPane(self.imaging_toolbar, event.IsChecked())

    def update_console_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide console panel."""
        self._mgr.ShowPane(self.console_panel, event.IsChecked())

    def update_evf_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide evf panel."""
        self._mgr.ShowPane(self.evf_panel, event.IsChecked())

    def update_properties_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide properties panel."""
        self._mgr.ShowPane(self.properties_panel, event.IsChecked())

    def update_timeline_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide timeline panel."""
        self._mgr.ShowPane(self.timeline_panel, event.IsChecked())

    def update_viewport_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide viewport panel."""
        self._mgr.ShowPane(self.viewport_panel, event.IsChecked())

    def update_stats_panel(self, event: wx.CommandEvent) -> None:
        """Show or hide stats panel."""
        self._mgr.ShowPane(self.stats_panel, event.IsChecked())

    def on_pane_close(self, event: aui.framemanager.AuiManagerEvent) -> None:
        """Update menu items in the Window menu when a pane has been closed."""
        pane = event.GetPane()
        # if closed pane is a notebook, process and hide all pages in the notebook.
        if pane.IsNotebookControl():
            notebook = pane.window
            for i in range(notebook.GetPageCount()):
                nb_pane = self._mgr.GetPane(notebook.GetPage(i))
                self._mgr.ShowPane(self.panels[nb_pane.name], False)
                self.menuitems[nb_pane.name].Check(False)
        else:
            self._mgr.ShowPane(self.panels[pane.name], False)
            self.menuitems[pane.name].Check(False)
        if pane.name == 'evf':
            pane.window.on_close()
            self._mgr.DetachPane(pane.window)
            self._mgr.Update()
            pane.window.Destroy()
            self.panels.pop('evf')
            self.menuitems['evf'].Enable(False)

    def on_close(self, event: wx.CloseEvent) -> None:
        """On EVT_CLOSE, exit application."""
        event.StopPropagation()
        if not self._prompt_saving('Close', event):
            return
        pos = self.GetPosition()
        size = self.GetSize()
        self.core.config.update_window_state(WindowState(pos.x, pos.y, size.x, size.y, self.IsMaximized()))
        self._mgr.UnInit()
        self.Destroy()

    def __del__(self) -> None:
        pass

    def update_properties_panel_title(self, title: str) -> None:
        """Updates the properties panel's title."""
        
        if title:
            title = title.title()
            self._mgr.GetPane(self.properties_panel).Caption(title)
            self._mgr.Update()
