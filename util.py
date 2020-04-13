import wx

def set_dialog(msg):
    dialog = wx.MessageDialog(None, msg, "Confirm Exit", wx.OK)
    dialog.ShowModal()
    dialog.Destroy()