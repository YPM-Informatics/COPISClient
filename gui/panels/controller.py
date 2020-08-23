"""TODO"""


from collections import OrderedDict
from typing import Tuple

import wx

from utils import create_scaled_bitmap


class ControllerPanel(wx.Panel):
    """TODO

    """

    xyz_unit_steps = [10, 1, 0.1, 0.01]
    xyz_units = OrderedDict([('mm', 1), ('cm', 10), ('in', 25.4)])
    ab_unit_steps = [10, 5, 1, 0.1, 0.01]
    ab_units = OrderedDict([('deg', 10000), ('rad', 100000)]) # TODO!

    def __init__(self, parent, *args, **kwargs) -> None:
        """Inits ControllerPanel with constructors."""
        super().__init__(parent, style=wx.BORDER_DEFAULT)

        self.parent = parent
        self.init_gui()

    def init_gui(self) -> None:
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        info_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Controller State'), wx.VERTICAL)
        info_grid = wx.FlexGridSizer(6, 7, 0, 0)
        info_grid.SetFlexibleDirection(wx.BOTH)
        info_grid.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        for col in (2, 5):
            info_grid.AddGrowableCol(col)

        x_text = wx.StaticText(self, label='X')
        y_text = wx.StaticText(self, label='Y')
        z_text = wx.StaticText(self, label='Z')
        a_text = wx.StaticText(self, label='A')
        b_text = wx.StaticText(self, label='B')
        for text in (x_text, y_text, z_text, a_text, b_text):
            text.Font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        # axis_text = wx.StaticText(self, label='Axis')
        mpos_text = wx.StaticText(self, label='Machine')
        wpos_text = wx.StaticText(self, label='World')
        mzero_text = wx.StaticText(self, label='Zero')
        wzero_text = wx.StaticText(self, label='Zero')
        for text in (mpos_text, wpos_text, mzero_text, wzero_text):
            text.Font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.x_m_text = wx.TextCtrl(self, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.y_m_text = wx.TextCtrl(self, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.z_m_text = wx.TextCtrl(self, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.a_m_text = wx.TextCtrl(self, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.b_m_text = wx.TextCtrl(self, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.x_w_text = wx.TextCtrl(self, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.y_w_text = wx.TextCtrl(self, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.z_w_text = wx.TextCtrl(self, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.a_w_text = wx.TextCtrl(self, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        self.b_w_text = wx.TextCtrl(self, value='0.000', size=(50, 24), style=wx.TE_READONLY)
        for text in (self.x_m_text, self.y_m_text, self.z_m_text, self.a_m_text, self.b_m_text,
                     self.x_w_text, self.y_w_text, self.z_w_text, self.a_w_text, self.b_w_text):
            text.Font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.x0_m_btn = wx.Button(self, label='X0', size=(30, -1))
        self.y0_m_btn = wx.Button(self, label='Y0', size=(30, -1))
        self.z0_m_btn = wx.Button(self, label='Z0', size=(30, -1))
        self.a0_m_btn = wx.Button(self, label='A0', size=(30, -1))
        self.b0_m_btn = wx.Button(self, label='B0', size=(30, -1))
        self.x0_w_btn = wx.Button(self, label='X0', size=(30, -1))
        self.y0_w_btn = wx.Button(self, label='Y0', size=(30, -1))
        self.z0_w_btn = wx.Button(self, label='Z0', size=(30, -1))
        self.a0_w_btn = wx.Button(self, label='A0', size=(30, -1))
        self.b0_w_btn = wx.Button(self, label='B0', size=(30, -1))
        for btn in (self.x0_m_btn, self.y0_m_btn, self.z0_m_btn, self.a0_m_btn, self.b0_m_btn,
                    self.x0_w_btn, self.y0_w_btn, self.z0_w_btn, self.a0_w_btn, self.b0_w_btn):
            btn.Font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        info_grid.AddMany([
            (0, 0),
            (10, 0),
            (mpos_text, 0, 0, 0),
            (mzero_text, 0, 0, 0),
            (10, 0),
            (wpos_text, 0, 0, 0),
            (wzero_text, 0, 0, 0),

            (x_text, 0, 0, 0),
            (0, 0),
            (self.x_m_text, 0, wx.ALL|wx.EXPAND, 1),
            (self.x0_m_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.x_w_text, 0, wx.ALL|wx.EXPAND, 1),
            (self.x0_w_btn, 0, wx.EXPAND, 0),

            (y_text, 0, 0, 0),
            (0, 0),
            (self.y_m_text, 0, wx.ALL|wx.EXPAND, 1),
            (self.y0_m_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.y_w_text, 0, wx.ALL|wx.EXPAND, 1),
            (self.y0_w_btn, 0, wx.EXPAND, 0),

            (z_text, 0, 0, 0),
            (0, 0),
            (self.z_m_text, 0, wx.ALL|wx.EXPAND, 1),
            (self.z0_m_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.z_w_text, 0, wx.ALL|wx.EXPAND, 1),
            (self.z0_w_btn, 0, wx.EXPAND, 0),

            (a_text, 0, 0, 0),
            (0, 0),
            (self.a_m_text, 0, wx.ALL|wx.EXPAND, 1),
            (self.a0_m_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.a_w_text, 0, wx.ALL|wx.EXPAND, 1),
            (self.a0_w_btn, 0, wx.EXPAND, 0),

            (b_text, 0, 0, 0),
            (0, 0),
            (self.b_m_text, 0, wx.ALL|wx.EXPAND, 1),
            (self.b0_m_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (self.b_w_text, 0, wx.ALL|wx.EXPAND, 1),
            (self.b0_w_btn, 0, wx.EXPAND, 0),
        ])

        info_sizer.Add(info_grid, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(info_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # ---

        xyzab_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Jog Controller'), wx.VERTICAL)

        xyzab_grid = wx.FlexGridSizer(6, 6, 0, 0)
        xyzab_grid.SetFlexibleDirection(wx.BOTH)
        xyzab_grid.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        for col in (0, 1, 2, 3):
            xyzab_grid.AddGrowableCol(col)

        self.arrow_nw_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('arrow_nw', 20), size=(30, 30))
        self.arrow_ne_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('arrow_ne', 20), size=(30, 30))
        self.arrow_sw_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('arrow_sw', 20), size=(30, 30))
        self.arrow_se_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('arrow_se', 20), size=(30, 30))

        self.x_pos_btn = wx.Button(self, label='X+', size=(30, 30))
        self.x_neg_btn = wx.Button(self, label='X-', size=(30, 30))
        self.y_pos_btn = wx.Button(self, label='Y+', size=(30, 30))
        self.y_neg_btn = wx.Button(self, label='Y-', size=(30, 30))
        self.xy_btn = wx.BitmapButton(self, bitmap=create_scaled_bitmap('keyboard', 24), size=(30, 30))
        self.z_pos_btn = wx.Button(self, label='Z+', size=(30, 30))
        self.z_neg_btn = wx.Button(self, label='Z-', size=(30, 30))

        self.tilt_up_btn = wx.Button(self, label='A+', size=(48, 30))
        self.tilt_down_btn = wx.Button(self, label='A-', size=(48, 30))
        tilt_up_90_btn = wx.Button(self, label='A+90', size=(48, 30))
        tilt_down_90_btn = wx.Button(self, label='A-90', size=(48, 30))
        self.pan_right_btn = wx.Button(self, label='B+', size=(48, 30))
        self.pan_left_btn = wx.Button(self, label='B-', size=(48, 30))
        pan_right_90_btn = wx.Button(self, label='B+90', size=(48, 30))
        pan_left_90_btn = wx.Button(self, label='B-90', size=(48, 30))

        for btn in (self.x_pos_btn, self.x_neg_btn, self.y_pos_btn, self.y_neg_btn, self.z_pos_btn, self.z_neg_btn,
                    self.tilt_up_btn, self.pan_left_btn, self.tilt_down_btn, self.pan_right_btn,
                    tilt_up_90_btn, tilt_down_90_btn, pan_right_90_btn, pan_left_90_btn):
            btn.Font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        step_text = wx.StaticText(self, label='Step size', style=wx.ALIGN_CENTRE_HORIZONTAL)
        step_text.Font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        xyz_step = wx.ComboBox(self, value='1', size=(50, -1), choices=list(map(str, self.xyz_unit_steps)), style=wx.TE_CENTRE)
        xyz_unit = wx.Choice(self, size=(60, -1), choices=list(self.xyz_units.keys()), style=wx.TE_CENTRE)
        xyz_unit.SetSelection(0)
        ab_step = wx.ComboBox(self, value='1', size=(50, -1), choices=list(map(str, self.ab_unit_steps)), style=wx.TE_CENTRE)
        ab_unit = wx.Choice(self, size=(60, -1), choices=list(self.ab_units.keys()), style=wx.TE_CENTRE)
        ab_unit.SetSelection(0)

        for control in (xyz_step, xyz_unit, ab_step, ab_unit):
            control.Font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        xyzab_grid.AddMany([
            (self.arrow_nw_btn, 0, wx.EXPAND, 0),
            (self.y_pos_btn, 0, wx.EXPAND, 0),
            (self.arrow_ne_btn, 0, wx.EXPAND, 0),
            (self.z_pos_btn, 0, wx.EXPAND, 0),
            (10, 0),
            (step_text, 0, wx.ALIGN_BOTTOM|wx.BOTTOM|wx.EXPAND, 5),

            (self.x_neg_btn, 0, wx.EXPAND, 0),
            (self.xy_btn, 0, wx.EXPAND, 0),
            (self.x_pos_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (0, 0),
            (xyz_step, 0, wx.ALL|wx.EXPAND, 1),

            (self.arrow_sw_btn, 0, wx.EXPAND, 0),
            (self.y_neg_btn, 0, wx.EXPAND, 0),
            (self.arrow_se_btn, 0, wx.EXPAND, 0),
            (self.z_neg_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (xyz_unit, 0, wx.ALL|wx.EXPAND, 1),

            (0, 5), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0),

            (self.pan_left_btn, 0, wx.EXPAND, 0),
            (self.pan_right_btn, 0, wx.EXPAND, 0),
            (self.tilt_up_btn, 0, wx.EXPAND, 0),
            (tilt_up_90_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (ab_step, 0, wx.ALL|wx.EXPAND, 1),

            (pan_left_90_btn, 0, wx.EXPAND, 0),
            (pan_right_90_btn, 0, wx.EXPAND, 0),
            (self.tilt_down_btn, 0, wx.EXPAND, 0),
            (tilt_down_90_btn, 0, wx.EXPAND, 0),
            (0, 0),
            (ab_unit, 0, wx.ALL|wx.EXPAND, 1),
        ])

        xyzab_sizer.Add(xyzab_grid, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(xyzab_sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(main_sizer)
        self.Layout()

    def update_machine_pos(self, pos: Tuple[float, float, float, float, float]) -> None:
        pass

    def update_world_pos(self, pos: Tuple[float, float, float, float, float]) -> None:
        pass
