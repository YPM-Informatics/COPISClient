# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""COPIS machine info properties panel."""

import threading
import time
import wx

from collections import defaultdict

from copis.gui.wxutils import simple_statictext


class MachineInfo(wx.Panel):
    """Show information related to the machine, in the properties panel."""

    def __init__(self, parent):
        get_new_text_ctrl = lambda: wx.StaticText(self, label='',
            style=wx.ALIGN_RIGHT|wx.TEXT_ALIGNMENT_RIGHT)

        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self._parent = parent
        self._core = parent.core

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Machine Info'), wx.VERTICAL)

        machine_grid = wx.FlexGridSizer(3, 2, 0, 0)
        machine_grid.AddGrowableCol(1, 0)

        devices = parent.core.project.devices

        device_grid = wx.FlexGridSizer(10, len(devices) + 1, 0, 0)
        # device_grid.AddGrowableCol(0, 0)


        self._device_count_caption = get_new_text_ctrl()
        self._machine_status_caption = get_new_text_ctrl()
        self._machine_is_homed_caption = get_new_text_ctrl()

        machine_grid.AddMany([
            (simple_statictext(self, 'Status:', 80), 0, wx.EXPAND, 0),
            (self._machine_status_caption, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Is Idle:', 80), 0, wx.EXPAND, 0),
            (self._machine_is_homed_caption, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Device Count:', 80), 0, wx.EXPAND, 0),
            (self._device_count_caption, 0, wx.EXPAND, 0),
        ])

        self._dvc_captions = defaultdict(dict)

        device_grid.AddMany([
            (0, 0),
            (simple_statictext(self, 'X', 30, style=wx.ALIGN_RIGHT), 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y', 30, style=wx.ALIGN_RIGHT), 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Z', 30, style=wx.ALIGN_RIGHT), 0, wx.EXPAND, 0),
            (simple_statictext(self, 'P', 30, style=wx.ALIGN_RIGHT), 0, wx.EXPAND, 0),
            (simple_statictext(self, 'T', 30, style=wx.ALIGN_RIGHT), 0, wx.EXPAND, 0),
            (simple_statictext(self, 'S', 30, style=wx.ALIGN_RIGHT), 0, wx.EXPAND, 0)
        ])

        # for dvc in devices:
        #     self._dvc_captions[dvc.device_id]['name'] = get_new_text_ctrl()
        #     self._dvc_captions[dvc.device_id]['x'] = get_new_text_ctrl()
        #     self._dvc_captions[dvc.device_id]['y'] = get_new_text_ctrl()
        #     self._dvc_captions[dvc.device_id]['z'] = get_new_text_ctrl()
        #     self._dvc_captions[dvc.device_id]['p'] = get_new_text_ctrl()
        #     self._dvc_captions[dvc.device_id]['t'] = get_new_text_ctrl()
        #     self._dvc_captions[dvc.device_id]['status'] = get_new_text_ctrl()

        #     for key in self._dvc_captions[dvc.device_id]:
        #         device_grid.AddMany([
        #             (self._dvc_captions[dvc.device_id][key], 0, 0, 0),
        #         ])

        #     self._on_device_updated(dvc)

        box_sizer.Add(machine_grid, 0, wx.ALL|wx.EXPAND, 4)
        box_sizer.AddSpacer(5)
        box_sizer.Add(wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 0)
        box_sizer.AddSpacer(5)
        box_sizer.Add(device_grid, 0, wx.ALL|wx.EXPAND, 4)

        self.Sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 7)
        self.Layout()

        poll_thread = threading.Thread(
            target=self._poll_machine_stats,
            name='machine status polling thread',
            daemon=True)

        poll_thread.start()

    def _poll_machine_stats(self):
        while True:
            if self._device_count_caption:
                self._device_count_caption.SetLabel(str(len(
                    self._parent.core.project.devices
                )))
                self._machine_status_caption.SetLabel(self._core.machine_status)
                self._machine_is_homed_caption.SetLabel(str(self._core.is_machine_homed).lower())

            time.sleep(.5)

    def _on_device_updated(self, device):
        name = f'{device.name} {device.type} ({device.device_id})'
        name = name.title()
        status = device.serial_status.name.lower()

        x, y, z, p, t = device.position
        # if device.serial_response:
        #     x, y, z, p, t = device.serial_response.position
        # else:
        #     x, y, z, p, t = [''] * 5

        self._dvc_captions[device.device_id]['name'].SetLabel(name)
        self._dvc_captions[device.device_id]['x'].SetLabel(str(x))
        self._dvc_captions[device.device_id]['y'].SetLabel(str(y))
        self._dvc_captions[device.device_id]['z'].SetLabel(str(z))
        self._dvc_captions[device.device_id]['p'].SetLabel(str(p))
        self._dvc_captions[device.device_id]['t'].SetLabel(str(t))
        self._dvc_captions[device.device_id]['status'].SetLabel(status)
