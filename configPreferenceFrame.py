import wx
#from wx.lib.pubsub import Publisher


class ConfigPreferenceFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Secondary Frame")
        panel = wx.Panel(self)
    
        msg = "Enter a Message to send to the main frame"
        instructions = wx.StaticText(panel, label=msg)
        self.msgTxt = wx.TextCtrl(panel, value="")
        closeBtn = wx.Button(panel, label="Send and Close")
        closeBtn.Bind(wx.EVT_BUTTON, self.onSendAndClose)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        flags = wx.ALL|wx.CENTER
        sizer.Add(instructions, 0, flags, 5)
        sizer.Add(self.msgTxt, 0, flags, 5)
        sizer.Add(closeBtn, 0, flags, 5)
        panel.SetSizer(sizer)
        
    #----------------------------------------------------------------------
    def onSendAndClose(self, event):
        """
        Send a message and close frame
        """
        msg = self.msgTxt.GetValue()
        Publisher().sendMessage(("show.mainframe"), msg)
        self.Close()
