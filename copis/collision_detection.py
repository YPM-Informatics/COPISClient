from ast import Return
import math
from typing import List
import glm
from glm import vec3
from copis.classes import (BoundingBox, Object3D, OBJObject3D, Device)
import copis.globals

from copis.project import Project


def collision_eval_cam2cam_path() -> List[dict]: 
    collisions = []
    proj = Project()
    if proj._is_initialized:
        for i in range(0,len(proj.pose_sets)-1):
            for k in range(0, len(proj.devices)):
                a = proj.devices[k]
                a_start = proj.last_pose_by_dev_id(i,a.device_id)
                if a_start != None:
                    a_end = proj.pose_by_dev_id(i + 1,a.device_id) 
                    if a_end == None:
                        a_end = a_start
                    for j in range(k+1, len(proj.devices)):
                        b = proj.devices[j]
                        b_start = proj.last_pose_by_dev_id(i,b.device_id)
                        if b_start != None:
                            b_end = proj.pose_by_dev_id(i + 1,b.device_id)
                            if b_end == None:
                                b_end = b_start
                            if is_collision_between_moving_cams(a, a_start.position_as_vec3, a_end.position_as_vec3, b, b_start.position_as_vec3, b_end.position_as_vec3):
                                collisions.append({'ps_idx':i+1,'cams':(a.device_id,b.device_id)}) 
                            
    return collisions

def collision_eval_cam2proxy_path() -> List[dict]:
    collisions = []
    proj = Project()
    if proj._is_initialized:
        for i in range(0,len(proj.pose_sets)-1):
            for k in range(0, len(proj.devices)):
                a = proj.devices[k]
                a_start = proj.last_pose_by_dev_id(i,a.device_id)
                if a_start != None:
                    a_end = proj.pose_by_dev_id(i + 1,a.device_id)
                    if a_end == None:
                        a_end = a_start
                    for proxy in proj.proxies:
                        if is_collision_between_proxy_cam_move(a, a_start.position_as_vec3, a_end.position_as_vec3, proxy.bbox) :
                            collisions.append({'ps_idx':i+1,'cams':(a.device_id,-1)})
    return collisions

def collision_eval_cam2proxy_start() -> List[dict]:
    collisions = []
    proj = Project()
    if proj._is_initialized:
        if len(proj.pose_sets) > 0:
            for device in proj.devices:
                first_pose = proj.first_pose_by_dev_id(0, device.device_id)
                if first_pose != None:
                    for proxy in proj.proxies:
                        if is_collision_between_proxy_cam_move(device, device.position,first_pose.position_as_vec3, proxy.bbox):
                            collisions.append({'ps_idx':-1,'cams':(-1,-1)})          
    return collisions

def collision_eval_cam2cam_start() -> List[dict]:
    collisions = []
    proj = Project()
    if proj._is_initialized:
        if len(proj.pose_sets) > 0:
            for k in range(0, len(proj.devices)):
                a = proj.devices[k]
                first_pose_a = proj.first_pose_by_dev_id(0,a.device_id)
                if first_pose_a != None: 
                    for j in range(k+1, len(proj.devices)):
                        b = proj.devices[j]
                        first_pose_b = proj.first_pose_by_dev_id(0,b.device_id)
                        if first_pose_b != None:
                            if is_collision_between_moving_cams(a, a.position, first_pose_a.position_as_vec3, b, b.position, first_pose_b.position_as_vec3):
                                collisions.append({'ps_idx':-1,'cams':(a.device_id,b.device_id)})           
    return collisions


class sphere(object):
    def __init__(self, p:vec3, r: float):
        self.p = p
        self.r = r

#axis aligned box
class aab(object): 
    def __init__(self, lower:vec3, upper: vec3):
        self.lower = lower
        self.upper = upper

#represents a series of bounding 3d geometries representing the head, body and gantry
class cam_bounds:
    def __init__(self, device: Device, pos:vec3):
        head_radius = device.head_radius #200
        body_width = device.body_dims.y #100
        body_depth = device.body_dims.x #40
        body_height= device.body_dims.z * device.gantry_orientation #740 * chamber_pos # starting point is center of head
        gantry_width = device.gantry_dims.x #1000
        gantry_depth = device.gantry_dims.y #125
        gantry_height = device.gantry_dims.z #110
        max_z_travel = 300
        self.head = sphere(pos, head_radius)                                              
        l_body = vec3(pos.x-body_width/2,pos.y-body_depth/2,pos.z)
        u_body = vec3(pos.x+body_width/2,pos.y+body_depth/2,pos.z+body_height) 
        self.body = aab(l_body,u_body)
        l_gantry = vec3(pos.x-gantry_width/2,pos.y-gantry_depth/2, max_z_travel)
        u_gantry = vec3(pos.x+gantry_width/2,pos.y+gantry_depth/2,pos.z+ max_z_travel - gantry_height) 
        self.gantry = aab(l_gantry,u_gantry)

def dist3d(p1:vec3, p2:vec3):
    d = math.sqrt((p2.x - p1.x)*(p2.x - p1.x) + (p2.y - p1.y)*(p2.y - p1.y) + (p2.z - p1.z)*(p2.z - p1.z))
    return d

def is_collision_between_sphere(s1:sphere,s2:sphere):
    if (dist3d(s1.p,s2.p) < (s1.r + s2.r)):
        return True 
    else: 
        return False

def is_collision_between_aab(b1: aab, b2:aab):
    if (b1.lower.x <= b2.upper.x) and (b1.upper.x >= b2.lower.x) \
    and (b1.lower.y <= b2.upper.y) and (b1.upper.y >= b2.lower.y)  \
    and (b1.lower.z <= b2.upper.z) and (b1.upper.z >= b2.lower.z) :
        return True
    else:
        return False

def is_point_inside_AABB(p: vec3, b:aab):
    if (p.x >= b.lower.x) and (p.x <= b.upper.x) and (p.y >= b.lower.y) and (p.y <= b.upper.y) and (p.z >= b.lower.z) and (p.z <= b.upper.z):
        return True
    else:
        return False

def is_point_inside_sphere(p: vec3, s:sphere):
    d = math.sqrt((p.x-s.p.x)*(p.x-s.p.x) + (p.y-s.p.y)*(p.y-s.p.y) + (p.z-s.p.z)*(p.z-s.p.z))
    if d < s.r:
        return True
    else:
        return False

def is_collision_between_aab_sphere(b:aab, s:sphere):
    x = max(b.lower.x, min(s.p.x,b.upper.x))
    y = max(b.lower.y, min(s.p.y,b.upper.y))
    z = max(b.lower.z, min(s.p.z,b.upper.z))
    return is_point_inside_sphere(vec3(x,y,x),s)

def is_collision_between_cam_bounds(a:cam_bounds, b:cam_bounds):
    #note gantry only needs to be checked against other gantries since they can't collid with anything else
    #head_a to all_b
    if is_collision_between_sphere(a.head,b.head):
        return True
    elif is_collision_between_aab_sphere(b.body,a.head):
        return True
    elif is_collision_between_aab_sphere(b.gantry,a.head):
        return True
    #Body_a to body_b and gantry_b
    elif is_collision_between_aab(a.body,b.body):
        return True
    elif is_collision_between_aab(a.body,b.gantry):
        return True
    #gantry_a to gantry_b
    elif is_collision_between_aab(a.gantry,b.gantry):
        return True
    #head_b to body_a
    elif is_collision_between_aab_sphere(a.body,b.head):
        return True
    return False
    
def bresenham_3D(p1:vec3, p2:vec3) ->  List[vec3]:
    _p1 = vec3(p1[0],p1[1],p1[2])
    results : List[vec3] = []
    results.append(vec3(_p1))
    dx = abs(p2.x - _p1.x)
    dy = abs(p2.y - _p1.y)
    dz = abs(p2.z - _p1.z)
    if (p2.x > _p1.x):
        xs = 1
    else:
        xs = -1
    if (p2.y > _p1.y):
        ys = 1
    else:
        ys = -1
    if (p2.z > _p1.z):
        zs = 1
    else:
        zs = -1
    
    # Lead axis is X-axis"
    if (dx >= dy and dx >= dz):        
        e1= 2 * dy - dx
        e2= 2 * dz - dx
        while (_p1.x != p2.x):
            _p1.x += xs
            if (e1>= 0):
                _p1.y += ys
                e1-= 2 * dx
            if (e2>= 0):
                _p1.z += zs
                e2-= 2 * dx
            e1+= 2 * dy
            e2+= 2 * dz
            results.append(vec3(_p1))
  
    # Lead axis is Y-axis"
    elif (dy >= dx and dy >= dz):       
        e1= 2 * dx - dy
        e2= 2 * dz - dy
        while (_p1.y != p2.y):
            _p1.y += ys
            if (e1>= 0):
                _p1.x += xs
                e1-= 2 * dy
            if (e2>= 0):
                _p1.z += zs
                e2-= 2 * dy
            e1+= 2 * dx
            e2+= 2 * dz
            results.append(vec3(_p1))
  
    # Lead axis is Z-axis"
    else:        
        e1 = 2 * dy - dz
        e2 = 2 * dx - dz
        while (_p1.z != p2.z):
            _p1.z += zs
            if (e1 >= 0):
                _p1.y += ys
                e1 -= 2 * dz
            if (e2 >= 0):
                _p1.x += xs
                _e2 -= 2 * dz
            e1 += 2 * dy
            e2 += 2 * dx
            results.append(vec3(_p1))
    return results

def point_at_dist(p1: vec3, p2: vec3, d: float):
    d1 = dist3d(p1,p2)
    if d1 == 0:
        return p1
    n = d/d1
    x = p1.x + (p2.x-p1.x) *n
    y = p1.y + (p2.y-p1.y) *n
    z = p1.z + (p2.z-p1.z) *n
    return vec3(x,y,z)

def gen_points_along_line(p1: vec3, p2: vec3, d: float) -> List[vec3] :
    results = []
    results.append(vec3(p1.x,p1.y,p1.z))
    if (p1.x == p2.x and p1.y == p2.y  and p1.z == p2.z):
        return results
    total_d = dist3d(p1,p2)
    cur_d = d
    while cur_d < total_d-d:
        results.append(point_at_dist(p1,p2,cur_d))
        cur_d = cur_d + d
    results.append(vec3(p2.x,p2.y,p2.z))
    return results

def cam_bounds_along_line(device : Device, start_pos: vec3, end_pos: vec3, increment_dist: float) ->List[cam_bounds] :
    results = []
    cam_pts = gen_points_along_line(start_pos,end_pos, increment_dist)
    for p in cam_pts:
        results.append(cam_bounds(device, p))
    return results

def is_collision_between_moving_cams(cam1: Device, cam1_start_pos: vec3, cam1_end_pos: vec3, cam2: Device, cam2_start_pos: vec3, cam2_end_pos: vec3):
    cb_list1 = cam_bounds_along_line(cam1, cam1_start_pos, cam1_end_pos, 5)
    cb_list2 = cam_bounds_along_line(cam1, cam2_start_pos, cam2_end_pos, 5)
    for cb1 in cb_list1:
        for cb2 in cb_list2:
            if (is_collision_between_cam_bounds(cb1,cb2)):
                return True
    return False

def is_collision_between_proxy_cam_move(cam : Device, cam_start_pos: vec3, cam_end_pos: vec3, proxy_aab :aab ):
    cb_list1 = cam_bounds_along_line(cam, cam_start_pos, cam_end_pos, 3)
    for cb1 in cb_list1:
        if is_collision_between_aab_sphere(proxy_aab, cb1.head):
            return True
    return False

    