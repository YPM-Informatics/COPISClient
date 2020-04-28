import wx
#from wx.lib.pubsub import Publisher


class ConfigPreferenceFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Configuration Preferences")
    
       ## TO DO: design an interface