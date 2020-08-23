"""TODO"""

import wx

from utils import set_dialog


class TimelinePanel(wx.Panel):
    """

    TODO: Improve timeline panel
    """

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits TimelinePanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.init_gui()

    def init_gui(self) -> None:
        hboxBottom = wx.BoxSizer()
        vboxCmd = wx.BoxSizer(wx.VERTICAL)
        self.cmd = wx.ListBox(self, style=wx.LB_SINGLE)
        vboxCmd.Add(self.cmd, 1, wx.EXPAND)

        hboxAddCmd = wx.BoxSizer()
        self.cmdWriter = wx.TextCtrl(self)
        hboxAddCmd.Add(self.cmdWriter, 1, wx.EXPAND)
        self.addBtn = wx.Button(self, wx.ID_ANY, label='Add')
        self.addBtn.Bind(wx.EVT_BUTTON, self.on_add_command)
        hboxAddCmd.Add(self.addBtn)
        vboxCmd.Add(hboxAddCmd, 0.5, wx.EXPAND)
        hboxBottom.Add(vboxCmd, 2, wx.EXPAND)

        vboxBtns = wx.BoxSizer(wx.VERTICAL)
        self.up_btn = wx.Button(self, wx.ID_ANY, label='Up')
        self.up_btn.direction = 'up'
        self.up_btn.Bind(wx.EVT_BUTTON, self.on_move_command)
        vboxBtns.Add(self.up_btn)
        self.down_btn = wx.Button(self, wx.ID_ANY, label='Down')
        self.down_btn.direction = 'down'
        self.down_btn.Bind(wx.EVT_BUTTON, self.on_move_command)
        vboxBtns.Add(self.down_btn)
        self.replace_btn = wx.Button(self, wx.ID_ANY, label='Replace')
        self.replace_btn.Bind(wx.EVT_BUTTON, self.on_replace_command)
        vboxBtns.Add(self.replace_btn)
        self.delete_btn = wx.Button(self, wx.ID_ANY, label='Delete')
        self.delete_btn.size = 'single'
        self.delete_btn.Bind(wx.EVT_BUTTON, self.on_delete_command)
        vboxBtns.Add(self.delete_btn)
        self.delall_button = wx.Button(self, wx.ID_ANY, label='Delete All')
        self.delall_button.size = 'all'
        self.delall_button.Bind(wx.EVT_BUTTON, self.on_delete_command)
        vboxBtns.Add(self.delall_button)
        self.savetofile_btn = wx.Button(self, wx.ID_ANY, label='Save To File')
        vboxBtns.Add(self.savetofile_btn)
        self.sendall_btn = wx.Button(self, wx.ID_ANY, label='Send All')
        vboxBtns.Add(self.sendall_btn)
        self.sendsel_button = wx.Button(self, wx.ID_ANY, label='Send Sel')
        vboxBtns.Add(self.sendsel_button)
        hboxBottom.Add(vboxBtns)

        self.SetSizer(hboxBottom)
        self.Layout()

    def on_add_command(self, event) -> None:
        cmd = self.cmdWriter.Value
        if cmd != '':
            self.cmd.Append(cmd)
            self.cmdWriter.SetValue('')

    def on_move_command(self, event) -> None:
        selected = self.cmd.StringSelection

        if selected != '':
            direction = event.EventObject.direction
            index = self.cmd.Selection
            self.cmd.Delete(index)

            if direction == 'up':
                index -= 1
            else:
                index += 1

            self.cmd.InsertItems([selected], index)

    def on_replace_command(self, event) -> None:
        selected = self.cmd.Selection

        if selected != -1:
            replacement = self.cmdWriter.Value

            if replacement != '':
                self.cmd.SetString(selected, replacement)
                self.cmdWriter.SetValue('')
            else:
                set_dialog('Please type command to replace.')
        else:
            set_dialog('Please select the command to replace.')

    def on_delete_command(self, event) -> None:
        size = event.EventObject.size
        if size == 'single':
            index = self.cmd.Selection
            if index != -1:
                self.cmd.Delete(index)
            else:
                set_dialog('Please select the command to delete.')
        else:
            self.cmd.Clear()
