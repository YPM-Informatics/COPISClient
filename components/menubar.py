import wx
from frames.pathGeneratorFrame import *
from frames.configPreferenceFrame import *

class MenuBar(wx.MenuBar):
    def __init__(self, parent):
        super(MenuBar, self).__init__()
        self.parent = parent

        ## view menu that shows view options
        self.initViewMenu()

        ## tools menu
        self.initToolMenu()

        ## configurataion menu
        self.initConfigMenu()

    def initViewMenu(self):
        viewMenu = wx.Menu()
        ## add statusbar show option to view menu
        name = 'Show statusbar'
        helpMsg = 'Enable or disable statusbar at the bottom of the application.'
        self.shst = viewMenu.Append(wx.ID_ANY, name, helpMsg, kind=wx.ITEM_CHECK)
        ## set default true
        viewMenu.Check(self.shst.GetId(), True)
        self.Bind(wx.EVT_MENU, self.toggleStatusbar, self.shst)
        self.Append(viewMenu, '&View')

    def toggleStatusbar(self, e):
        if self.shst.IsChecked():
            self.parent.statusbar.Show()
        else:
            self.parent.statusbar.Hide()

    def initToolMenu(self):
        toolMenu = wx.Menu()
        name = 'Generate path'
        helpMsg = 'By generating circular or sphere path, you can position cameras in the path and take pictures from it.'
        self.pathGenerator = toolMenu.Append(wx.ID_ANY, name, helpMsg, kind = wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.openPathGeneratorToolbox, self.pathGenerator)
        self.Append(toolMenu, '&Tools')

    def openPathGeneratorToolbox(self, e):
        self.pathGenFrame = PathGeneratorFrame()
        self.pathGenFrame.Show()

    def initConfigMenu(self):
        configMenu = wx.Menu()
        name = 'Preferences'
        helpMsg = 'Choose configuration options by your preference'
        self.preference = configMenu.Append(wx.ID_ANY, name, helpMsg, kind = wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.openConfigPreferenceBox, self.preference)
        self.Append(configMenu, '&Configuration')

    def openConfigPreferenceBox(self, e):
        self.configPrefFrame = ConfigPreferenceFrame()
        self.configPrefFrame.Show()