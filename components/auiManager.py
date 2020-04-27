import wx
import wx.lib.agw.aui as aui
from panels.controllerPanel import ControllerPanel
from panels.visualizerPanel import VisualizerPanel
from panels.cmdPanel import CommandPanel
from panels.evfPanel import EvfPanel

class AuiManager(aui.AuiManager):
    def __init__(self, managed_window=None):
        super(AuiManager, self).__init__(managed_window=managed_window)

        self.addControllerPane()
        self.addVisualizerPane()
        self.addCommandPane()

        #self._mgr.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.onPaneClose)
        self.Update()


    def addControllerPane(self):
        control_panel = ControllerPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name("Controller").Left().MinSize(wx.Size(600, 500)).Resizable(True).Layer(1)
        self.AddPane(control_panel, pane_info)

    def addVisualizerPane(self):
        visual_panel = VisualizerPanel(self.GetManagedWindow())
        pane_info =  aui.AuiPaneInfo().Name("Visualizer").Centre().MinSize(wx.Size(400, 500)).Resizable(True).MaximizeButton(True).Layer(0)
        self.AddPane(visual_panel, pane_info)

    def addCommandPane(self):
        command_panel = CommandPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name("Command").Bottom().MinSize(wx.Size(300, 200)).Resizable(True).Layer(1)
        self.AddPane(command_panel, pane_info)

    def addEvfPane(self):
        evf_panel = EvfPanel(self.GetManagedWindow())
        pane_info = aui.AuiPaneInfo().Name("Evf").Right().MinSize(wx.Size(600, 420)).DestroyOnClose(True).Layer(1)
        self.AddPane(evf_panel, pane_info)
        self.Update()
        
    def onPaneClose(self):
        pass

    def calcualteBestPaneSize(self):
        pass

