#!/usr/bin/env python3

import wx
# from wx.lib.pubsub import Publisher


class PreferenceDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id = wx.ID_ANY, title = 'Preferences', pos = wx.DefaultPosition, size = wx.Size(500,500), style = wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer2 = wx.BoxSizer(wx.VERTICAL)

        self.m_listbook7 = wx.Listbook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LB_DEFAULT)
        self.m_panel30 = wx.Panel(self.m_listbook7, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer11 = wx.BoxSizer(wx.VERTICAL)

        sbSizer13 = wx.StaticBoxSizer(wx.StaticBox(self.m_panel30, wx.ID_ANY, 'Theme'), wx.VERTICAL)


        bSizer11.Add(sbSizer13, 0, wx.ALL|wx.EXPAND, 5)


        self.m_panel30.SetSizer(bSizer11)
        self.m_panel30.Layout()
        bSizer11.Fit(self.m_panel30)
        self.m_listbook7.AddPage(self.m_panel30, 'General', False)
        self.m_panel351 = wx.Panel(self.m_listbook7, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer121 = wx.BoxSizer(wx.VERTICAL)

        sbSizer121 = wx.StaticBoxSizer(wx.StaticBox(self.m_panel351, wx.ID_ANY, 'Appearance'), wx.VERTICAL)

        self.m_checkBox12 = wx.CheckBox(sbSizer121.GetStaticBox(), wx.ID_ANY, 'Show axes', wx.DefaultPosition, wx.DefaultSize, 0)
        sbSizer121.Add(self.m_checkBox12, 0, wx.ALL|wx.EXPAND, 2)

        self.m_checkBox111 = wx.CheckBox(sbSizer121.GetStaticBox(), wx.ID_ANY, 'Show axes', wx.DefaultPosition, wx.DefaultSize, 0)
        sbSizer121.Add(self.m_checkBox111, 0, wx.ALL|wx.EXPAND, 2)


        bSizer121.Add(sbSizer121, 0, wx.ALL|wx.EXPAND, 5)

        sbSizer22 = wx.StaticBoxSizer(wx.StaticBox(self.m_panel351, wx.ID_ANY, 'Grid'), wx.VERTICAL)

        fgSizer2 = wx.FlexGridSizer(4, 2, 5, 10)
        fgSizer2.SetFlexibleDirection(wx.BOTH)
        fgSizer2.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.m_staticText3 = wx.StaticText(sbSizer22.GetStaticBox(), wx.ID_ANY, 'Gridline &every:', wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText3.Wrap(-1)

        fgSizer2.Add(self.m_staticText3, 0, wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_textCtrl2 = wx.TextCtrl(sbSizer22.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        fgSizer2.Add(self.m_textCtrl2, 0, wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_staticText4 = wx.StaticText(sbSizer22.GetStaticBox(), wx.ID_ANY, 'Sub&divisions:', wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText4.Wrap(-1)

        fgSizer2.Add(self.m_staticText4, 0, wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_textCtrl3 = wx.TextCtrl(sbSizer22.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        fgSizer2.Add(self.m_textCtrl3, 0, wx.ALIGN_CENTER_VERTICAL, 5)


        sbSizer22.Add(fgSizer2, 1, wx.ALL|wx.EXPAND, 5)


        bSizer121.Add(sbSizer22, 0, wx.ALL|wx.EXPAND, 5)


        self.m_panel351.SetSizer(bSizer121)
        self.m_panel351.Layout()
        bSizer121.Fit(self.m_panel351)
        self.m_listbook7.AddPage(self.m_panel351, 'Visualizer', False)
        self.m_panel28 = wx.Panel(self.m_listbook7, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer111 = wx.BoxSizer(wx.VERTICAL)

        sbSizer131 = wx.StaticBoxSizer(wx.StaticBox(self.m_panel28, wx.ID_ANY, 'Keyboard Shortcuts'), wx.VERTICAL)


        bSizer111.Add(sbSizer131, 0, wx.ALL|wx.EXPAND, 5)


        self.m_panel28.SetSizer(bSizer111)
        self.m_panel28.Layout()
        bSizer111.Fit(self.m_panel28)
        self.m_listbook7.AddPage(self.m_panel28, 'Keyboard Shortcuts', True)

        bSizer2.Add(self.m_listbook7, 1, wx.ALL|wx.EXPAND, 5)

        m_sdbSizer5 = wx.StdDialogButtonSizer()
        self.m_sdbSizer5OK = wx.Button(self, wx.ID_OK)
        m_sdbSizer5.AddButton(self.m_sdbSizer5OK)
        self.m_sdbSizer5Cancel = wx.Button(self, wx.ID_CANCEL)
        m_sdbSizer5.AddButton(self.m_sdbSizer5Cancel)
        m_sdbSizer5.Realize();

        bSizer2.Add(m_sdbSizer5, 0, wx.ALL|wx.EXPAND, 5)


        self.SetSizer(bSizer2)
        self.Layout()

        self.Centre(wx.BOTH)

    def __del__(self):
        pass
