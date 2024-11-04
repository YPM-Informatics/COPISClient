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

"""COPIS Proxy Info Properties Panel"""


import wx

from copis.gui.wxutils import simple_statictext

from copis.classes import Object3D, AABoxObject3D, CylinderObject3D

class ProxyInfo(wx.Panel): 
    """Proxy Object panel to display details and settings for proxy objects"""

    def __init__(self, parent) -> None:
        super().__init__(parent, style=wx.BORDER_NONE)
        self.parent = parent
        self._object = None
        

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Proxy Object Info'), wx.VERTICAL)

        #create a grid to display proxy object details
        grid = wx.FlexGridSizer(4, 2, 0, 0)
        grid.AddGrowableCol(1, 0)

        self.id_text = wx.StaticText(self, label = '')
        self.name_text = wx.StaticText(self, label = '')
        self.type_text = wx.StaticText(self, label = '')
        self.desc_text = wx.StaticText(self, label = '')
        
        grid.AddMany([
            (simple_statictext(self, 'ID:', 80), 0, wx.EXPAND, 0),
            (self.id_text, 0, wx.EXPAND, 0),

            (simple_statictext(self, 'Name:', 80), 0, wx.EXPAND, 0),
            (self.name_text, 0, wx.EXPAND, 0),

            (simple_statictext(self, 'Type:', 80), 0, wx.EXPAND, 0),
            (self.type_text, 0, wx.EXPAND, 0),

            (simple_statictext(self, 'Description:', 80), 0, wx.EXPAND, 0),
            (self.desc_text, 0, wx.EXPAND, 0),
        ])

        self.box_sizer.Add(grid, 0, wx.ALL|wx.EXPAND,4)
        self.Sizer.Add(self.box_sizer, 0, wx.ALL|wx.EXPAND, 7)
        self.Layout()

    def set_proxy(self, object: Object3D):
        '''parses proxy attributes'''
        self.id_text.Label = "str(object.id)"
        self.name_text.Label =object.name
        self.type_text.Label =object.type
        self.desc_text.Label = "object.description"