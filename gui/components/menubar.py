#!/usr/bin/env python3

import wx
from gui.pathgen_frame import *
from gui.pref_frame import *


class MenuBar(wx.MenuBar):
    def __init__(self, parent, *args, **kwargs):
        super(MenuBar, self).__init__()
        self.parent = parent

        self.initViewMenu()
        self.initToolMenu()
        self.initConfigMenu()

    def initViewMenu(self):
        viewMenu = wx.Menu()

        # add enabling statusbar option
        name = 'Show statusbar'
        helpMsg = 'Enable or disable statusbar at the bottom of the application.'
        self.shst = viewMenu.Append(wx.ID_ANY, name, helpMsg, kind=wx.ITEM_CHECK)

        # set default to true
        viewMenu.Check(self.shst.GetId(), True)
        self.Bind(wx.EVT_MENU, self.toggleStatusbar, self.shst)
        self.Append(viewMenu, '&View')

    def toggleStatusbar(self, e):
        if self.shst.IsChecked():
            self.parent.GetStatusBar().Show()
        else:
            self.parent.GetStatusBar().Hide()

    def initToolMenu(self):
        toolMenu = wx.Menu()

        # add path generator
        name = 'Generate path'
        helpMsg = 'By generating a circular or sphere path, you can position cameras in the path and take pictures.'
        self.path_generator = toolMenu.Append(wx.ID_ANY, name, helpMsg, kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.openPathGeneratorToolbox, self.path_generator)
        self.Append(toolMenu, '&Tools')

    def openPathGeneratorToolbox(self, e):
        self.path_generator = PathGeneratorFrame()
        self.path_generator.Show()

    def initConfigMenu(self):
        configMenu = wx.Menu()

        # add configuration preferences setting
        name = 'Preferences'
        helpMsg = 'Choose configuration options by your preference'
        self.preference = configMenu.Append(wx.ID_ANY, name, helpMsg, kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.open_pref_box, self.preference)
        self.Append(configMenu, '&Configuration')

    def open_pref_box(self, e):
        self.pref_frame = PreferenceFrame()
        self.pref_frame.Show()
