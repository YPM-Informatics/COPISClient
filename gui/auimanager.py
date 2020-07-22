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
        super().__init__(managed_window=managed_window, agwFlags=
            aui.AUI_MGR_ALLOW_FLOATING |
            aui.AUI_MGR_ALLOW_ACTIVE_PANE |
            aui.AUI_MGR_TRANSPARENT_DRAG |
            aui.AUI_MGR_TRANSPARENT_HINT |
            aui.AUI_MGR_HINT_FADE |
            aui.AUI_MGR_LIVE_RESIZE)

        self.init_dockart()

        self.add_visualizer_panel()
        self.add_console_panel()
        self.add_command_panel()
        self.add_toolbar_panel()
        self.add_controller_panel()

        # self.Bind(aui.EVT_AUI_PANE_CLOSE, self.on_pane_close)
        self.Update()

    def init_dockart(self):
        dockart = aui.AuiDefaultDockArt()
        dockart.SetMetric(aui.AUI_DOCKART_SASH_SIZE, 2)
        dockart.SetMetric(aui.AUI_DOCKART_CAPTION_SIZE, 18)
        dockart.SetMetric(aui.AUI_DOCKART_PANE_BORDER_SIZE, 1)
        dockart.SetMetric(aui.AUI_DOCKART_PANE_BUTTON_SIZE, 16)
        dockart.SetColour(aui.AUI_DOCKART_ACTIVE_CAPTION_COLOUR, wx.Colour(100, 100, 100))
        dockart.SetColour(aui.AUI_DOCKART_INACTIVE_CAPTION_COLOUR, wx.Colour(210, 210, 210))
        dockart.SetColour(aui.AUI_DOCKART_BORDER_COLOUR, wx.Colour(140, 140, 140))
        dockart.SetMetric(aui.AUI_DOCKART_GRADIENT_TYPE, aui.AUI_GRADIENT_NONE)
        self.SetArtProvider(dockart)

    def add_visualizer_panel(self):
        visual_panel = VisualizerPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name('Visualizer').Caption('Visualizer').MinSize(200, 150).MaximizeButton(True).MinimizeButton(True).Center().Layer(0).Position(0)
        self.AddPane(visual_panel, pane_info)

    def add_console_panel(self):
        console_panel = ConsolePanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name('Console').Caption('Console').MinSize(200, 185).MinimizeButton(True).Bottom().Layer(0).Position(0)
        self.AddPane(console_panel, pane_info)

    def add_command_panel(self):
        command_panel = CommandPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name('Command').Caption('Command').MinSize(200, 185).MinimizeButton(True).Bottom().Layer(0).Position(0)
        self.AddPane(command_panel, pane_info)

    def add_toolbar_panel(self):
        toolbar_panel = ToolBarPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name('ToolBar').Caption('ToolBar').ToolbarPane().DockFixed(True).Gripper(False).PaneBorder(False).DestroyOnClose(False).Top()
        # pane_info = aui.AuiPaneInfo().Name('ToolBar').Caption('ToolBar').ToolbarPane().DestroyOnClose(False).Bottom()
        self.AddPane(toolbar_panel, pane_info)

    def add_controller_panel(self):
        control_panel = ControllerPanel(self.GetManagedWindow(), self)
        pane_info = aui.AuiPaneInfo().Name('Controller').Caption('Controller').MinSize(360, 420).MinimizeButton(True).Left().Layer(1).Position(0)
        self.AddPane(control_panel, pane_info)

    def add_evf_pane(self):
        evf_panel = EvfPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name('Evf').Caption('Live View').MinSize(600, 420).MinimizeButton(True).DestroyOnClose(True).MaximizeButton(True).Right().Layer(0).Position(1)
        self.AddPane(evf_panel, pane_info)
        self.Update()

    def on_pane_close(self, event):
        pane = event.GetPane()
        if pane.name == 'Evf':
            pane.window.timer.Stop()
            pane.window.on_destroy()
            self.DetachPane(pane.window)
            pane.window.Destroy()
