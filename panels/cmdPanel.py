import wx


class CommandPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(CommandPanel, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        hboxBottom = wx.BoxSizer()
        vboxCmd = wx.BoxSizer(wx.VERTICAL)
        self.cmd = wx.ListBox(self, style=wx.LB_SINGLE)
        vboxCmd.Add(self.cmd, 1, wx.EXPAND)

        hboxAddCmd = wx.BoxSizer()
        self.cmdWriter = wx.TextCtrl(self)
        hboxAddCmd.Add(self.cmdWriter, 1, wx.EXPAND)
        self.addBtn = wx.Button(self, wx.ID_ANY, label='Add')
        self.addBtn.Bind(wx.EVT_BUTTON, self.OnAddCommand)
        hboxAddCmd.Add(self.addBtn)
        vboxCmd.Add(hboxAddCmd, 0.5, wx.EXPAND)
        hboxBottom.Add(vboxCmd, 2, wx.EXPAND)

        vboxBtns = wx.BoxSizer(wx.VERTICAL)
        self.upBtn = wx.Button(self, wx.ID_ANY, label='Up')
        self.upBtn.direction = 'up'
        self.upBtn.Bind(wx.EVT_BUTTON, self.OnMoveCommand)
        vboxBtns.Add(self.upBtn)
        self.downBtn = wx.Button(self, wx.ID_ANY, label='Down')
        self.downBtn.direction = 'down'
        self.downBtn.Bind(wx.EVT_BUTTON, self.OnMoveCommand)
        vboxBtns.Add(self.downBtn)
        self.replaceBtn = wx.Button(self, wx.ID_ANY, label='Replace')
        self.replaceBtn.Bind(wx.EVT_BUTTON, self.OnReplaceCommand)
        vboxBtns.Add(self.replaceBtn)
        self.deleteBtn = wx.Button(self, wx.ID_ANY, label='Delete')
        self.deleteBtn.size = 'single'
        self.deleteBtn.Bind(wx.EVT_BUTTON, self.OnDeleteCommand)
        vboxBtns.Add(self.deleteBtn)
        self.deleteAllBtn = wx.Button(self, wx.ID_ANY, label='Delete All')
        self.deleteAllBtn.size = 'all'
        self.deleteAllBtn.Bind(wx.EVT_BUTTON, self.OnDeleteCommand)
        vboxBtns.Add(self.deleteAllBtn)
        self.saveToFileBtn = wx.Button(self, wx.ID_ANY, label='Save To File')
        vboxBtns.Add(self.saveToFileBtn)
        self.sendAllBtn = wx.Button(self, wx.ID_ANY, label='Send All')
        vboxBtns.Add(self.sendAllBtn)
        self.sendSelBtn = wx.Button(self, wx.ID_ANY, label='Send Sel')
        vboxBtns.Add(self.sendSelBtn)
        hboxBottom.Add(vboxBtns)

        self.SetSizer(hboxBottom)
        self.Layout()

    def OnAddCommand(self, event):
        cmd = self.cmdWriter.GetValue()
        if cmd != "":
            self.cmd.Append(cmd)
            self.cmdWriter.SetValue("")

    def OnMoveCommand(self, event):
        selected = self.cmd.GetStringSelection()

        if selected != "":
            direction = event.GetEventObject().direction
            index = self.cmd.GetSelection()
            self.cmd.Delete(index)

            if direction == "up":
                index -= 1
            else:
                index += 1

            self.cmd.InsertItems([selected], index)

    def OnReplaceCommand(self, event):
        selected = self.cmd.GetSelection()

        if selected != -1:
            replacement = self.cmdWriter.GetValue()

            if replacement != "":
                self.cmd.SetString(selected, replacement)
                self.cmdWriter.SetValue("")
            else:
                util.set_dialog("Please type command to replace.")
        else:
            util.set_dialog("Please select the command to replace.")

    def OnDeleteCommand(self, event):
        size = event.GetEventObject().size
        if size == "single":
            index = self.cmd.GetSelection()
            if index != -1:
                self.cmd.Delete(index)
            else:
                util.set_dialog("Please select the command to delete.")
        else:
            self.cmd.Clear()


