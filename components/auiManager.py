import wx
import wx.lib.agw.aui as aui
from panels.controllerPanel import ControllerPanel
from panels.visualizerPanel import VisualizerPanel
from panels.cmdPanel import CommandPanel
from panels.evfPanel import EvfPanel

# Reference
# https://wxpython.org/Phoenix/docs/html/wx.lib.agw.aui.framemanager.AuiManager.html?highlight=auimanager#wx.lib.agw.aui.framemanager.AuiManager
# https://wxpython.org/Phoenix/docs/html/wx.lib.agw.aui.framemanager.AuiPaneInfo.html

class AuiManager(aui.AuiManager):
    def __init__(self, managed_window=None):
        ## giving control of managing the window to AuiManager
        ## AuiManager follows the rules specified in AuiPaneInfo for each pane
        super(AuiManager, self).__init__(managed_window=managed_window)

        self.addVisualizerPane()
        self.addControllerPane()
        self.addCommandPane()

        self.Bind(aui.EVT_AUI_PANE_CLOSE, self.onPaneClose)
        self.Update()


    def addControllerPane(self):
        control_panel = ControllerPanel(self.GetManagedWindow(), self)
        pane_info = aui.AuiPaneInfo().Name("Controller").MinSize(wx.Size(600, 500)).Left().Resizable(True).Layer(1).Position(0)
        self.AddPane(control_panel, pane_info)

    def addVisualizerPane(self):
        visual_panel = VisualizerPanel(self.GetManagedWindow())
        pane_info =  aui.AuiPaneInfo().Name("Visualizer").MinSize(wx.Size(400, 500)).Center().Resizable(True).MaximizeButton(True).Layer(0).Position(0)
        self.AddPane(visual_panel, pane_info)

    def addCommandPane(self):
        command_panel = CommandPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name("Command").MinSize(wx.Size(300, 200)).Bottom().Resizable(True).Layer(2)
        self.AddPane(command_panel, pane_info)

    def addEvfPane(self):
        evf_panel = EvfPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name("Evf").Right().MinSize(wx.Size(600, 420)).DestroyOnClose(True).Layer(1).Position(1)
        self.AddPane(evf_panel, pane_info)
        self.Update()
        
    def onPaneClose(self, event):
        pane = event.GetPane()
        if pane.name == "Evf":
            pane.window.timer.Stop()
            pane.window.on_destroy()
            self.DetachPane(pane.window)
            pane.window.Destroy()

    def calcualteBestPaneSize(self):
        pass

