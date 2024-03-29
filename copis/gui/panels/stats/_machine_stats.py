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

"""COPIS machine section of stats panel."""

import threading
import time

from collections import defaultdict
from pydispatch import dispatcher

import wx

from copis.gui.wxutils import simple_statictext


class MachineStats(wx.Panel):
    """Show info related to the machine, in the stats panel."""

    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_DEFAULT)

        self._parent = parent
        self._core = parent.core
        self._keep_polling = True
        self._num_devices = len(self._core.project.devices)
        self._last_machine_status = None
        self._last_machine_homed_status = None

        self._build_panel()

        self._polling_thread = threading.Thread(
            target=self._poll_machine_stats,
            name='machine status polling thread',
            daemon=True)

        self._polling_thread.start()

        # Bind listeners.
        dispatcher.connect(self.on_device_updated, signal='ntf_device_ser_updated')
        dispatcher.connect(self.on_device_updated, signal='ntf_device_eds_updated')
        dispatcher.connect(self._on_device_list_changed, signal='ntf_d_list_changed')

    def _build_panel(self):
        text_ctrl = lambda s=wx.ALIGN_RIGHT|wx.TEXT_ALIGNMENT_RIGHT, f=None: simple_statictext(
            self, label='',
            style=s,
            font=f)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self._box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Machine Stats'),
            wx.VERTICAL)

        machine_grid = wx.FlexGridSizer(3, 2, 0, 0)
        machine_grid.AddGrowableCol(1, 0)

        device_grid = wx.FlexGridSizer(self._num_devices + 1, 7, 0, 0)

        self._device_count_caption = text_ctrl(f=self._parent.font)
        self._machine_status_caption = text_ctrl(f=self._parent.font)
        self._machine_is_homed_caption = text_ctrl(f=self._parent.font)

        machine_grid.AddMany([
            (simple_statictext(self, 'Status:', 80, font=self._parent.font), 0, wx.EXPAND, 0),
            (self._machine_status_caption, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Is Homed:', 80, font=self._parent.font), 0, wx.EXPAND, 0),
            (self._machine_is_homed_caption, 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Device Count:', 80,
             font=self._parent.font), 0, wx.EXPAND, 0),
            (self._device_count_caption, 0, wx.EXPAND, 0),
        ])

        self._dvc_captions = defaultdict(dict)

        device_grid.AddMany([
            (0, 0),
            (simple_statictext(self, 'X', 40, style=wx.ALIGN_RIGHT,
             font=self._parent.font), 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Y', 40, style=wx.ALIGN_RIGHT,
             font=self._parent.font), 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Z', 40, style=wx.ALIGN_RIGHT,
             font=self._parent.font), 0, wx.EXPAND, 0),
            (simple_statictext(self, 'P', 40, style=wx.ALIGN_RIGHT,
             font=self._parent.font), 0, wx.EXPAND, 0),
            (simple_statictext(self, 'T', 40, style=wx.ALIGN_RIGHT,
             font=self._parent.font), 0, wx.EXPAND, 0),
            (simple_statictext(self, 'Status', 50, style=wx.ALIGN_RIGHT,
             font=self._parent.font), 0, wx.EXPAND, 0)
        ])

        for dvc in self._core.project.devices:
            self._dvc_captions[dvc.device_id]['name'] = text_ctrl(
                wx.ALIGN_LEFT|wx.TEXT_ALIGNMENT_LEFT|wx.ST_ELLIPSIZE_END, self._parent.font)
            self._dvc_captions[dvc.device_id]['x'] = text_ctrl(f=self._parent.font)
            self._dvc_captions[dvc.device_id]['y'] = text_ctrl(f=self._parent.font)
            self._dvc_captions[dvc.device_id]['z'] = text_ctrl(f=self._parent.font)
            self._dvc_captions[dvc.device_id]['p'] = text_ctrl(f=self._parent.font)
            self._dvc_captions[dvc.device_id]['t'] = text_ctrl(f=self._parent.font)
            self._dvc_captions[dvc.device_id]['status'] = text_ctrl(
                f=self._parent.font)

            for key in self._dvc_captions[dvc.device_id]:
                device_grid.Add(self._dvc_captions[dvc.device_id][key], 0, wx.EXPAND, 0)

            self._update_device(dvc)

        self._box_sizer.Add(machine_grid, 0,
            wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        self._box_sizer.AddSpacer(5)
        self._box_sizer.Add(wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 0)
        self._box_sizer.AddSpacer(5)
        self._box_sizer.Add(device_grid, 0,
            wx.EXPAND|wx.LEFT|wx.RIGHT, 5)

        self.Sizer.Add(self._box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.Layout()

    def _on_device_list_changed(self):
        self._num_devices = len(self._core.project.devices)
        self._device_count_caption.SetLabel(str(self._num_devices))
        self._keep_polling = False
        self._polling_thread.join()

        self.DestroyChildren()
        self._build_panel()

        self._keep_polling = True

        self._polling_thread = threading.Thread(
            target=self._poll_machine_stats,
            name='machine status polling thread',
            daemon=True)

        self._polling_thread.start()

    def _poll_machine_stats(self):
        wx.CallAfter(self._device_count_caption.SetLabel, str(self._num_devices))

        while self._keep_polling:
            if self._device_count_caption:
                status = self._core.machine_status
                homed = str(self._core.is_machine_homed).lower()

                if self._last_machine_homed_status != homed:
                    self._last_machine_homed_status = homed
                    wx.CallAfter(self._machine_is_homed_caption.SetLabel, str(self._core.is_machine_homed).lower())

                if self._last_machine_status != status:
                    self._last_machine_status = status
                    wx.CallAfter(self._machine_status_caption.SetLabel, status)

            time.sleep(self._core.YIELD_TIMEOUT)

    def _update_device(self, device):
        format_num = lambda n: f'{n:.3f}'

        name = f'{device.name} {device.type} ({device.device_id})'
        name = name.title()
        status = device.status.name.lower()

        if device.serial_response:
            x, y, z, p, t = [format_num(c) for c in device.serial_response.position]
        else:
            x, y, z, p, t = ['?'] * 5

        self._dvc_captions[device.device_id]['name'].SetLabel(name)
        self._dvc_captions[device.device_id]['name'].SetMaxSize((90, -1))
        self._dvc_captions[device.device_id]['name'].SetToolTip(
            wx.ToolTip(name))

        self._dvc_captions[device.device_id]['x'].SetLabel(x)
        self._dvc_captions[device.device_id]['y'].SetLabel(y)
        self._dvc_captions[device.device_id]['z'].SetLabel(z)
        self._dvc_captions[device.device_id]['p'].SetLabel(p)
        self._dvc_captions[device.device_id]['t'].SetLabel(t)

        self._dvc_captions[device.device_id]['status'].SetLabel(status)
        self._dvc_captions[device.device_id]['status'].SetToolTip(
            wx.ToolTip(status))

    def on_device_updated(self, device):
        """Handles device updated event."""
        # Call the specified function after the current and pending event handlers have been completed.
        # This is good for making GUI method calls from non-GUI threads, in order to prevent hangs.
        wx.CallAfter(self._update_device, device)