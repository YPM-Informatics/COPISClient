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

"""Provide the COPIS Configuration class"""

import os
import errno
import shutil
import platformdirs
from configparser import ConfigParser
from glm import vec3
from copis.classes.sys_db import SysDB


#from .core import COPISCore
import copis.store as store
from .globals import DebugEnv, Size, WindowState
from .classes import ApplicationSettings, MachineSettings
import wx

from copis.gui import config_dialog

def _get_bool(val):
    return val.lower() in ['yes', 'on', 'true', '1']


def _get_state_parts(state_str):
    parts = state_str.split(',')
    return list(int(s)
        if i < len(parts) - 1 else _get_bool(s)
            for i, s in enumerate(parts))


class Config():
    """Handle application configuration."""

    _MAX_RECENT_PROJECTS_COUNT = 5

    def __init__(self, filepath:str = None) -> None:
        self._application_settings = None
        self._machine_settings = None
        self._log_serial_tx : bool = False
        self._log_serial_rx : bool = False
        self._homing_method : str = ''
        self._adjust_live_pan : bool = False
        self._db_path : str = None
        self._profile_path : str = None
        self._default_proxy_path : str = 'proxies\\handsome_dan.obj'
        self._root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self._ini_path : str = filepath
        self._ini_path_type : str = None
        self._plaform_data_path : str = platformdirs.site_data_path('copis','copis') #ideally where we want it to be
        self._plaform_user_path : str = platformdirs.user_data_dir('copis','copis')
        
        if self._ini_path is None:
            self._ini_path = os.path.join(self._root_path, 'copis.ini') #local path
            if os.path.exists(self._ini_path):
                self._ini_path_type = 'local' 
            else:
                self._ini_path_type = "platform"
                if not os.path.exists(self._plaform_data_path):
                    os.makedirs(self._plaform_data_path)
                if not os.path.exists(self._plaform_user_path):
                    os.makedirs(self._plaform_user_path)
                self._ini_path = os.path.join(self._plaform_data_path, 'copis.ini') 
                if not os.path.exists(self._ini_path):  #if it doesn't exist we check 3 older version of the user path where it was originally placed and move the init into the correct location. We do not move other files stored their, leaving that up to the user by editing the config file.  Unlikley any clients are using these older directories for the ini file, but we check them anyway.
                    legacy_data_dir_0 = self._plaform_user_path
                    legacy_data_dir_1 = os.path.split(platformdirs.user_data_dir('copis', roaming=True))[0] 
                    legacy_data_dir_2 = os.path.split(platformdirs.user_data_dir('copis'))[0]
                    test_ini_path_0 = os.path.join(legacy_data_dir_0, 'copis.ini')
                    test_ini_path_1 = os.path.join(legacy_data_dir_1, 'copis.ini')
                    test_ini_path_2 = os.path.join(legacy_data_dir_2, 'copis.ini')
                    if os.path.exists(test_ini_path_0):
                        shutil.move(test_ini_path_0, self._ini_path)
                    elif os.path.exists(test_ini_path_1):
                        shutil.move(test_ini_path_1, self._ini_path)
                    elif os.path.exists(test_ini_path_2):
                        shutil.move(test_ini_path_2, self._ini_path)
                    else: #none of the legacy files found, no root ini found and no plaform dir file found. Therfore new install and we copy sample ini over along with matching profile.
                        #set defaults for app setting and machine setting, cofigure paths, copy sample profile and save copis.ini 
                        self._application_settings =  ApplicationSettings(DebugEnv('prod'), Size(width=800,height=600), self._ensure_window_state_exists(min_width=800,min_height=600))
                        self._machine_settings = MachineSettings(vec3(350.0, 400.0, 0.0),vec3(700.0, 800.0, 450.0))
                        self.db_path = os.path.join(self._plaform_data_path, 'copis.db') 
                        self.profile_path = os.path.join(self._plaform_data_path, 'default_profile.json') 
                        sample_profile_path = os.path.join(self._root_path,'ex','ex_profile.json')
                        shutil.copyfile(sample_profile_path, self.profile_path)
                        self.save_to_file(self._ini_path)
        else:
            self._ini_path_type = 'custom' 
            
        self.load_from_file(filepath)
   
    @property
    def root_path(self) -> str:
        """Returns the path to the application root."""
        return self._root_path
    
    @property
    def ini_path(self) -> str:
        """Returns the path to the application root."""
        return self._ini_path
    
    @property
    def profile_path(self) -> str:
        """Returns the path to the system database."""
        return self._profile_path
    
    @profile_path.setter
    def profile_path(self, value):
        self._profile_path = value     
        
    @property
    def default_proxy_path(self) -> str:
        """Returns the path to the system database."""
        return self._default_proxy_path
    
    @default_proxy_path.setter
    def default_proxy_path(self, value):
        self._default_proxy_path = value 

    @property
    def adjust_live_pan(self) -> bool:
        return self._adjust_live_pan
    
    @property
    def homing_method(self) -> bool:
        """Returns a homing method if a special one has been configured"""
        return self._homing_method
    
    @property
    def db_path(self) -> str:
        """Returns the path to the system database."""
        return self._db_path
    
    @db_path.setter
    def db_path(self, value):
        self._db_path = value 

    @property
    def log_serial_tx(self) -> bool:
        """Returns a flag indicating whether to log serial Tx, if a database is configured."""
        return self._log_serial_tx

    @property
    def log_serial_rx(self) -> bool:
        """Returns a flag indicating whether to log serial Rx, if a database is configured."""
        return self._log_serial_rx

    @property
    def application_settings(self) -> ApplicationSettings:
        """Application configuration settings getter."""
        return self._application_settings

    @property
    def machine_settings(self) -> MachineSettings:
        """Machine configuration settings getter."""
        return self._machine_settings

    def _ensure_window_state_exists(self, x:int=None, y:int=None, width:int=None, height:int=None, is_maximized:bool=False, min_width:int=800, min_height:int=600) -> WindowState:
        """This method ensures that the window's state is correctly initialized, properly fits within the display area, 
        and saves this state to a configuration file for future use. 
        It prevents the window from being positioned outside the visible screen or being too small, maintaining a user-friendly interface."""
        displays = (wx.Display(i) for i in range(wx.Display.GetCount()))
        main_d = next(filter(lambda d: d.IsPrimary, displays))
        display_rect = main_d.GetGeometry()
        if not x and not width:
            width =  display_rect[2] * 60 / 100
        elif not width:
            width = min_width 
        if not y and not height:
            height =  display_rect[3] * 60 / 100
        elif not height:
            height = min_height    
        if not is_maximized:
            if x is not None and y is not None:
                if x < 0:
                    width = max(min_width, width + x)
                    x = 0
                if y < 0:
                    height = max(min_height, height + y)
                    y = 0
                if x > display_rect.X + display_rect.Width:
                    offset = x - display_rect.X
                    width = max(min_width, width - offset)
                    x = x - offset
                if y  > display_rect.Y + display_rect.Height:
                    offset = y - display_rect.Y
                    height = max(min_height, height - offset)
                    y = y - offset
                if x + width > display_rect.X + display_rect.Width:
                    offset = x + width - display_rect.X - display_rect.Width
                    width = max(min_width, width - offset)
                if y + height > display_rect.Y+ display_rect.Height:
                    offset = y + height - display_rect.Y - display_rect.Height
                    height = max(min_height, height - offset)
            else:
                x = int((display_rect.X - width) / 2)
                y = int((display_rect.Y - height) / 2)
        return WindowState(int(x),int(y),int(width),int(height),is_maximized)

    def update_window_state(self, state: WindowState) -> None:
        """Updates the window geometry application setting."""
        self._application_settings.window_state = state
        self.save_to_file()


    def update_recent_projects(self, path: str) -> None:
        """Updates the recent projects and last output path application settings."""
        self._application_settings.last_output_path = store.get_directory(path)
        self._application_settings.recent_projects.insert(0, path)
        if len(self._application_settings.recent_projects) > self._MAX_RECENT_PROJECTS_COUNT:
            self._application_settings.recent_projects = self._application_settings.recent_projects[
                :self._MAX_RECENT_PROJECTS_COUNT]
        self.save_to_file()


    def remove_recent_project(self, path: str) -> None:
        """Removes a recent projects entry."""
        recent_projects = list(map(str.lower, self._application_settings.recent_projects))
        index = recent_projects.index(path.strip().lower())
        if index >= 0:
            self._application_settings.recent_projects.pop(index)
            self.save_to_file()

    def load_from_file(self, config_filepath : str = None):
        """Creates a configuration object from an existing ini file. Only revelvant values are stored. 
        If no file is provided, the store will be used to determine the file to read"""
        if config_filepath is None:
            config_filepath = self._ini_path
        if not os.path.exists(config_filepath):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_filepath)
        
        parser = ConfigParser()
        parser.read(config_filepath)
        app = parser['App']
        if 'window_min_size' in app:
            w_min_size = [int(value) for value in app['window_min_size'].split(',')]
        else:
            w_min_size = [800,600]
            
        if 'window_state' in app:
            w_state = app['window_state'].split(',')
            x, y, w, h = [int(value) for value in w_state[:-1]]
            m = _get_bool(w_state[-1])
        else:
            x, y, w, h, m = None,None,None,None,False
        window_min_size = Size(width=w_min_size[0],height=w_min_size[1])
        window_state = self._ensure_window_state_exists(x=x,y=y,width=w,height=h,is_maximized=m, min_width=w_min_size[0],min_height=w_min_size[1])
        
        debug_env = app['debug_env']
        if not any(e.value == debug_env for e in DebugEnv):
            debug_env = 'prod'
        self._application_settings = ApplicationSettings(DebugEnv(debug_env), window_min_size, window_state)
        key = 'last_output_path'
        if key in app:
            last_output_path = app[key]
            if last_output_path:
                self._application_settings.last_output_path = last_output_path
        key = 'recent_projects'
        if key in app:
            recent_projects = app[key]
            if recent_projects:
                self._application_settings.recent_projects = [
                    l.strip('\t') for l in recent_projects.splitlines()]
        
        machine = parser['Machine']
        size_x = machine.getfloat('size_x')
        size_y = machine.getfloat('size_y')
        size_z = machine.getfloat('size_z')
        origin_x = machine.getfloat('origin_x')
        origin_y = machine.getfloat('origin_y')
        origin_z = machine.getfloat('origin_z')
        origin = vec3(origin_x, origin_y, origin_z)
        dimensions = vec3(size_x, size_y, size_z)
        self._machine_settings = MachineSettings(origin, dimensions)

        self._log_serial_tx : bool = False
        self._log_serial_rx : bool = False
        self._homing_method : str = ''
        self._adjust_live_pan : bool = False
        self._db_path: str = None
        
        if parser.has_option('System', 'db'):
            self._db_path = parser['System']['db']
            db_dir = os.path.dirname(self._db_path)
            if db_dir and not db_dir.isspace() and not os.path.exists(db_dir): 
                os.makedirs(db_dir)
            #we should throw an error if after this db path does not exist
            
        if self._db_path and parser.has_option('System', 'log_serial_tx'):
            self._log_serial_tx = _get_bool(parser['System']['log_serial_tx'])
        if self._db_path and parser.has_option('System', 'log_serial_rx'):
            self._log_serial_rx = _get_bool(parser['System']['log_serial_rx'])
        if parser.has_option('System', 'homing_method'):
                self._homing_method = parser['System']['homing_method']
        if parser.has_option('System', 'live_cam_pan_op'):
            self._adjust_live_pan = _get_bool(parser['System']['live_cam_pan_op'])
        
        if parser.has_option('Project', 'profile_path'):
            self._profile_path = parser['Project']['profile_path']
        if parser.has_option('Project', 'default_proxy_path'):
            self._default_proxy_path = parser['Project']['default_proxy_path']

    def save_to_file(self, config_filepath : str = None):
        """Save a configuration object to an ini file. 
        If the file alreade exists, it will update whith file with values from the config
        If no file is provided, the store will be used to determine the file to output"""
        
        if config_filepath is None:
            config_filepath = self.ini_path
            
        stringify = lambda val: ','.join([str(d) for d in val])
        stringify_list = lambda val: '\n\t'.join([str(d) for d in val])
        config_dict = {}
        config_dict['Machine'] ={
                'size_x': self._machine_settings.dimensions.x,
                'size_y': self._machine_settings.dimensions.y,
                'size_z': self._machine_settings.dimensions.z,
                'origin_x': self._machine_settings.origin.x,
                'origin_y': self._machine_settings.origin.y,
                'origin_z': self._machine_settings.origin.z
        }
        config_dict['App'] = {'window_min_size': stringify(self._application_settings.window_min_size),
                'debug_env': self._application_settings.debug_env.value,
                'window_state': stringify(self._application_settings.window_state)
        }   
        if self._application_settings.last_output_path:
            config_dict['App']['last_output_path'] = self._application_settings.last_output_path
        if self._application_settings.recent_projects:
            config_dict['App']['recent_projects'] = stringify_list(self._application_settings.recent_projects)
        
        config_dict['System'] = {
            'db': self._db_path,
            'log_serial_tx' : self._log_serial_tx,
            'log_serial_rx' : self._log_serial_rx,
            'live_cam_pan_op' : self._adjust_live_pan
            
        }
        config_dict['Project'] = {
            'profile_path': self._profile_path,
            'default_proxy_path' : self._default_proxy_path
        }
        
        parser = ConfigParser()
        parser.read_dict(config_dict)
        
        if os.path.exists(config_filepath):
            prior_parser = ConfigParser()
            prior_parser.read(config_filepath)
            for section in parser.sections():
                if not prior_parser.has_section(section):
                    prior_parser.add_section(section)
                for key, value in parser.items(section):
                    prior_parser.set(section, key, value)
            parser = prior_parser
            
        with open(config_filepath, 'w', encoding='utf-8') as file:
            parser.write(file)
        

        
