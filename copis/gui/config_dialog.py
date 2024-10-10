# -*- coding: utf-8 -*-

###########################################################################
## Parts of this file generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
## http://www.wxformbuilder.org/
## FORM BUILDER IMPORTS
###########################################################################

import wx
import wx.xrc
import gettext
_ = gettext.gettext

###########################################################################

import uuid
import copis.store as store
import os
from copis.classes.sys_db import SysDB
from copis.gl.glcanvas import GLCanvas3D
from copis.gui import profile_dialog

class dlg_config ( wx.Dialog ):

    def __init__( self, parent ):
        
        self._load_wx_form(parent)
        self._load_config()
        
   
    def _load_wx_form(self, parent):
        ###########################################################################
        ## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
        ## http://www.wxformbuilder.org/
        ##
        ## PLEASE DO *NOT* EDIT THIS!
        ###########################################################################

        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"Configuration File Editor"), pos = wx.DefaultPosition, size = wx.Size( 434,447 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        self.SetToolTip( _(u"Local application folder stores config info with the application, making it easy distribute and run the same application from multiple machines or from a network location.  System App folder uses the OS defined folder for application data. This is recommended for most installations.") )

        bSizer1 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, _(u"Select options below to configure the COPIS client application.  See documentation for more information about these settings. "), wx.DefaultPosition, wx.Size( -1,30 ), 0 )
        self.m_staticText1.Wrap( -1 )

        bSizer1.Add( self.m_staticText1, 0, wx.ALL, 5 )

        m_radio_ini_locationChoices = [ _(u"System's App Data Folder"), _(u"Local Application Folder") ]
        self.m_radio_ini_location = wx.RadioBox( self, wx.ID_ANY, _(u"Cofiguration File Location"), wx.DefaultPosition, wx.DefaultSize, m_radio_ini_locationChoices, 1, wx.RA_SPECIFY_COLS )
        self.m_radio_ini_location.SetSelection( 1 )
        self.m_radio_ini_location.Enable( False )
        self.m_radio_ini_location.Hide()

        bSizer1.Add( self.m_radio_ini_location, 0, wx.ALL, 5 )

        fgSizer1 = wx.FlexGridSizer( 4, 4, 0, 0 )
        fgSizer1.SetFlexibleDirection( wx.BOTH )
        fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )


        fgSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, _(u"X [Width]"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText4.Wrap( -1 )

        fgSizer1.Add( self.m_staticText4, 0, wx.ALL, 5 )

        self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, _(u"Y [Depth]"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText7.Wrap( -1 )

        fgSizer1.Add( self.m_staticText7, 0, wx.ALL, 5 )

        self.m_staticText8 = wx.StaticText( self, wx.ID_ANY, _(u"Z [Height]"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText8.Wrap( -1 )

        fgSizer1.Add( self.m_staticText8, 0, wx.ALL, 5 )

        self.m_staticText9 = wx.StaticText( self, wx.ID_ANY, _(u"Chamber Dimensions"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText9.Wrap( -1 )

        self.m_staticText9.SetToolTip( _(u"Working envelope displayed in the 3D user interface.") )

        fgSizer1.Add( self.m_staticText9, 0, wx.ALL, 5 )

        self.m_text_x_dim = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 50,-1 ), 0 )
        fgSizer1.Add( self.m_text_x_dim, 0, wx.ALL, 5 )

        self.m_text_y_dim = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 50,-1 ), 0 )
        fgSizer1.Add( self.m_text_y_dim, 0, wx.ALL, 5 )

        self.m_text_z_dim = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 50,-1 ), 0 )
        fgSizer1.Add( self.m_text_z_dim, 0, wx.ALL, 5 )

        self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, _(u"Origin [0,0,0]"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText5.Wrap( -1 )

        self.m_staticText5.SetToolTip( _(u"Define where 0,0,0 should be displayed in UI relative to chamber dimensions.") )

        fgSizer1.Add( self.m_staticText5, 0, wx.ALL, 5 )

        self.m_text_x_origin = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 50,-1 ), 0 )
        self.m_text_x_origin.SetToolTip( _(u"Typically, 1/2 of the width") )

        fgSizer1.Add( self.m_text_x_origin, 0, wx.ALL, 5 )

        self.m_text_y_origin = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 50,-1 ), 0 )
        self.m_text_y_origin.SetToolTip( _(u"Typically, 1/2 of the depth") )

        fgSizer1.Add( self.m_text_y_origin, 0, wx.ALL, 5 )

        self.m_text_z_origin = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 50,-1 ), 0 )
        self.m_text_z_origin.SetToolTip( _(u"Typically, 0 for single chamber, half the Z height for a double chamber.") )

        fgSizer1.Add( self.m_text_z_origin, 0, wx.ALL, 5 )


        bSizer1.Add( fgSizer1, 1, wx.EXPAND, 5 )

        self.m_chk_live_cam_pan_op = wx.CheckBox( self, wx.ID_ANY, _(u"Enable active pan optimization"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1.Add( self.m_chk_live_cam_pan_op, 0, wx.ALL, 5 )

        self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, _(u"Select Log Database File Location:"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText2.Wrap( -1 )

        bSizer1.Add( self.m_staticText2, 0, wx.ALL, 5 )

        self.m_file_db = wx.FilePickerCtrl( self, wx.ID_ANY, u"db\\copis.db", _(u"Select a file"), _(u"*.*"), wx.DefaultPosition, wx.Size( 300,-1 ), wx.FLP_USE_TEXTCTRL )
        bSizer1.Add( self.m_file_db, 0, wx.ALL, 5 )

        self.m_chk_db_log_tx = wx.CheckBox( self, wx.ID_ANY, _(u"Log Serial Transmit"), wx.Point( -1,-1 ), wx.DefaultSize, 0 )
        bSizer1.Add( self.m_chk_db_log_tx, 0, wx.ALL, 5 )

        self.m_chk_db_log_rx = wx.CheckBox( self, wx.ID_ANY, _(u"Log Serial Receive"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1.Add( self.m_chk_db_log_rx, 0, wx.ALL, 5 )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer1.Add( bSizer4, 1, wx.ALL, 5 )

        self.m_staticText21 = wx.StaticText( self, wx.ID_ANY, _(u"Select Machine Profile: [File must exist, please create one or use a default. Edit this file to match your configuration before connecting to machine]:"), wx.DefaultPosition, wx.Size( -1,30 ), 0 )
        self.m_staticText21.Wrap( -1 )

        bSizer1.Add( self.m_staticText21, 0, wx.ALL, 5 )

        bSizer3 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_file_profile = wx.FilePickerCtrl( self, wx.ID_ANY, u"profiles\\default_profile.json", _(u"Select a file"), _(u"*.*"), wx.DefaultPosition, wx.Size( 300,-1 ), wx.FLP_SAVE|wx.FLP_USE_TEXTCTRL )
        bSizer3.Add( self.m_file_profile, 0, wx.ALL, 5 )

        self.m_btn_new_profile = wx.Button( self, wx.ID_ANY, _(u"New Profile..."), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_btn_new_profile.Enable( False )
        self.m_btn_new_profile.Hide()

        bSizer3.Add( self.m_btn_new_profile, 0, wx.ALL, 5 )


        bSizer1.Add( bSizer3, 1, wx.EXPAND, 5 )

        bSizer2 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_btn_ok = wx.Button( self, wx.ID_ANY, _(u"OK"), wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        bSizer2.Add( self.m_btn_ok, 0, wx.RIGHT, 10 )

        self.m_btn_cancel = wx.Button( self, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.m_btn_cancel, 0, 0, 5 )


        bSizer1.Add( bSizer2, 1, wx.ALIGN_RIGHT|wx.RIGHT|wx.TOP, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()

        self.Centre( wx.BOTH )
        ###########################################################################

    ###########################################################################
    ##
    ## Form Builder imports
    ##
    ###########################################################################
    def __del__( self ):
        pass
    ###########################################################################

        
        
    def _load_config(self):
        if 'COPISCore' not in globals():
            from copis.core import COPISCore 
            
        #self.m_btn_ok.Disable()
        self.m_btn_ok.Bind(wx.EVT_BUTTON, self._on_apply)
        self.m_btn_cancel.Bind(wx.EVT_BUTTON, self._on_cancel)
        self.m_file_db.Bind(wx.EVT_FILEPICKER_CHANGED, self._on_db_selected)
        self.m_file_profile.Bind(wx.EVT_FILEPICKER_CHANGED, self._on_profile_selected)
        
        self.m_btn_new_profile.Bind(wx.EVT_BUTTON, self._on_new_profile)   
        
        self.core : COPISCore = self.Parent.core 
        self._glcanvas :GLCanvas3D = self.Parent.viewport_panel.glcanvas
        
        self.m_text_x_dim.SetValue(f'{self.core.config.machine_settings.dimensions.x}') 
        self.m_text_y_dim.SetValue(f'{self.core.config.machine_settings.dimensions.y}') 
        self.m_text_z_dim.SetValue(f'{self.core.config.machine_settings.dimensions.z}')
        
        self.m_text_x_origin.SetValue(f'{self.core.config.machine_settings.origin.x}') 
        self.m_text_y_origin.SetValue(f'{self.core.config.machine_settings.origin.y}') 
        self.m_text_z_origin.SetValue(f'{self.core.config.machine_settings.origin.z}')
        

        db_path = self.core.config.db_path
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
        #db_path = self._get_path_abs_or_relative(db_path)
        self.m_file_db.SetPath(db_path)
        self.m_chk_db_log_tx.SetValue(self.core.config.log_serial_tx) 
        self.m_chk_db_log_rx.SetValue(self.core.config.log_serial_rx) 
        
        pfl_path = self.core.config.profile_path
        #if not os.path.isabs(pfl_path):
        #    pfl_path = os.path.abspath(pfl_path)
        self.m_file_profile.SetPath(pfl_path)
        #if store.get_root() in pfl_path:
        #    pfl_path = pfl_path.replace(store.get_root() ,'')
        
        #self.m_txt_ctrl_profile_path.SetValue(store.get_proxy_path)
    
    def _on_profile_selected(self, event):
        pfl_path = event.GetPath()
        app_root = store.get_root() + os.sep
        if app_root in pfl_path:
            pfl_path = pfl_path.replace(app_root,'')
        self.m_file_profile.SetPath(pfl_path)    
        
    def _on_db_selected(self, event):
        db_path = event.GetPath()
        app_root = store.get_root() + os.sep
        if app_root in db_path:
            db_path = db_path.replace(app_root,'')
        self.m_file_db.SetPath(db_path)  
        
    def _on_new_profile(self,event):
        pfl_dlg =  profile_dialog.dlg_profile(self)        
        pfl_dlg.ShowModal()
        pfl_dlg.Destroy()

    def _on_apply(self, event):
        
        #if not self.core.config._config_parser.has_section('App'):
        #    self.core.config._config_parser.add_section('App')
        #    self.core.config._config_parser['App']['window_min_size'] = '800,600'
        #    self.core.config._config_parser['App']['debug_env'] = 'prod'
        #    self.core.config._config_parser['App']['window_state'] = '0,0,600,800,False'
        
        #if not self.core.config._config_parser.has_section('Machine'):
        #    self.core.config._config_parser.add_section('Machine')    
            
        build_dims = [None] * 6 
        build_dims[0] = float(self.m_text_x_dim.GetValue())
        build_dims[1] = float(self.m_text_y_dim.GetValue())
        build_dims[2] = float(self.m_text_z_dim.GetValue())
        build_dims[3] = float(self.m_text_x_origin.GetValue()) # build_dims[0] *.5
        build_dims[4] = float(self.m_text_y_origin.GetValue()) # build_dims[1] *.5
        build_dims[5] = float(self.m_text_z_origin.GetValue()) # build_dims[2] *.5
        self._glcanvas.build_dimensions = build_dims
        self.core.config.machine_settings.dimensions.x = build_dims[0]
        self.core.config.machine_settings.dimensions.y = build_dims[1]
        self.core.config.machine_settings.dimensions.z = build_dims[2]
        self.core.config.machine_settings.origin.x = build_dims[3]
        self.core.config.machine_settings.origin.y = build_dims[4]
        self.core.config.machine_settings.origin.z = build_dims[5]
        

        #if not self.core.config._config_parser.has_section('System'):
        #    self.core.config._config_parser.add_section('System')
        db_path = self.m_file_db.GetPath()
        #self.core.config._config_parser['System']['db'] = db_path
        self.core.config.db_path = db_path
        self.core.sys_db = SysDB(self.core.config.db_path)
        self.core.config._log_serial_rx = self.m_chk_db_log_rx.GetValue()
        self.core.config._log_serial_tx = self.m_chk_db_log_tx.GetValue()
        serial_log_opts = {'log_tx': self.core.config.log_serial_tx, 'log_rx': self.core.config.log_serial_rx }
        self.core._serial.attach_sys_db(self.core.sys_db, serial_log_opts)
        self.core._edsdk.attach_sys_db(self.core.sys_db)
        
        
        pfl_path = self.m_file_profile.GetPath()
        
        self.core.config.profile_path = pfl_path

        if len(self.core.project.pose_sets) > 0:
            self.core.select_pose_set(-1)
            self.core.select_pose(-1)
            self.core.project.pose_sets.clear()

        self.core.config.save_to_file()
        self.core.project.start(self.core.config.profile_path, self.core.config.default_proxy_path ) 
        self.EndModal(wx.ID_OK)
    
    def _on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
        #self.Close()  # Close the dialog when the Cancel button is clicked

