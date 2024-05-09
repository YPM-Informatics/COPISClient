

from json.encoder import py_encode_basestring_ascii
from pickle import FALSE
from glm import rotate
import wx
from copis.core import COPISCore
from copis.classes.action import Action
from copis.classes.pose import Pose
from copis.classes.device import Device
from copis.gui.wxutils import show_msg_dialog, simple_statictext, FancyTextCtrl, EVT_FANCY_TEXT_UPDATED_EVENT, create_scaled_bitmap
from copis.helpers import create_action_args, get_atype_kind, get_heading, is_number, print_debug_msg, rad_to_dd, sanitize_number, sanitize_point, xyz_units, pt_units, dd_to_rad, get_end_position, get_heading
from copis.pathutils import build_pose_sets

from copis.classes.object3d import AABoxObject3D 
from glm import vec3   
from pydispatch import dispatcher  

class SetEditorFrame(wx.Dialog):
    def __init__(self, parent, title, copis_core : COPISCore):
        super(SetEditorFrame, self).__init__(parent, title=title, size=(400, 640), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.core = copis_core
        self.panel = wx.Panel(self)
        self.selected_op = None
        self.deinterleaved = False
        self.deinterleave_algo = "By Device"
        self.ops = ["Deinterleave", "Change Device", "Delete", "Increment Position", "Forward/Back", "Retarget"] #"Change Payload"]
        self.device_choices = list(map(lambda x: f'{x.device_id} ({x.name})', self.core.project.devices))
        self.create_widgets()
        self.selected_pose_idxs = []
        dispatcher.connect(self._get_filtered_pose_indexes, signal='ntf_a_list_changed') 
        
    def create_widgets(self):
        liner_unit = 'mm'
        rotational_unit = 'dd'
        self.device_sel_box = wx.StaticBox(self.panel, id =wx.ID_ANY, pos=(20,10), size=(135,120))
        self.filter_device = wx.CheckBox(self.panel, label="Device", id =wx.ID_ANY, pos=(20,10)) 
        self.device_checklist = wx.CheckListBox(self.device_sel_box, size=(110, 80),pos=(15,15), choices=self.device_choices)
        self.device_sel_box.Enable(False)
        
        self.pose_range_sel_box = wx.StaticBox(self.panel, id =wx.ID_ANY, pos=(20,140), size=(160,75))
        self.filter_pose_range = wx.CheckBox(self.panel, label="Pose Range", id =wx.ID_ANY, pos=(20,140))
        wx.StaticText(self.pose_range_sel_box, label="Start Pose No.:", pos=(15,20))
        wx.StaticText(self.pose_range_sel_box, label="End Pose No.:", pos=(15,50))
        self.start_pose_ctrl = wx.TextCtrl(self.pose_range_sel_box, size=(48, 25), pos=(100, 15), value='0')     
        self.end_pose_ctrl = wx.TextCtrl(self.pose_range_sel_box, size=(48, 25), pos=(100, 45), value=(str(len(self.core.project.poses)-1)) )
        self.pose_range_sel_box.Enable(False)
        
        self.bb_sel_box = wx.StaticBox(self.panel, id =wx.ID_ANY, pos=(20,225), size=(172,315))
        self.filter_bb = wx.CheckBox(self.panel, label="Bounding Box", id =wx.ID_ANY, pos=(20,225))    
        wx.StaticText(self.bb_sel_box, label="Start X (mm):", pos=(15, 20))
        wx.StaticText(self.bb_sel_box, label="Start Y (mm):", pos=(15, 50))
        wx.StaticText(self.bb_sel_box, label="Start Z (mm):", pos=(15, 80))
        wx.StaticText(self.bb_sel_box, label="Start P (dd):", pos=(15, 110))
        wx.StaticText(self.bb_sel_box, label="Start T (dd):", pos=(15, 140))
        wx.StaticText(self.bb_sel_box, label="End X (mm):", pos=(15, 170))
        wx.StaticText(self.bb_sel_box, label="End Y (mm):", pos=(15, 200))
        wx.StaticText(self.bb_sel_box, label="End Z (mm):", pos=(15, 230))
        wx.StaticText(self.bb_sel_box, label="End P (dd):", pos=(15, 260))
        wx.StaticText(self.bb_sel_box, label="End T (dd):", pos=(15, 290))

        min_x = 0
        max_x = 0
        min_y = 0
        max_y = 0
        min_z = 0
        max_z = 0
        min_p = -360
        max_p = 360
        min_t = -360
        max_t = 360
        if len(self.core.project.poses) > 0:
            p0 = self.core.project.poses[0].position_as_point5
            min_x = p0.x
            max_x = p0.x
            min_y = p0.y
            max_y = p0.y
            min_z = p0.z
            max_z = p0.z
            min_p = p0.p
            max_p = p0.p
            min_t = p0.t
            max_t = p0.t
            for p in self.core.project.poses:
                p5 = p.position_as_point5
                min_x = min(min_x, p5.x)
                min_y = min(min_y, p5.y)
                min_z = min(min_z, p5.z)
                min_p = min(min_p, p5.p)
                min_t = min(min_t, p5.t)
                max_x = max(max_x, p5.x)
                max_y = max(max_y, p5.y)
                max_z = max(max_z, p5.z)
                max_p = max(max_p, p5.p)
                max_t = max(max_t, p5.t)
            min_p = rad_to_dd(min_p)
            max_p = rad_to_dd(max_p)
            min_t = rad_to_dd(min_t)
            max_t = rad_to_dd(max_t)      
        self.bb_start_x_ctrl = FancyTextCtrl(self.bb_sel_box, size=(60, 25), pos=(100, 15), num_value=min_x, default_unit=liner_unit, unit_conversions=xyz_units)
        self.bb_start_y_ctrl = FancyTextCtrl(self.bb_sel_box, size=(60, 25), pos=(100, 45), num_value=min_y, default_unit=liner_unit, unit_conversions=xyz_units)
        self.bb_start_z_ctrl = FancyTextCtrl(self.bb_sel_box, size=(60, 25), pos=(100, 75), num_value=min_z, default_unit=liner_unit, unit_conversions=xyz_units)
        self.bb_start_p_ctrl = FancyTextCtrl(self.bb_sel_box, size=(60, 25), pos=(100, 105), num_value=min_p, default_unit=rotational_unit, unit_conversions=pt_units)
        self.bb_start_t_ctrl = FancyTextCtrl(self.bb_sel_box, size=(60, 25), pos=(100, 135), num_value=min_t, default_unit=rotational_unit, unit_conversions=pt_units)
        self.bb_end_x_ctrl = FancyTextCtrl(self.bb_sel_box, size=(60, 25), pos=(100, 165), num_value=max_x, default_unit=liner_unit, unit_conversions=xyz_units)
        self.bb_end_y_ctrl = FancyTextCtrl(self.bb_sel_box, size=(60, 25), pos=(100, 195), num_value=max_y, default_unit=liner_unit, unit_conversions=xyz_units)
        self.bb_end_z_ctrl = FancyTextCtrl(self.bb_sel_box, size=(60, 25), pos=(100, 225), num_value=max_z, default_unit=liner_unit, unit_conversions=xyz_units)
        self.bb_end_p_ctrl = FancyTextCtrl(self.bb_sel_box, size=(60, 25), pos=(100, 255), num_value=max_p, default_unit=rotational_unit, unit_conversions=pt_units)
        self.bb_end_t_ctrl = FancyTextCtrl(self.bb_sel_box, size=(60, 25), pos=(100, 285), num_value=max_t, default_unit=rotational_unit, unit_conversions=pt_units)
        self.bb_sel_box.Enable(False)       

        self.op_box = wx.StaticBox(self.panel, id =wx.ID_ANY, label="Operation", pos=(200,10), size=(160,255))
        self.operations_ctrl = wx.Choice(self.op_box, id =wx.ID_ANY, choices=self.ops, pos=(15, 20))
        self.pose_count_label = wx.StaticText(self.op_box, label="0 pose(s) selected.", pos=(15, 50))
        self.op_dev_change_choice_ctrl = wx.Choice(self.op_box, id =wx.ID_ANY, choices=self.device_choices, pos=(15, 80))
        self.op_dev_change_choice_ctrl.SetSelection(0)
        self.op_dev_change_choice_ctrl.Hide()
        self.op_deinterleave_algo__choice_ctrl = wx.Choice(self.op_box, id =wx.ID_ANY, choices=["By Device", "By Order"], pos=(15, 80))
        self.op_deinterleave_algo__choice_ctrl.SetSelection(0)
        self.op_deinterleave_algo__choice_ctrl.Hide()
        
        self.op_dist = wx.StaticText(self.op_box, label="+/- dist (mm):", pos=(15, 80))
        self.op_dist.Hide()
        self.op_dist_ctrl = FancyTextCtrl(self.op_box, size=(48, 25), pos=(100, 75), num_value=0, default_unit=liner_unit, unit_conversions=xyz_units)
        self.op_dist_ctrl.Hide()
        
        self.op_retarget_x = wx.StaticText(self.op_box, label="X (mm):", pos=(15, 80))
        self.op_retarget_x.Hide()
        self.op_retarget_y = wx.StaticText(self.op_box, label="Y (mm):", pos=(15, 110))
        self.op_retarget_y.Hide()
        self.op_retarget_z = wx.StaticText(self.op_box, label="Z (mm):", pos=(15, 140))
        self.op_retarget_z.Hide()
        self.op_retarget_x_ctrl = FancyTextCtrl(self.op_box, size=(48, 25), pos=(100, 75), num_value=0, default_unit=liner_unit, unit_conversions=xyz_units)
        self.op_retarget_x_ctrl.Hide()
        self.op_retarget_y_ctrl = FancyTextCtrl(self.op_box, size=(48, 25), pos=(100, 105), num_value=0, default_unit=liner_unit, unit_conversions=xyz_units)
        self.op_retarget_y_ctrl.Hide()
        self.op_retarget_z_ctrl = FancyTextCtrl(self.op_box, size=(48, 25), pos=(100, 135), num_value=0, default_unit=liner_unit, unit_conversions=xyz_units)
        self.op_retarget_z_ctrl.Hide()
        
        self.op_x = wx.StaticText(self.op_box, label="+/- X (mm):", pos=(15, 80))
        self.op_x.Hide()
        self.op_y = wx.StaticText(self.op_box, label="+/- Y (mm):", pos=(15, 110))
        self.op_y.Hide()
        self.op_z = wx.StaticText(self.op_box, label="+/- Z (mm):", pos=(15, 140))
        self.op_z.Hide()
        self.op_p = wx.StaticText(self.op_box, label="+/- P (dd):", pos=(15, 170))
        self.op_p.Hide()
        self.op_t = wx.StaticText(self.op_box, label="+/- T (dd):", pos=(15, 200))
        self.op_t.Hide()
        self.op_x_ctrl = FancyTextCtrl(self.op_box, size=(48, 25), pos=(100, 75), num_value=0, default_unit=liner_unit, unit_conversions=xyz_units)
        self.op_x_ctrl.Hide()
        self.op_y_ctrl = FancyTextCtrl(self.op_box, size=(48, 25), pos=(100, 105), num_value=0, default_unit=liner_unit, unit_conversions=xyz_units)
        self.op_y_ctrl.Hide()
        self.op_z_ctrl = FancyTextCtrl(self.op_box, size=(48, 25), pos=(100, 135), num_value=0, default_unit=liner_unit, unit_conversions=xyz_units)
        self.op_z_ctrl.Hide()
        self.op_p_ctrl = FancyTextCtrl(self.op_box, size=(48, 25), pos=(100, 165), num_value=0, default_unit=rotational_unit, unit_conversions=pt_units)
        self.op_p_ctrl.Hide()
        self.op_t_ctrl = FancyTextCtrl(self.op_box, size=(48, 25), pos=(100, 195), num_value=0, default_unit=rotational_unit, unit_conversions=pt_units)
        self.op_t_ctrl.Hide()
        
        self.filter_device.Bind(wx.EVT_CHECKBOX, self._on_filter_device_checked)
        self.device_checklist.Bind(wx.EVT_CHECKLISTBOX, self._on_ctrl_update)
        
        self.filter_pose_range.Bind(wx.EVT_CHECKBOX, self._on_filter_pose_range_checked)
        self.start_pose_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)        
        self.end_pose_ctrl.Bind(wx.EVT_TEXT, self._on_ctrl_update)  
        
        self.filter_bb.Bind(wx.EVT_CHECKBOX, self._on_filter_bb_checked)
      
        self.bb_start_x_ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_ctrl_update)        
        self.bb_start_y_ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_ctrl_update)  
        self.bb_start_z_ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_ctrl_update)
        self.bb_start_p_ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_ctrl_update)
        self.bb_start_t_ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_ctrl_update)
        self.bb_end_x_ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_ctrl_update)        
        self.bb_end_y_ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_ctrl_update)  
        self.bb_end_z_ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_ctrl_update) 
        self.bb_end_p_ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_ctrl_update)
        self.bb_end_t_ctrl.Bind(EVT_FANCY_TEXT_UPDATED_EVENT, self._on_ctrl_update)
        
        self.operations_ctrl.Bind(wx.EVT_CHOICE, self._on_operation_selected)
        
        apply_btn = wx.Button(self.panel, label="Apply", pos=(120, 550))
        close_btn = wx.Button(self.panel, label="Close", pos=(220, 550))

        apply_btn.Bind(wx.EVT_BUTTON, self._on_apply)
        close_btn.Bind(wx.EVT_BUTTON, self._on_close)
    
    def _on_ctrl_update(self, event):
        self._get_filtered_pose_indexes()
    def _on_filter_device_checked(self, event):
        self.device_sel_box.Enable(event.IsChecked()) 
        self._get_filtered_pose_indexes()
    def _on_filter_pose_range_checked(self, event):
        self.pose_range_sel_box.Enable(event.IsChecked())
        self._get_filtered_pose_indexes()
    def _on_filter_bb_checked(self, event):
        self.bb_sel_box.Enable(event.IsChecked())
        self._get_filtered_pose_indexes()

    def _hide_op_children(self):
        self.op_dev_change_choice_ctrl.Hide()
        self.op_deinterleave_algo__choice_ctrl.Hide()
        self.op_x.Hide()
        self.op_y.Hide()
        self.op_z.Hide()
        self.op_p.Hide()
        self.op_t.Hide()
        self.op_x_ctrl.Hide()
        self.op_y_ctrl.Hide()
        self.op_z_ctrl.Hide()
        self.op_p_ctrl.Hide()
        self.op_t_ctrl.Hide()
        self.op_dist.Hide()
        self.op_dist_ctrl.Hide()
        self.op_retarget_x.Hide()
        self.op_retarget_x_ctrl.Hide()
        self.op_retarget_y.Hide()
        self.op_retarget_y_ctrl.Hide()
        self.op_retarget_z.Hide()
        self.op_retarget_z_ctrl.Hide()
           
    def _on_operation_selected(self, event):
        self._hide_op_children()
        self.selected_op = self.operations_ctrl.GetStringSelection()
        self._get_filtered_pose_indexes()
        if self.selected_op == "Change Device":
            self.op_dev_change_choice_ctrl.Show()
        elif self.selected_op == "Deinterleave":
            self.op_deinterleave_algo__choice_ctrl.Show()
        elif self.selected_op == "Increment Position":
            self.op_x.Show()
            self.op_y.Show()
            self.op_z.Show()
            self.op_p.Show()
            self.op_t.Show()
            self.op_x_ctrl.Show()
            self.op_y_ctrl.Show()
            self.op_z_ctrl.Show()
            self.op_p_ctrl.Show()
            self.op_t_ctrl.Show()
        elif self.selected_op == "Forward/Back":
            self.op_dist.Show()
            self.op_dist_ctrl.Show()
        elif self.selected_op == "Retarget":
            self.op_retarget_x.Show()
            self.op_retarget_x_ctrl.Show()
            self.op_retarget_y.Show()
            self.op_retarget_y_ctrl.Show()
            self.op_retarget_z.Show()
            self.op_retarget_z_ctrl.Show()
            

            
    def _get_filtered_pose_indexes(self) -> list:
        filtered_idxs = []
        self.core.project.adhocs.clear()
        if self.selected_op == "Deinterleave":       
            self.pose_count_label.SetLabel(f"{len(self.core.project.poses)} pose(s) selected.")
        else:
            filter_check = False
            for i, p in enumerate(self._op_deinterleave_to_poses_copy(self.deinterleave_algo)):
                p5 = p.position_as_point5
                if self.filter_device.IsChecked():
                    if p.position.device in self.device_checklist.CheckedItems:
                        filter_check = True
                    else:
                        continue    
                if self.filter_bb.IsChecked():
                    min_x = min(self.bb_start_x_ctrl.num_value,self.bb_end_x_ctrl.num_value)
                    max_x = max(self.bb_start_x_ctrl.num_value,self.bb_end_x_ctrl.num_value)
                    min_y = min(self.bb_start_y_ctrl.num_value,self.bb_end_y_ctrl.num_value)
                    max_y = max(self.bb_start_y_ctrl.num_value,self.bb_end_y_ctrl.num_value)
                    min_z = min(self.bb_start_z_ctrl.num_value,self.bb_end_z_ctrl.num_value)
                    max_z = max(self.bb_start_z_ctrl.num_value,self.bb_end_z_ctrl.num_value)
                    min_p = min(self.bb_start_p_ctrl.num_value,self.bb_end_p_ctrl.num_value)
                    max_p = max(self.bb_start_p_ctrl.num_value,self.bb_end_p_ctrl.num_value)
                    min_t = min(self.bb_start_t_ctrl.num_value,self.bb_end_t_ctrl.num_value)
                    max_t = max(self.bb_start_t_ctrl.num_value,self.bb_end_t_ctrl.num_value)
                    lower = vec3(min_x,min_y, min_z)
                    upper = vec3(max_x,max_y,max_z)
                    self.core.project.adhocs.append(AABoxObject3D(lower, upper))
                    if (min_x <= p5.x <= max_x and min_y <= p5.y <= max_y and min_z <=  p5.z <= max_z and min_p <=  rad_to_dd(p5.p) <= max_p and min_t <=  rad_to_dd(p5.t) <= max_t):
                            filter_check = True
                    else: 
                        continue
                if self.filter_pose_range.IsChecked():
                    if (i>= int(self.start_pose_ctrl.GetValue()) and i<= int(self.end_pose_ctrl.GetValue())):
                        filter_check = True
                    else:
                        continue
                if filter_check:
                    filtered_idxs.append(i)
            self.pose_count_label.SetLabel(f"{len(filtered_idxs)} pose(s) selected.")
        return filtered_idxs
    
    def _on_apply(self, event):
        if self.selected_op == "Deinterleave":
            algo = self.op_deinterleave_algo__choice_ctrl.GetStringSelection()
            self._op_deinterleave_active_poseset(algo)
        elif self.selected_op == "Change Device":
            self._op_deinterleave_active_poseset(self.deinterleave_algo)
            for f in self._get_filtered_pose_indexes():
                p = self.core.project.poses[f] 
                p.position.device = self.op_dev_change_choice_ctrl.GetSelection() 
                for a in p.payload:
                    a.device = self.op_dev_change_choice_ctrl.GetSelection()
            self.core.project.pose_sets._dispatch()
        elif self.selected_op == "Delete":
            self._op_deinterleave_active_poseset(self.deinterleave_algo)     
            for f in reversed(self._get_filtered_pose_indexes()):
                self.core.project.delete_pose_set(f) #since we deinterleaved, there should be one pose per poseset, so we can delete the posesets.
            self.core.project.pose_sets._dispatch() 
        elif self.selected_op == "Increment Position":     
            for f in self._get_filtered_pose_indexes():
                pp = self.core.project.poses[f].position 
                p5 =  self.core.project.poses[f].position_as_point5
                new_point = [0,0,0,0,0]
                new_point[0] = p5[0] + self.op_x_ctrl.num_value
                new_point[1] = p5[1] + self.op_y_ctrl.num_value
                new_point[2] = p5[2] + self.op_z_ctrl.num_value
                new_point[3] = sanitize_number(p5[3] + dd_to_rad(self.op_p_ctrl.num_value))
                new_point[4] = sanitize_number(p5[4] + dd_to_rad(self.op_t_ctrl.num_value))
                args = create_action_args(new_point)
                argc = min(len(pp.args), len(args))
                for i in range(argc):
                    pp.args[i] = args[i]
                pp.argc = argc
                pp.update()
            self.core.project.pose_sets._dispatch()
        elif self.selected_op == "Forward/Back":     
            for f in self._get_filtered_pose_indexes():
                pp = self.core.project.poses[f].position 
                p5 =  self.core.project.poses[f].position_as_point5
                dist = self.op_dist_ctrl.num_value
                new_x, new_y, new_z =get_end_position(p5, dist)
                new_point = [0,0,0,0,0]
                new_point[0] = new_x
                new_point[1] = new_y
                new_point[2] = new_z
                new_point[3] = p5[3]
                new_point[4] = p5[4]
                args = create_action_args(new_point)
                argc = min(len(pp.args), len(args))
                for i in range(argc):
                    pp.args[i] = args[i]
                pp.argc = argc
                pp.update()
            self.core.project.pose_sets._dispatch()
        elif self.selected_op == "Retarget":     
            for f in self._get_filtered_pose_indexes():
                pp = self.core.project.poses[f].position 
                p3 =  self.core.project.poses[f].position_as_vec3
                target_x = self.op_retarget_x_ctrl.num_value
                target_y = self.op_retarget_y_ctrl.num_value
                target_z = self.op_retarget_z_ctrl.num_value
                new_point = [p3[0],p3[1],p3[2],0,0]
                new_point[3], new_point[4] = get_heading(p3,vec3(target_x,target_y,target_z))
                args = create_action_args(new_point)
                argc = min(len(pp.args), len(args))
                for i in range(argc):
                    pp.args[i] = args[i]
                pp.argc = argc
                pp.update()
            self.core.project.pose_sets._dispatch()
        self._get_filtered_pose_indexes()

    def _on_close(self, event):
        self.core.project.adhocs.clear()
        dispatcher.disconnect(self._get_filtered_pose_indexes, signal='ntf_a_list_changed') 
        self.Close()
   
    #return a copy of deinterleaved list of poses without changing anything
    def _op_deinterleave_to_poses_copy(self, algorithm:str="by_device"): 
        self.deinterleaved = True
        sorted_poses = []
        if algorithm == "By Device":
            get_device = lambda a: a.position.device
            sorted_poses = sorted(self.core.project.poses, key=get_device)
        elif algorithm == "By Order":
            for ps in self.core.project.pose_sets:
                for p in ps:
                    sorted_poses.append(p)
        return(sorted_poses)        

    #op functions should be moved to another class inside of copis probabaly called as project.deinterleave() etc.
    #aplies the deinterleave to project posesets
    def _op_deinterleave_active_poseset(self, algorithm:str="By Device"):
        if algorithm != self.deinterleave_algo:
            self.deinterleave_algo = algorithm
            self.deinterleaved = False
        if not self.deinterleaved:
            self.deinterleaved = True
            get_device = lambda a: a.position.device
            sorted_poses = self._op_deinterleave_to_poses_copy(algorithm)
            de_interleaves_pose_sets = []
            for pose in sorted_poses:
                de_interleaves_pose_sets.append([pose])
            self.core.project.pose_sets.clear(False)
            self.core.project.pose_sets.extend(de_interleaves_pose_sets)
        self.deinterleaved = True