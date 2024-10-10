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

import wx
import wx.xrc

import gettext
_ = gettext.gettext
import copis.store as store

class AboutDialog(wx.Dialog):
    
###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

    def __init__( self, parent ):
        filename = store.find_path('img/logo_lb3.png')
        
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"About"), pos = wx.DefaultPosition, size = wx.Size( 450,275 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer1 = wx.BoxSizer( wx.VERTICAL )

        self.m_bitmap1 = wx.StaticBitmap( self, wx.ID_ANY, wx.Bitmap(filename, wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1.Add( self.m_bitmap1, 0, wx.ALIGN_CENTER|wx.TOP, 20 )

        self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, _(u"COPIS Client Software\nBuild Version 20241010\nYale Peabody Museum\nDivision of Informatics\ncopis3d.org"), wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL )
        self.m_staticText1.Wrap( -1 )

        bSizer1.Add( self.m_staticText1, 0, wx.ALIGN_CENTER|wx.TOP, 20 )


        self.SetSizer( bSizer1 )
        self.Layout()

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass