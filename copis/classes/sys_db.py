
import time
import sqlite3
from sqlite3 import Error
from copis import store
from copis.classes import Device

class SysDB():
    """Represents a system database object in sqlite that can be used for tracking all image and serial requests. 
       Sys db can be used to sync images with positional information 
    """
    def __init__(self):
        self._filename = store.get_sys_db_path()
        if self._filename == '':
            self._is_initialized = False
            return
        if (not store.sys_db_exists()):
            self._create_db()
        self._poses_in_play = {} #dict keeping containing devices id's and corresponding database id's for poses "in play" (ie awaiting idle respose after imaging)
        self._is_initialized = True
        print("using sysdb: ", self._filename )
    

    @property
    def is_initialized(self) -> bool:
        """Returns True if db has been successfully initialized, false otherwise """
        return self._is_initialized

    def _create_db(self):
        db =  sqlite3.connect(self._filename)
        s = """CREATE TABLE IF NOT EXISTS image_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            x REAL, y REAL, z REAL, p REAL, t REAL, 
            src TEXT,ext_info TEXT, 
            cam_id INTEGER, cam_name TEXT, cam_type TEXT, cam_desc TEXT, 
            unix_time_start REAL, unix_time_end REAL
        );"""
        db.execute(s)
        s = """CREATE TABLE IF NOT EXISTS serial_tx (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data BLOB, unix_time REAL
        );"""
        db.execute(s)
        s = """CREATE TABLE IF NOT EXISTS serial_rx (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data BLOB, unix_time REAL
        );"""
        db.execute(s)
        db.commit()
        db.close()
    
    def serial_tx(self, b : bytes) -> int:
        if not self._is_initialized:
            return -1
        s = 'INSERT INTO serial_tx (data, unix_time) VALUES(?,?);'
        db = sqlite3.connect(self._filename)
        cur = db.cursor()
        v = (b,time.time() )
        cur.execute(s, v)
        id = cur.lastrowid
        cur.close()
        db.commit()
        db.close()
        return id

    def serial_rx(self, b : bytes) -> int:
        if not self._is_initialized:
            return -1
        if len(b) <1:
            return -2
        s = 'INSERT INTO serial_rx (data, unix_time) VALUES(?,?);'
        db = sqlite3.connect(self._filename)
        cur = db.cursor()
        v = (b,time.time() )
        cur.execute(s, v)
        id = cur.lastrowid
        cur.close()
        db.commit()
        db.close()
        return id

    def start_pose(self, device: Device, src: str, ext_info = '') -> int:
        if not self._is_initialized:
            return -1
        id = -1
        v = (device.position.x, \
             device.position.y, \
             device.position.z, \
             device.position.p, \
             device.position.t, \
             src,               \
             ext_info,          \
             device.device_id,  \
             device.name,       \
             device.type,       \
             device.description,\
             time.time())

        s = 'INSERT INTO image_metadata (x,y,z,p,t,src,ext_info,cam_id,cam_name,cam_type,cam_desc,unix_time_start) VALUES(?,?,?,?,?,?,?,?,?,?,?,?);'
        db = sqlite3.connect(self._filename)
        cur = db.cursor()
        cur.execute(s, v)
        id = cur.lastrowid
        if device.device_id not in self._poses_in_play:
            self._poses_in_play[device.device_id] = [id]
        else:
            self._poses_in_play[device.device_id].append(id)
        cur.close()
        db.commit()
        db.close()
        return id

    def end_pose(self, device: Device) -> int:
        if not self._is_initialized:
            return -1
        if device.device_id in self._poses_in_play and len(self._poses_in_play[device.device_id]) > 0:
            p_id = self._poses_in_play[device.device_id][0] #the reason we maintain a list even thoug only one image can be taken at a time per device, is that in case the device signals it is finished and recieves another image request while we are still processing the last.
            self._poses_in_play[device.device_id].pop(0)
            db = sqlite3.connect(self._filename)
            cur = db.cursor()
            s = 'UPDATE image_metadata SET unix_time_end = ? WHERE id =? and unix_time_end is null;'
            v = (time.time(), p_id)
            cur.execute(s, v)
            cur.close()
            db.commit()
            db.close()
            return p_id
        return -2



    

    