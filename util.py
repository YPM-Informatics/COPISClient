def set_dialog(msg):
    dialog = wx.MessageDialog(self, msg, "Confirm Exit", wx.OK)
    dialog.ShowModal()
    dialog.Destroy()