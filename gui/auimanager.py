#!/usr/bin/env python3

import wx
import wx.lib.agw.aui as aui

from gui.panels.controller import ControllerPanel
from gui.panels.visualizer import VisualizerPanel
from gui.panels.cmd import CommandPanel
from gui.panels.evf import EvfPanel
from gui.panels.console import ConsolePanel
from gui.panels.toolbar import ToolBarPanel


# Reference
# https://wxpython.org/Phoenix/docs/html/wx.lib.agw.aui.framemanager.AuiManager.html?highlight=auimanager#wx.lib.agw.aui.framemanager.AuiManager
# https://wxpython.org/Phoenix/docs/html/wx.lib.agw.aui.framemanager.AuiPaneInfo.html

class AuiManager(aui.AuiManager):
    def __init__(self, managed_window=None):
        # giving control of managing the window to AuiManager
        # AuiManager follows the rules specified in AuiPaneInfo for each pane
        super(AuiManager, self).__init__(managed_window=managed_window)

        self.add_visualizer_panel()
        self.add_console_panel()
        self.add_command_panel()
        self.add_toolbar_pane()
        self.add_controller_panel()

        self.Bind(aui.EVT_AUI_PANE_CLOSE, self.on_pane_close)
        self.Update()

    def add_visualizer_panel(self):
        visual_panel = VisualizerPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name('Visualizer').Caption('Visualizer').MinSize(300, 400).MaximizeButton(True).Resizable(True).Center().Layer(0).Position(0)
        self.AddPane(visual_panel, pane_info)

    def add_console_panel(self):
        console_panel = ConsolePanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name('Console').Caption('Console').MinSize(200, 185).Resizable(True).Bottom().Layer(0).Position(0)
        # pane_info = aui.AuiPaneInfo().Name('Console').Caption('Console').Resizable(True).Bottom().Layer(0).Position(0)
        self.AddPane(console_panel, pane_info)

    def add_command_panel(self):
        command_panel = CommandPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name('Command').Caption('Command').MinSize(200, 185).Resizable(True).Bottom().Layer(0).Position(0)
        # pane_info = aui.AuiPaneInfo().Name('Command').Caption('Command').Resizable(True).Bottom().Layer(0).Position(0)
        self.AddPane(command_panel, pane_info)

    def add_toolbar_pane(self):
        toolbar_panel = ToolBarPanel(self.GetManagedWindow())
        # pane_info = aui.AuiPaneInfo().Name('ToolBar').Caption('ToolBar').CaptionVisible(False).Movable(False).Floatable(False).DestroyOnClose(False).Top().Layer(1).Position(0)
        pane_info = aui.AuiPaneInfo().Name('ToolBar').Caption('ToolBar').ToolbarPane().DestroyOnClose(False).Top().Layer(1).Position(0)
        self.AddPane(toolbar_panel, pane_info)

    def add_controller_panel(self):
        control_panel = ControllerPanel(self.GetManagedWindow(), self)
        pane_info = aui.AuiPaneInfo().Name('Controller').Caption('Controller').MinSize(360, 420).Resizable(True).Left().Layer(1).Position(0)
        self.AddPane(control_panel, pane_info)

    def add_evf_pane(self):
        evf_panel = EvfPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name('Evf').Caption('Live View').MinSize(600, 420).DestroyOnClose(True).MaximizeButton(True).Right().Layer(0).Position(1)
        self.AddPane(evf_panel, pane_info)
        self.Update()

    def on_pane_close(self, event):
        pane = event.GetPane()
        if pane.name == 'Evf':
            pane.window.timer.Stop()
            pane.window.on_destroy()
            self.DetachPane(pane.window)
            pane.window.Destroy()
