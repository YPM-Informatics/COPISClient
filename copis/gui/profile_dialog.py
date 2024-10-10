# -*- coding: utf-8 -*-

###########################################################################
## Parts of this file generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
## http://www.wxformbuilder.org/
## FORM BUILDER IMPORTS
###########################################################################

import os
import json
import wx
import wx.xrc
import gettext
_ = gettext.gettext

###########################################################################

import uuid
import copis.store as store
from copis.classes.sys_db import SysDB
from copis.gl.glcanvas import GLCanvas3D

class dlg_profile ( wx.Dialog ):

    def __init__( self, parent ):
        
        self._local_devices_dict = {}
        self._load_wx_form(parent)
        self._load_profile()

   
    def _load_wx_form(self, parent):
        ###########################################################################
        ## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
        ## http://www.wxformbuilder.org/
        ##
        ## PLEASE DO *NOT* EDIT THIS!
        ###########################################################################
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"Machine Profile Configuration"), pos = wx.DefaultPosition, size = wx.Size( 516,678 ), style = wx.DEFAULT_DIALOG_STYLE|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.RESIZE_BORDER )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer6 = wx.BoxSizer( wx.VERTICAL )

        fgSizer5 = wx.FlexGridSizer( 0, 1, 10, 0 )
        fgSizer5.SetFlexibleDirection( wx.BOTH )
        fgSizer5.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        fgSizer25 = wx.FlexGridSizer( 0, 1, 10, 0 )
        fgSizer25.SetFlexibleDirection( wx.BOTH )
        fgSizer25.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        fgSizer221 = wx.FlexGridSizer( 1, 8, 0, 15 )
        fgSizer221.SetFlexibleDirection( wx.BOTH )
        fgSizer221.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        bSizer401 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText531 = wx.StaticText( self, wx.ID_ANY, _(u"Cameras"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText531.Wrap( -1 )

        bSizer401.Add( self.m_staticText531, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )

        m_lst_ctrl_camsChoices = []
        self.m_lst_ctrl_cams = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_lst_ctrl_camsChoices, 0 )
        self.m_lst_ctrl_cams.SetMinSize( wx.Size( 80,80 ) )

        bSizer401.Add( self.m_lst_ctrl_cams, 0, wx.ALL, 5 )

        self.m_btn_cam_update = wx.Button( self, wx.ID_ANY, _(u"Update"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer401.Add( self.m_btn_cam_update, 0, wx.ALL, 5 )

        self.m_btn_cam_insert = wx.Button( self, wx.ID_ANY, _(u"Insert"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer401.Add( self.m_btn_cam_insert, 0, wx.ALL, 5 )

        self.m_btn_cam_delete = wx.Button( self, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer401.Add( self.m_btn_cam_delete, 0, wx.ALL, 5 )


        fgSizer221.Add( bSizer401, 1, wx.EXPAND, 5 )

        bSizer332 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText501 = wx.StaticText( self, wx.ID_ANY, _(u"Details"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText501.Wrap( -1 )

        bSizer332.Add( self.m_staticText501, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )

        fgSizer35 = wx.FlexGridSizer( 4, 0, 0, 0 )
        fgSizer35.SetFlexibleDirection( wx.BOTH )
        fgSizer35.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        fgSizer36 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer36.SetFlexibleDirection( wx.BOTH )
        fgSizer36.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText63 = wx.StaticText( self, wx.ID_ANY, _(u"ID"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText63.Wrap( -1 )

        fgSizer36.Add( self.m_staticText63, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )

        self.m_txt_ctrl_cam_id = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_id.SetMinSize( wx.Size( 75,-1 ) )

        fgSizer36.Add( self.m_txt_ctrl_cam_id, 0, wx.ALL, 5 )

        self.m_staticText67 = wx.StaticText( self, wx.ID_ANY, _(u"Serial #"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText67.Wrap( -1 )

        fgSizer36.Add( self.m_staticText67, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )

        self.m_txt_ctrl_cam_sn = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_sn.SetMinSize( wx.Size( 75,-1 ) )

        fgSizer36.Add( self.m_txt_ctrl_cam_sn, 0, wx.ALL, 5 )

        self.m_staticText64 = wx.StaticText( self, wx.ID_ANY, _(u"Name"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText64.Wrap( -1 )

        fgSizer36.Add( self.m_staticText64, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )

        self.m_txt_ctrl_cam_name = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_name.SetMinSize( wx.Size( 75,-1 ) )

        fgSizer36.Add( self.m_txt_ctrl_cam_name, 0, wx.ALL, 5 )

        self.m_staticText65 = wx.StaticText( self, wx.ID_ANY, _(u"Type"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText65.Wrap( -1 )

        fgSizer36.Add( self.m_staticText65, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )

        self.m_txt_ctrl_cam_type = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_type.SetMinSize( wx.Size( 75,-1 ) )

        fgSizer36.Add( self.m_txt_ctrl_cam_type, 0, wx.ALL, 5 )


        fgSizer35.Add( fgSizer36, 1, wx.EXPAND, 5 )


        bSizer332.Add( fgSizer35, 1, wx.EXPAND, 5 )

        fgSizer40 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer40.SetFlexibleDirection( wx.BOTH )
        fgSizer40.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )


        bSizer332.Add( fgSizer40, 1, wx.EXPAND, 5 )


        fgSizer221.Add( bSizer332, 1, wx.EXPAND, 5 )

        bSizer33241 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticline2 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL )
        bSizer33241.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )


        fgSizer221.Add( bSizer33241, 1, wx.EXPAND, 5 )

        bSizer3321 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText5011 = wx.StaticText( self, wx.ID_ANY, _(u"Home Pos"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText5011.Wrap( -1 )

        bSizer3321.Add( self.m_staticText5011, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )

        fgSizer351 = wx.FlexGridSizer( 4, 0, 0, 0 )
        fgSizer351.SetFlexibleDirection( wx.BOTH )
        fgSizer351.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        fgSizer361 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer361.SetFlexibleDirection( wx.BOTH )
        fgSizer361.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText631 = wx.StaticText( self, wx.ID_ANY, _(u"X"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText631.Wrap( -1 )

        fgSizer361.Add( self.m_staticText631, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )

        self.m_txt_ctrl_cam_home_x = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_home_x.SetMinSize( wx.Size( 50,-1 ) )

        fgSizer361.Add( self.m_txt_ctrl_cam_home_x, 0, wx.ALL, 5 )

        self.m_staticText671 = wx.StaticText( self, wx.ID_ANY, _(u"Y"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText671.Wrap( -1 )

        fgSizer361.Add( self.m_staticText671, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )

        self.m_txt_ctrl_cam_home_y = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_home_y.SetMinSize( wx.Size( 50,-1 ) )

        fgSizer361.Add( self.m_txt_ctrl_cam_home_y, 0, wx.ALL, 5 )

        self.m_staticText641 = wx.StaticText( self, wx.ID_ANY, _(u"Z"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText641.Wrap( -1 )

        fgSizer361.Add( self.m_staticText641, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )

        self.m_txt_ctrl_cam_home_z = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_home_z.SetMinSize( wx.Size( 50,-1 ) )

        fgSizer361.Add( self.m_txt_ctrl_cam_home_z, 0, wx.ALL, 5 )

        self.m_staticText651 = wx.StaticText( self, wx.ID_ANY, _(u"P"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText651.Wrap( -1 )

        fgSizer361.Add( self.m_staticText651, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )

        self.m_txt_ctrl_cam_home_p = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_home_p.SetMinSize( wx.Size( 50,-1 ) )

        fgSizer361.Add( self.m_txt_ctrl_cam_home_p, 0, wx.ALL, 5 )

        self.m_staticText6511 = wx.StaticText( self, wx.ID_ANY, _(u"T"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText6511.Wrap( -1 )

        fgSizer361.Add( self.m_staticText6511, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )

        self.m_txt_ctrl_cam_home_t = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_home_t.SetMinSize( wx.Size( 50,-1 ) )

        fgSizer361.Add( self.m_txt_ctrl_cam_home_t, 0, wx.ALL, 5 )


        fgSizer351.Add( fgSizer361, 1, wx.EXPAND, 5 )


        bSizer3321.Add( fgSizer351, 1, wx.EXPAND, 5 )

        fgSizer401 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer401.SetFlexibleDirection( wx.BOTH )
        fgSizer401.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )


        bSizer3321.Add( fgSizer401, 1, wx.EXPAND, 5 )


        fgSizer221.Add( bSizer3321, 1, wx.EXPAND, 5 )

        bSizer3322 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText5012 = wx.StaticText( self, wx.ID_ANY, _(u"Min"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText5012.Wrap( -1 )

        bSizer3322.Add( self.m_staticText5012, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )

        fgSizer352 = wx.FlexGridSizer( 4, 0, 0, 0 )
        fgSizer352.SetFlexibleDirection( wx.BOTH )
        fgSizer352.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        fgSizer362 = wx.FlexGridSizer( 5, 0, 0, 0 )
        fgSizer362.SetFlexibleDirection( wx.BOTH )
        fgSizer362.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_txt_ctrl_cam_min_x = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_min_x.SetMinSize( wx.Size( 50,-1 ) )

        fgSizer362.Add( self.m_txt_ctrl_cam_min_x, 0, wx.ALL, 5 )

        self.m_txt_ctrl_cam_min_y = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_min_y.SetMinSize( wx.Size( 50,-1 ) )

        fgSizer362.Add( self.m_txt_ctrl_cam_min_y, 0, wx.ALL, 5 )

        self.m_txt_ctrl_cam_min_z = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_min_z.SetMinSize( wx.Size( 50,-1 ) )

        fgSizer362.Add( self.m_txt_ctrl_cam_min_z, 0, wx.ALL, 5 )


        fgSizer352.Add( fgSizer362, 1, wx.EXPAND, 5 )


        bSizer3322.Add( fgSizer352, 1, wx.EXPAND, 5 )

        fgSizer402 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer402.SetFlexibleDirection( wx.BOTH )
        fgSizer402.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )


        bSizer3322.Add( fgSizer402, 1, wx.EXPAND, 5 )


        fgSizer221.Add( bSizer3322, 1, wx.EXPAND, 5 )

        bSizer93 = wx.BoxSizer( wx.VERTICAL )

        bSizer33221 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText50121 = wx.StaticText( self, wx.ID_ANY, _(u"Max"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText50121.Wrap( -1 )

        bSizer33221.Add( self.m_staticText50121, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )

        fgSizer3521 = wx.FlexGridSizer( 4, 0, 0, 0 )
        fgSizer3521.SetFlexibleDirection( wx.BOTH )
        fgSizer3521.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        fgSizer3621 = wx.FlexGridSizer( 5, 0, 0, 0 )
        fgSizer3621.SetFlexibleDirection( wx.BOTH )
        fgSizer3621.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_txt_ctrl_cam_max_x = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_max_x.SetMinSize( wx.Size( 50,-1 ) )

        fgSizer3621.Add( self.m_txt_ctrl_cam_max_x, 0, wx.ALL, 5 )

        self.m_txt_ctrl_cam_max_y = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_max_y.SetMinSize( wx.Size( 50,-1 ) )

        fgSizer3621.Add( self.m_txt_ctrl_cam_max_y, 0, wx.ALL, 5 )

        self.m_txt_ctrl_cam_max_z = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_max_z.SetMinSize( wx.Size( 50,-1 ) )

        fgSizer3621.Add( self.m_txt_ctrl_cam_max_z, 0, wx.ALL, 5 )


        fgSizer3521.Add( fgSizer3621, 1, wx.EXPAND, 5 )


        bSizer33221.Add( fgSizer3521, 1, wx.EXPAND, 5 )

        fgSizer4021 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer4021.SetFlexibleDirection( wx.BOTH )
        fgSizer4021.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )


        bSizer33221.Add( fgSizer4021, 1, wx.EXPAND, 5 )


        bSizer93.Add( bSizer33221, 1, 0, 5 )


        fgSizer221.Add( bSizer93, 1, wx.EXPAND, 5 )


        fgSizer25.Add( fgSizer221, 1, 0, 5 )

        fgSizer101 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer101.SetFlexibleDirection( wx.BOTH )
        fgSizer101.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText169 = wx.StaticText( self, wx.ID_ANY, _(u"Port"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText169.Wrap( -1 )

        fgSizer101.Add( self.m_staticText169, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )

        self.m_txt_ctrl_cam_port = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_cam_port.SetMinSize( wx.Size( 300,-1 ) )

        fgSizer101.Add( self.m_txt_ctrl_cam_port, 0, wx.ALL, 5 )

        self.m_staticText1691 = wx.StaticText( self, wx.ID_ANY, _(u"EDSDK save path"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1691.Wrap( -1 )

        fgSizer101.Add( self.m_staticText1691, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.LEFT, 5 )

        self.m_txt_ctrl_edsdk = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_txt_ctrl_edsdk.SetMinSize( wx.Size( 300,-1 ) )

        fgSizer101.Add( self.m_txt_ctrl_edsdk, 0, wx.ALL, 5 )


        fgSizer25.Add( fgSizer101, 1, wx.EXPAND|wx.SHAPED, 5 )

        self.m_staticline6 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        fgSizer25.Add( self.m_staticline6, 0, wx.EXPAND |wx.ALL, 5 )

        fgSizer22 = wx.FlexGridSizer( 0, 4, 0, 0 )
        fgSizer22.SetFlexibleDirection( wx.BOTH )
        fgSizer22.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        bSizer40 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText53 = wx.StaticText( self, wx.ID_ANY, _(u"Homing Commands"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText53.Wrap( -1 )

        bSizer40.Add( self.m_staticText53, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        m_lst_ctrl_homing_cmdsChoices = []
        self.m_lst_ctrl_homing_cmds = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_lst_ctrl_homing_cmdsChoices, 0 )
        self.m_lst_ctrl_homing_cmds.SetMinSize( wx.Size( 200,150 ) )

        bSizer40.Add( self.m_lst_ctrl_homing_cmds, 0, wx.ALL, 5 )


        fgSizer22.Add( bSizer40, 1, wx.EXPAND|wx.LEFT, 5 )

        bSizer331 = wx.BoxSizer( wx.VERTICAL )

        self.m_btn_homing_up = wx.Button( self, wx.ID_ANY, _(u"Move Up"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
        bSizer331.Add( self.m_btn_homing_up, 0, wx.ALL, 5 )

        self.m_btn_homing_down = wx.Button( self, wx.ID_ANY, _(u"Move Down"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
        bSizer331.Add( self.m_btn_homing_down, 0, wx.ALL, 5 )

        self.m_btn_homing_delete = wx.Button( self, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
        bSizer331.Add( self.m_btn_homing_delete, 0, wx.ALL, 5 )

        self.m_btn_homing_insert = wx.Button( self, wx.ID_ANY, _(u"Insert"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
        bSizer331.Add( self.m_btn_homing_insert, 0, wx.ALL, 5 )

        self.m_btn_homing_replace = wx.Button( self, wx.ID_ANY, _(u"Replace"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
        bSizer331.Add( self.m_btn_homing_replace, 0, wx.ALL, 5 )


        fgSizer22.Add( bSizer331, 1, wx.ALIGN_BOTTOM, 5 )


        fgSizer25.Add( fgSizer22, 1, wx.EXPAND, 5 )

        self.m_staticline7 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        fgSizer25.Add( self.m_staticline7, 0, wx.EXPAND |wx.ALL, 5 )

        fgSizer23 = wx.FlexGridSizer( 0, 3, 0, 0 )
        fgSizer23.SetFlexibleDirection( wx.BOTH )
        fgSizer23.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText1111 = wx.StaticText( self, wx.ID_ANY, _(u"Save to:"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1111.Wrap( -1 )

        fgSizer23.Add( self.m_staticText1111, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.m_file_profile = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, _(u"Select a file"), _(u"*.*"), wx.DefaultPosition, wx.Size( 350,-1 ), wx.FLP_SAVE|wx.FLP_USE_TEXTCTRL )
        fgSizer23.Add( self.m_file_profile, 0, wx.ALL, 5 )


        fgSizer25.Add( fgSizer23, 1, wx.EXPAND, 5 )

        self.m_staticline5 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        fgSizer25.Add( self.m_staticline5, 0, wx.EXPAND |wx.ALL, 5 )


        fgSizer5.Add( fgSizer25, 1, wx.EXPAND|wx.SHAPED, 5 )

        fgSizer102 = wx.FlexGridSizer( 0, 2, 0, 20 )
        fgSizer102.SetFlexibleDirection( wx.BOTH )
        fgSizer102.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_btn_cancel = wx.Button( self, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer102.Add( self.m_btn_cancel, 0, wx.ALIGN_CENTER, 5 )

        self.m_btn_apply = wx.Button( self, wx.ID_ANY, _(u"Apply"), wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer102.Add( self.m_btn_apply, 0, wx.ALIGN_CENTER, 5 )


        fgSizer5.Add( fgSizer102, 1, wx.ALIGN_RIGHT|wx.EXPAND, 5 )


        bSizer6.Add( fgSizer5, 1, wx.EXPAND, 5 )


        self.SetSizer( bSizer6 )
        self.Layout()

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass

    def _load_profile(self):
        if 'COPISCore' not in globals():
            from copis.core import COPISCore 
        
        self.core : COPISCore = self.Parent.core 
        
            
        #self.m_btn_apply.Disable()
        self.m_btn_apply.Bind(wx.EVT_BUTTON, self._on_apply)
        self.m_btn_cancel.Bind(wx.EVT_BUTTON, self._on_cancel)
        self.m_lst_ctrl_cams.Bind(wx.EVT_LISTBOX, self._on_cam_selected)    
        self.m_btn_cam_insert.Bind(wx.EVT_BUTTON, self._on_cam_add) 
        self.m_btn_cam_update.Bind(wx.EVT_BUTTON, self._on_cam_update) 
        self.m_btn_cam_delete.Bind(wx.EVT_BUTTON, self._on_cam_delete) 
        
        self.m_btn_homing_insert.Bind(wx.EVT_BUTTON, self._on_homing_add)
        self.m_btn_homing_delete.Bind(wx.EVT_BUTTON, self._on_homing_remove)
        self.m_btn_homing_replace.Bind(wx.EVT_BUTTON, self._on_homing_replace)
        self.m_btn_homing_up.Bind(wx.EVT_BUTTON, self._on_move_homing_up)
        self.m_btn_homing_down.Bind(wx.EVT_BUTTON, self._on_move_homing_down)
        
        self.m_file_profile.Bind(wx.EVT_FILEPICKER_CHANGED, self._on_profile_selected)
        
        self.m_file_profile.SetPath(self.core.config.profile_path)
        
        with open(self.core.config.profile_path, 'r', encoding='utf-8') as file: #--> self.core.project._profile might be better to reference already loaded profile rather than re-reading it from disk
            pfl = json.load(file)
        h = self.core.project.homing_sequence
        self.m_lst_ctrl_homing_cmds.Clear()
        for s in h:
            self.m_lst_ctrl_homing_cmds.Append(s)
        self._local_devices_dict = {}
        if 'devices' in pfl:
            for d in pfl['devices']:
                self.m_lst_ctrl_cams.Append(str(d['id']))
                self._local_devices_dict[d['id']] = d
    

    def _load_device(self, dev_id: int):
        device = self._local_devices_dict[dev_id]
        if 'serial_no' not in device:
            device['serial_no'] = ''
        if 'name' not in device:
            device['name'] = ''
        if 'type' not in device:
            device['type'] = 'Camera'
        if 'description' not in device:
            device['description'] = ''
        if 'home_position' not in device:
            device['home_position'] = [0,0,0,0,0]
        if 'range_x' not in device:
            device['range_x'] = [-800,800]
        if 'range_y' not in device:
            device['range_y'] = [-800,800]
        if 'range_z' not in device:
            device['range_z'] = [-800,800]
        if 'size' not in device:
            device['size'] = [350,250,200]
        if 'port' not in device:
            device['port'] = ""
        if 'edsdk_save_to_path' not in device:
            device['edsdk_save_to_path'] = ""
        if 'head_radius' not in device:
            device['head_radius'] = 200
        if 'body_dims' not in device:
            device['body_dims'] = [ 100, 40, 740 ]
        if 'gantry_dims' not in device:
            device['gantry_dims'] = [ 1000, 125, 100 ]
                    
        self.m_txt_ctrl_cam_id.SetValue(str(device['id']))
        self.m_txt_ctrl_cam_sn.SetValue(device['serial_no'])
        self.m_txt_ctrl_cam_name.SetValue(device['name'])
        self.m_txt_ctrl_cam_type.SetValue(device['type'])
        #self.m_txt_ctrl_cam_desc.SetValue(device['description'])
        self.m_txt_ctrl_cam_home_x.SetValue(str(device['home_position'][0]))
        self.m_txt_ctrl_cam_home_y.SetValue(str(device['home_position'][1]))
        self.m_txt_ctrl_cam_home_z.SetValue(str(device['home_position'][2]))
        self.m_txt_ctrl_cam_home_p.SetValue(str(device['home_position'][3]))
        self.m_txt_ctrl_cam_home_t.SetValue(str(device['home_position'][4]))
        self.m_txt_ctrl_cam_min_x.SetValue(str(device['range_x'][0]))    
        self.m_txt_ctrl_cam_max_x.SetValue(str(device['range_x'][1])) 
        self.m_txt_ctrl_cam_min_y.SetValue(str(device['range_y'][0]))    
        self.m_txt_ctrl_cam_max_y.SetValue(str(device['range_y'][1]))
        self.m_txt_ctrl_cam_min_z.SetValue(str(device['range_z'][0]))    
        self.m_txt_ctrl_cam_max_z.SetValue(str(device['range_z'][1])) 
        self.m_txt_ctrl_cam_port.SetValue(device['port'])
        self.m_txt_ctrl_edsdk.SetValue(device['edsdk_save_to_path'])
    
    def _on_cam_selected(self, event):
        selection = int(self.m_lst_ctrl_cams.GetStringSelection())
        self._load_device(selection)
    
    def _on_cam_add(self, event):
        if not self.m_txt_ctrl_cam_id.GetValue().isdigit():
            wx.MessageBox("Unable to add Camera; Invalid ID",  "ID Must be an Integer", wx.OK | wx.ICON_INFORMATION)
            return
        if int(self.m_txt_ctrl_cam_id.GetValue()) in self._local_devices_dict:
             wx.MessageBox("Unable to add Camera; ID already exists",  "ID Already Exists", wx.OK | wx.ICON_INFORMATION)
             return
        id = int(self.m_txt_ctrl_cam_id.GetValue()) 
        self._local_devices_dict[id] = {}
        self._local_devices_dict[id]['id'] = int(self.m_txt_ctrl_cam_id.GetValue())
        self._local_devices_dict[id]['serial_no'] = self.m_txt_ctrl_cam_sn.GetValue()
        self._local_devices_dict[id]['name'] = self.m_txt_ctrl_cam_name.GetValue()
        self._local_devices_dict[id]['type'] =self.m_txt_ctrl_cam_type.GetValue()
        self._local_devices_dict[id]['description'] = ''
        self._local_devices_dict[id]['home_position'] = [0] * 5
        self._local_devices_dict[id]['home_position'][0] = float(self.m_txt_ctrl_cam_home_x.GetValue())
        self._local_devices_dict[id]['home_position'][1] = float(self.m_txt_ctrl_cam_home_y.GetValue())
        self._local_devices_dict[id]['home_position'][2] = float(self.m_txt_ctrl_cam_home_z.GetValue())
        self._local_devices_dict[id]['home_position'][3] = float(self.m_txt_ctrl_cam_home_p.GetValue())
        self._local_devices_dict[id]['home_position'][4] = float(self.m_txt_ctrl_cam_home_t.GetValue())
        self._local_devices_dict[id]['range_x'] = [0] * 2
        self._local_devices_dict[id]['range_x'][0] = float(self.m_txt_ctrl_cam_min_x.GetValue())
        self._local_devices_dict[id]['range_x'][1] = float(self.m_txt_ctrl_cam_max_x.GetValue())
        self._local_devices_dict[id]['range_y'] = [0] * 2
        self._local_devices_dict[id]['range_y'][0] = float(self.m_txt_ctrl_cam_min_y.GetValue())
        self._local_devices_dict[id]['range_y'][1] = float(self.m_txt_ctrl_cam_max_y.GetValue())
        self._local_devices_dict[id]['range_z'] = [0] * 2
        self._local_devices_dict[id]['range_z'][0] = float(self.m_txt_ctrl_cam_min_z.GetValue())
        self._local_devices_dict[id]['range_z'][1] = float(self.m_txt_ctrl_cam_max_z.GetValue())
        self._local_devices_dict[id]['port'] = self.m_txt_ctrl_cam_port.GetValue()
        self._local_devices_dict[id]['edsdk_save_to_path'] = self.m_txt_ctrl_edsdk.GetValue()
        self.m_lst_ctrl_cams.Append(self.m_txt_ctrl_cam_id.GetValue())
        self.m_lst_ctrl_cams.SetSelection(self.m_lst_ctrl_cams.GetCount()-1)

    def _on_cam_delete(self, event):
        selected_index  = self.m_lst_ctrl_cams.GetSelection()
        if selected_index != wx.NOT_FOUND:
            dev_id = int(self.m_lst_ctrl_cams.GetString(selected_index))
            self.m_lst_ctrl_cams.Delete(selected_index)
            self._local_devices_dict.pop(dev_id)
        
    def _on_cam_update(self, event):
        selected_index  = self.m_lst_ctrl_cams.GetSelection()
        if selected_index  != wx.NOT_FOUND:
            dev_id = int(self.m_lst_ctrl_cams.GetString(selected_index))
            if not self.m_txt_ctrl_cam_id.GetValue().isdigit():
                wx.MessageBox("Unable to update Camera; Invalid ID",  "ID Must be an Integer", wx.OK | wx.ICON_INFORMATION)
                return
            if (dev_id == int(self.m_txt_ctrl_cam_id.GetValue())) or (int(self.m_txt_ctrl_cam_id.GetValue()) not in self._local_devices_dict): 
                id = int(self.m_txt_ctrl_cam_id.GetValue()) 
                self._local_devices_dict[id] = {}
                self._local_devices_dict[id]['id'] = int(self.m_txt_ctrl_cam_id.GetValue())
                self._local_devices_dict[id]['serial_no'] = self.m_txt_ctrl_cam_sn.GetValue()
                self._local_devices_dict[id]['name'] = self.m_txt_ctrl_cam_name.GetValue()
                self._local_devices_dict[id]['type'] =self.m_txt_ctrl_cam_type.GetValue()
                self._local_devices_dict[id]['description'] = ''
                self._local_devices_dict[id]['home_position'] = [0] * 5
                self._local_devices_dict[id]['home_position'][0] = float(self.m_txt_ctrl_cam_home_x.GetValue())
                self._local_devices_dict[id]['home_position'][1] = float(self.m_txt_ctrl_cam_home_y.GetValue())
                self._local_devices_dict[id]['home_position'][2] = float(self.m_txt_ctrl_cam_home_z.GetValue())
                self._local_devices_dict[id]['home_position'][3] = float(self.m_txt_ctrl_cam_home_p.GetValue())
                self._local_devices_dict[id]['home_position'][4] = float(self.m_txt_ctrl_cam_home_t.GetValue())
                self._local_devices_dict[id]['range_x'] = [0] * 2
                self._local_devices_dict[id]['range_x'][0] = float(self.m_txt_ctrl_cam_min_x.GetValue())
                self._local_devices_dict[id]['range_x'][1] = float(self.m_txt_ctrl_cam_max_x.GetValue())
                self._local_devices_dict[id]['range_y'] = [0] * 2
                self._local_devices_dict[id]['range_y'][0] = float(self.m_txt_ctrl_cam_min_y.GetValue())
                self._local_devices_dict[id]['range_y'][1] = float(self.m_txt_ctrl_cam_max_y.GetValue())
                self._local_devices_dict[id]['range_z'] = [0] * 2
                self._local_devices_dict[id]['range_z'][0] = float(self.m_txt_ctrl_cam_min_z.GetValue())
                self._local_devices_dict[id]['range_z'][1] = float(self.m_txt_ctrl_cam_max_z.GetValue())
                self._local_devices_dict[id]['port'] = self.m_txt_ctrl_cam_port.GetValue()
                self._local_devices_dict[id]['edsdk_save_to_path'] = self.m_txt_ctrl_edsdk.GetValue()
                self.m_lst_ctrl_cams.Delete(selected_index)
                self.m_lst_ctrl_cams.Insert(self.m_txt_ctrl_cam_id.GetValue(), selected_index)
                self.m_lst_ctrl_cams.SetSelection(selected_index)
            else:
                wx.MessageBox("Unable to update camera",  "ID conflict", wx.OK | wx.ICON_INFORMATION)
                return
            
        

    def _on_homing_add(self, event):
        item = wx.GetTextFromUser("Enter a new item:", "Add Item")
        if item:
            self.m_lst_ctrl_homing_cmds.Append(item)
            
    def _on_homing_remove(self, event):
        selection = self.m_lst_ctrl_homing_cmds.GetSelection()
        if selection != wx.NOT_FOUND:
            self.m_lst_ctrl_homing_cmds.Delete(selection)
 
    def _on_homing_replace(self, event):
        selection = self.m_lst_ctrl_homing_cmds.GetSelection()
        if selection != wx.NOT_FOUND:
            item = wx.GetTextFromUser("Enter a new item:", "Replace Item")
            if item:
                self.m_lst_ctrl_homing_cmds.SetString(selection, item)
        
    def _on_move_homing_up(self, event):
        selection = self.m_lst_ctrl_homing_cmds.GetSelection()
        if selection > 0:
            item = self.m_lst_ctrl_homing_cmds.GetString(selection)
            self.m_lst_ctrl_homing_cmds.Delete(selection)
            self.m_lst_ctrl_homing_cmds.Insert(item, selection - 1)
            self.m_lst_ctrl_homing_cmds.SetSelection(selection - 1)
        
    def _on_move_homing_down(self, event):
        selection = self.m_lst_ctrl_homing_cmds.GetSelection()
        if selection != wx.NOT_FOUND and selection < self.m_lst_ctrl_homing_cmds.GetCount() - 1:
            item = self.m_lst_ctrl_homing_cmds.GetString(selection)
            self.m_lst_ctrl_homing_cmds.Delete(selection)
            self.m_lst_ctrl_homing_cmds.Insert(item, selection + 1)
            self.m_lst_ctrl_homing_cmds.SetSelection(selection + 1)
    
    def _on_profile_selected(self, event):
        filepath = event.GetPath()
        app_root = store.get_root() + os.sep
        if app_root in filepath:
            filepath = filepath.replace(app_root,'')
        self.m_file_profile.SetPath(filepath)

    def _on_apply(self, event):
        out_filepath = self.m_file_profile.GetPath()
        out_data = {}
        out_data['devices'] = []
        
        for id,dev in self._local_devices_dict.items():
            out_data['devices'].append(dev)
        
        out_data['homing_sequence'] =  '\n'.join( self.m_lst_ctrl_homing_cmds.GetItems())
        
        with open(out_filepath, 'w', encoding='utf-8') as file:
            json.dump(out_data, file, indent='\t')
        
        if len(self.core.project.pose_sets) > 0:
            self.core.select_pose_set(-1)
            self.core.select_pose(-1)
            self.core.project.pose_sets.clear()
            
        self.core.config.profile_path = out_filepath    
        self.core.config.save_to_file()
        
        self._glcanvas :GLCanvas3D = self.Parent.viewport_panel.glcanvas
        self._glcanvas._actionvis._initialized = False
        self.core.project.start(self.core.config.profile_path, self.core.config.default_proxy_path ) 
        #self._glcanvas :GLCanvas3D = self.Parent.viewport_panel.glcanvas
        #self._glcanvas._actionvis._initialized = False
        
        self.EndModal(wx.ID_OK)
    
    def _on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
        
