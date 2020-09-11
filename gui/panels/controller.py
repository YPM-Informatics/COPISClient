"""ControllerPanel class."""

import math
from collections import OrderedDict

import wx
import wx.lib.scrolledpanel as scrolled
from pydispatch import dispatcher

import utils
from gui.wxutils import create_scaled_bitmap
from utils import Point3, Point5


class ControllerPanel(scrolled.ScrolledPanel):
    """Controller panel. When camera selected, jogs movement.

    Args:
        parent: Pointer to a parent wx.Frame.
    """

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits ControllerPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)
        self.parent = parent

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.add_state_controls()
        self.add_jog_controls()

        self.SetupScrolling(scroll_x=False)

        # start disabled, as no devices will be selected
        self.Disable()
        self.Layout()

        # bind copiscore listeners
        dispatcher.connect(self.on_device_selected, signal='core_d_selected')
        dispatcher.connect(self.on_device_deselected, signal='core_d_deselected')

    def on_device_selected(self, device) -> None:
        """On core_d_selected, update and enable controls."""
        self.update_machine_pos(device.position)
        self.Enable()

    def on_device_deselected(self) -> None:
        """On core_d_deselected, clear and disable controls."""
        self.update_machine_pos(Point5())
        self.Disable()

    def add_state_controls(self) -> None:
        """Initialize controller state sizer and setup child elements."""
        info_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='State'), wx.VERTICAL)

        info_grid = wx.FlexGridSizer(6, 7, 0, 0)
        for col in (2, 5):
            info_grid.AddGrowableCol(col)

        x_text = wx.StaticText(info_sizer.StaticBox, label='X')
        y_text = wx.StaticText(info_sizer.StaticBox, label='Y')
        z_text = wx.StaticText(info_sizer.StaticBox, label='Z')
        p_text = wx.StaticText(info_sizer.StaticBox, label='P')
        t_text = wx.StaticText(info_sizer.StaticBox, label='T')
        for text in (x_text, y_text, z_text, p_text, t_text):
            text.Font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        mpos_text = wx.StaticText(info_sizer.StaticBox, label='Machine')
        wpos_text = wx.StaticText(info_sizer.StaticBox, label='Work')
        mzero_text = wx.StaticText(info_sizer.StaticBox, label='Zero')
        wzero_text = wx.StaticText(info_sizer.StaticBox, label='Zero')

        self.x_m_text = wx.TextCtrl(info_sizer.StaticBox, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.y_m_text = wx.TextCtrl(info_sizer.StaticBox, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.z_m_text = wx.TextCtrl(info_sizer.StaticBox, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.p_m_text = wx.TextCtrl(info_sizer.StaticBox, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.t_m_text = wx.TextCtrl(info_sizer.StaticBox, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.x_w_text = wx.TextCtrl(info_sizer.StaticBox, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.y_w_text = wx.TextCtrl(info_sizer.StaticBox, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.z_w_text = wx.TextCtrl(info_sizer.StaticBox, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.p_w_text = wx.TextCtrl(info_sizer.StaticBox, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.t_w_text = wx.TextCtrl(info_sizer.StaticBox, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        for text in (self.x_m_text, self.y_m_text, self.z_m_text, self.p_m_text, self.t_m_text,
                     self.x_w_text, self.y_w_text, self.z_w_text, self.p_w_text, self.t_w_text):
            text.Font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        x0_m_btn = wx.Button(info_sizer.StaticBox, label='X0', size=(30, -1))
        y0_m_btn = wx.Button(info_sizer.StaticBox, label='Y0', size=(30, -1))
        z0_m_btn = wx.Button(info_sizer.StaticBox, label='Z0', size=(30, -1))
        p0_m_btn = wx.Button(info_sizer.StaticBox, label='P0', size=(30, -1))
        t0_m_btn = wx.Button(info_sizer.StaticBox, label='T0', size=(30, -1))
        x0_w_btn = wx.Button(info_sizer.StaticBox, label='X0', size=(30, -1))
        y0_w_btn = wx.Button(info_sizer.StaticBox, label='Y0', size=(30, -1))
        z0_w_btn = wx.Button(info_sizer.StaticBox, label='Z0', size=(30, -1))
        p0_w_btn = wx.Button(info_sizer.StaticBox, label='P0', size=(30, -1))
        t0_w_btn = wx.Button(info_sizer.StaticBox, label='T0', size=(30, -1))
        for btn in (x0_m_btn, y0_m_btn, z0_m_btn, p0_m_btn, t0_m_btn,
                    x0_w_btn, y0_w_btn, z0_w_btn, p0_w_btn, t0_w_btn):
            btn.Font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        info_grid.AddMany([
            (0, 0),
            (8, 0),
            (mpos_text, 0, 0, 0),
            (mzero_text, 0, 0, 0),
            (8, 0),
            (wpos_text, 0, 0, 0),
            (wzero_text, 0, 0, 0),

            (x_text, 0, 0, 0),
            (0, 0),
            (self.x_m_text, 0, wx.ALL|wx.EXPAND, 1),
            (x0_m_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.x_w_text, 0, wx.ALL|wx.EXPAND, 1),
            (x0_w_btn, 0, wx.EXPAND, 0),

            (y_text, 0, 0, 0),
            (0, 0),
            (self.y_m_text, 0, wx.ALL|wx.EXPAND, 1),
            (y0_m_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.y_w_text, 0, wx.ALL|wx.EXPAND, 1),
            (y0_w_btn, 0, wx.EXPAND, 0),

            (z_text, 0, 0, 0),
            (0, 0),
            (self.z_m_text, 0, wx.ALL|wx.EXPAND, 1),
            (z0_m_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.z_w_text, 0, wx.ALL|wx.EXPAND, 1),
            (z0_w_btn, 0, wx.EXPAND, 0),

            (p_text, 0, 0, 0),
            (0, 0),
            (self.p_m_text, 0, wx.ALL|wx.EXPAND, 1),
            (p0_m_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.p_w_text, 0, wx.ALL|wx.EXPAND, 1),
            (p0_w_btn, 0, wx.EXPAND, 0),

            (t_text, 0, 0, 0),
            (0, 0),
            (self.t_m_text, 0, wx.ALL|wx.EXPAND, 1),
            (t0_m_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.t_w_text, 0, wx.ALL|wx.EXPAND, 1),
            (t0_w_btn, 0, wx.EXPAND, 0),
        ])

        info_sizer.Add(info_grid, 1, wx.ALL|wx.EXPAND, 4)
        self.Sizer.Add(info_sizer, 0, wx.ALL|wx.EXPAND, 7)

    def add_jog_controls(self) -> None:
        """Initialize jog controller sizer and setup child elements."""
        jog_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Jogging'), wx.VERTICAL)

        xyzab_grid = wx.FlexGridSizer(6, 6, 0, 0)
        for col in (0, 1, 2, 3):
            xyzab_grid.AddGrowableCol(col)

        arrow_nw_btn = wx.BitmapButton(jog_sizer.StaticBox, bitmap=create_scaled_bitmap('arrow_nw', 20), size=(24, 24))
        arrow_ne_btn = wx.BitmapButton(jog_sizer.StaticBox, bitmap=create_scaled_bitmap('arrow_ne', 20), size=(24, 24))
        arrow_sw_btn = wx.BitmapButton(jog_sizer.StaticBox, bitmap=create_scaled_bitmap('arrow_sw', 20), size=(24, 24))
        arrow_se_btn = wx.BitmapButton(jog_sizer.StaticBox, bitmap=create_scaled_bitmap('arrow_se', 20), size=(24, 24))

        x_pos_btn = wx.Button(jog_sizer.StaticBox, label='X+', size=(24, 24))
        x_neg_btn = wx.Button(jog_sizer.StaticBox, label='X-', size=(24, 24))
        y_pos_btn = wx.Button(jog_sizer.StaticBox, label='Y+', size=(24, 24))
        y_neg_btn = wx.Button(jog_sizer.StaticBox, label='Y-', size=(24, 24))
        xy_btn = wx.BitmapButton(jog_sizer.StaticBox, bitmap=create_scaled_bitmap('keyboard', 24), size=(24, 24))
        z_pos_btn = wx.Button(jog_sizer.StaticBox, label='Z+', size=(24, 24))
        z_neg_btn = wx.Button(jog_sizer.StaticBox, label='Z-', size=(24, 24))

        tilt_up_btn = wx.Button(jog_sizer.StaticBox, label='T+', size=(42, 24))
        tilt_down_btn = wx.Button(jog_sizer.StaticBox, label='T-', size=(42, 24))
        tilt_up_90_btn = wx.Button(jog_sizer.StaticBox, label='T+90', size=(42, 24))
        tilt_down_90_btn = wx.Button(jog_sizer.StaticBox, label='T-90', size=(42, 24))
        pan_right_btn = wx.Button(jog_sizer.StaticBox, label='P+', size=(42, 24))
        pan_left_btn = wx.Button(jog_sizer.StaticBox, label='P-', size=(42, 24))
        pan_right_90_btn = wx.Button(jog_sizer.StaticBox, label='P+90', size=(42, 24))
        pan_left_90_btn = wx.Button(jog_sizer.StaticBox, label='P-90', size=(42, 24))

        for btn in (x_pos_btn, x_neg_btn, y_pos_btn, y_neg_btn, z_pos_btn, z_neg_btn,
                    tilt_up_btn, pan_left_btn, tilt_down_btn, pan_right_btn,
                    tilt_up_90_btn, tilt_down_90_btn, pan_right_90_btn, pan_left_90_btn):
            btn.Font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        step_text = wx.StaticText(jog_sizer.StaticBox, label='Step sizes', style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.xyz_step_cb = wx.ComboBox(jog_sizer.StaticBox, value='1', size=(50, -1), choices=list(map(str, utils.xyz_steps)), style=wx.TE_CENTRE)
        self.xyz_unit_choice = wx.Choice(jog_sizer.StaticBox, size=(50, -1), choices=list(utils.xyz_units.keys()), style=wx.TE_CENTRE)
        self.xyz_unit_choice.Selection = 0
        self.pt_step_cb = wx.ComboBox(jog_sizer.StaticBox, value='1', size=(50, -1), choices=list(map(str, utils.pt_steps)), style=wx.TE_CENTRE)
        self.pt_unit_choice = wx.Choice(jog_sizer.StaticBox, size=(50, -1), choices=list(utils.pt_units.keys()), style=wx.TE_CENTRE)
        self.pt_unit_choice.Selection = 0

        xyzab_grid.AddMany([
            (arrow_nw_btn, 0, wx.EXPAND, 0),
            (y_pos_btn, 0, wx.EXPAND, 0),
            (arrow_ne_btn, 0, wx.EXPAND, 0),
            (z_pos_btn, 0, wx.EXPAND, 0),
            (8, 0),
            (step_text, 0, wx.ALIGN_BOTTOM|wx.BOTTOM|wx.EXPAND, 3),

            (x_neg_btn, 0, wx.EXPAND, 0),
            (xy_btn, 0, wx.EXPAND, 0),
            (x_pos_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (0, 0),
            (self.xyz_step_cb, 0, wx.ALL|wx.EXPAND, 1),

            (arrow_sw_btn, 0, wx.EXPAND, 0),
            (y_neg_btn, 0, wx.EXPAND, 0),
            (arrow_se_btn, 0, wx.EXPAND, 0),
            (z_neg_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.xyz_unit_choice, 0, wx.ALL|wx.EXPAND, 1),

            (0, 5), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0),

            (pan_left_btn, 0, wx.EXPAND, 0),
            (pan_right_btn, 0, wx.EXPAND, 0),
            (tilt_up_btn, 0, wx.EXPAND, 0),
            (tilt_up_90_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.pt_step_cb, 0, wx.ALL|wx.EXPAND, 1),

            (pan_left_90_btn, 0, wx.EXPAND, 0),
            (pan_right_90_btn, 0, wx.EXPAND, 0),
            (tilt_down_btn, 0, wx.EXPAND, 0),
            (tilt_down_90_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.pt_unit_choice, 0, wx.ALL|wx.EXPAND, 1),
        ])

        jog_sizer.Add(xyzab_grid, 1, wx.ALL|wx.EXPAND, 4)
        self.Sizer.Add(jog_sizer, 0, wx.ALL|wx.EXPAND, 7)

    def update_machine_pos(self, pos: Point5) -> None:
        """Update machine position values given point."""
        self.x_m_text.ChangeValue(f'{pos.x:.3f}')
        self.y_m_text.ChangeValue(f'{pos.y:.3f}')
        self.z_m_text.ChangeValue(f'{pos.z:.3f}')
        self.p_m_text.ChangeValue(f'{pos.p:.3f}')
        self.t_m_text.ChangeValue(f'{pos.t:.3f}')

    def update_world_pos(self, pos: Point5) -> None:
        """Update world position values given point."""
        self.x_w_text.ChangeValue(f'{pos.x:.3f}')
        self.y_w_text.ChangeValue(f'{pos.y:.3f}')
        self.z_w_text.ChangeValue(f'{pos.z:.3f}')
        self.p_w_text.ChangeValue(f'{pos.p:.3f}')
        self.t_w_text.ChangeValue(f'{pos.t:.3f}')
