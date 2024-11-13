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

"""COPIS Application GUI properties panel."""

import wx
import wx.lib.scrolledpanel as scrolled

from pydispatch import dispatcher

from copis.globals import ActionType

from ._default_panel import DefaultPanel
from ._transform_panel import TransformPanel
from ._payload_panel import PayloadPanel
from ._device_info_panel import DeviceInfoPanel
from ._device_actions_panel import DeviceActionsPanel
from ._proxy_info_panel import ProxyInfo
from copis.classes import object3d, OBJObject3D, AABoxObject3D, CylinderObject3D


class PropertiesPanel(scrolled.ScrolledPanel):
    """Properties panel. Shows settings and controls in the context of the
        current selection."""

    _CONFIG = {
        'Default': ['default'],
        'Pose': ['default', 'transform', 'payload'],
        'Device': ['default', 'device_info', 'live_transform', 'device_actions'],
        'Object': ['default', 'proxy_info', 'proxy_transform']
    }


    def __init__(self, parent) -> None:
        """Initialize PropertiesPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)

        self.parent = parent
        self.core = self.parent.core

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self._property_panels = {}

        self.build_panels()
        self.update_to_selected('Default')

        self.SetupScrolling(scroll_x=False)
        self.Layout()

        # Bind listeners.
        dispatcher.connect(self.on_device_selected, signal='ntf_d_selected')
        dispatcher.connect(self.on_pose_selected, signal='ntf_a_selected')
        dispatcher.connect(self.on_device_homed, signal='ntf_device_homed')
        dispatcher.connect(self.on_deselected, signal='ntf_a_deselected')
        dispatcher.connect(self.on_deselected, signal='ntf_d_deselected')
        dispatcher.connect(self.on_object_selected, signal='ntf_o_selected')
        dispatcher.connect(self.on_deselected, signal='ntf_o_deselected')

    def build_panels(self) -> None:
        """Initialize all property panels."""
        # self._property_panels['transform'] = _PropTransform(self)
        # self._property_panels['device_config'] = _PropDeviceConfig(self)
        # self._property_panels['quick_actions'] = _PropQuickActions(self)
        self._property_panels['default'] = DefaultPanel(self)
        self._property_panels['transform'] = TransformPanel(self)
        self._property_panels['device_info'] = DeviceInfoPanel(self)
        self._property_panels['live_transform'] = TransformPanel(self, True)
        self._property_panels['device_actions'] = DeviceActionsPanel(self)
        self._property_panels['payload'] = PayloadPanel(self)
        self._property_panels['proxy_info'] = ProxyInfo(self)
        self._property_panels['proxy_transform'] = TransformPanel(self, False, True)

        for _, panel in self._property_panels.items():
            self.Sizer.Add(panel, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 0)

    def update_to_selected(self, selected: str) -> None:
        """Update panels to reflect the given selection."""
        if selected not in self._CONFIG:
            return

        # Show/hide appropriate panels.
        for name, panel in self._property_panels.items():
            panel.Show(name in self._CONFIG[selected])

        self.Layout()
        w, h = self.Sizer.GetMinSize()
        self.SetVirtualSize((w, h))

    def on_pose_selected(self, pose_index: int) -> None:
        """On ntf_a_selected, set to pose view."""
        pose = self.core.project.poses[pose_index]
        if pose.position.atype in [ActionType.G0, ActionType.G1]:
            self._property_panels['transform'].set_pose(pose)
            self._property_panels['payload'].set_pose(pose)
            self.update_to_selected('Pose')
            self.parent.update_properties_panel_title('pose properties')

    def on_device_selected(self, device) -> None:
        """On ntf_d_selected, set to device view."""
        self._property_panels['live_transform'].set_device(device)
        self._property_panels['device_info'].set_device(device)
        self._property_panels['device_actions'].set_device(device)
        self.update_to_selected('Device')
        self.parent.update_properties_panel_title('device properties')

        if not device.is_homed:
            self._property_panels['live_transform'].Disable()

    def on_object_selected(self, object) -> None:
        """On ntf_o_selected, set to proxy object view."""
        self.current = 'Object'
        self._property_panels['proxy_info'].set_proxy(object)

        # transform acts differently depending on the proxy type for now only allowing box proxies to be transformed, 
        # eventually will implement functionality for all proxy types 
        if isinstance(object, AABoxObject3D): 
            self._property_panels['proxy_transform'].set_proxy(object)
        else:
            #TODO transform for cylinders and meshes
            pass 
        self.update_to_selected('Object')
        self.parent.update_properties_panel_title('proxy properties')


    def on_deselected(self) -> None:
        """On ntf_*_deselected, reset to default view."""
        self.update_to_selected('Default')
        self.parent.update_properties_panel_title('properties')

    def on_device_homed(self) -> None:
        """On ntf_device_homed, enable appropriate panels."""
        if self._property_panels['live_transform']:
            self._property_panels['live_transform'].Enable()
