
import time
import sqlite3
from sqlite3 import Error
from copis import store
from copis.classes import Device
from copis.helpers import hash_file_md5
class SysDB():
    """Represents a system database object in sqlite that can be used for tracking all image and serial requests. 
       Sys db can be used to sync images with positional information 
    """

    _schema = {'image_metadata': {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT', 
                   'x': 'REAL', 'y': 'REAL','z': 'REAL','p': 'REAL','t': 'REAL',
                   'src' : 'TEXT', 'img1_md5' : 'TEXT', 'img1_fname' : 'TEXT', 'img2_md5': 'TEXT',  'img2_fname' : 'TEXT', 'session_id' : 'INTEGER',
                   'cam_id' : 'INTEGER', 'cam_serial_no': 'TXT', 'cam_name' : 'TEXT', 'cam_type' : 'TEXT', 'cam_desc' : 'TEXT', 
                   'unix_time_start' : 'REAL', 'unix_time_end' : 'REAL',
                   },
               'serial_tx': {'id' : 'INTEGER PRIMARY KEY AUTOINCREMENT',
                             'data' : 'BLOB', 'unix_time' : 'REAL'},
               'serial_rx': {'id' : 'INTEGER PRIMARY KEY AUTOINCREMENT',
                             'data' : 'BLOB', 'unix_time' : 'REAL'}
               }

    def __init__(self):
        self._filename = store.get_sys_db_path()
        if self._filename == '':
            self._is_initialized = False
            return
        self._create_or_update_schema()
        self._poses_in_play = {} #dict keeping containing devices id's and corresponding database id's for poses "in play" (ie awaiting idle respose after imaging)
        self._is_initialized = True
        print("using sysdb: ", self._filename )
    

    @property
    def is_initialized(self) -> bool:
        """Returns True if db has been successfully initialized, false otherwise """
        return self._is_initialized

    def _create_or_update_schema(self):
        """Creates databse or checks to make sure schema is up to date, 
        adding missings columns to tables """
        db =  sqlite3.connect(self._filename)
        for tbl_name, tbl_schema in self._schema.items():
            s = f'SELECT name FROM sqlite_master WHERE type=\'table\' AND name=\'{tbl_name}\'';
            if len(db.execute(s).fetchall()) == 0:
                fields = ','.join(' '.join((k,v)) for (k,v) in tbl_schema.items())
                s = f'CREATE TABLE IF NOT EXISTS {tbl_name} ({fields});'
                db.execute(s)
            else:
                s = f'PRAGMA table_info({tbl_name})'
                rows = db.execute(s,[]).fetchall()
                for k,v in tbl_schema.items():    
                    if len ([item for item in rows if item[1] == k]) == 0:
                        s = f'ALTER TABLE {tbl_name} ADD COLUMN {k} {v};';
                        print(s)
                        db.execute(s)
        db.commit()
        db.close()
    
    def last_session_id(self) -> int:
        if not self._is_initialized:
            return -1
        result = -1
        s = 'select MAX(session_id) from image_metadata;'
        db = sqlite3.connect(self._filename)
        cur = db.cursor()
        cur.execute(s)
        r = cur.fetchone()
        if r[0] is not None:
            result = r[0]
        cur.close()
        db.close()
        return result

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

    def start_pose(self, device: Device, src: str, session_id=-1) -> int:
        if not self._is_initialized:
            return -1
        id = -1
        v = (session_id,      \
             device.position.x, \
             device.position.y, \
             device.position.z, \
             device.position.p, \
             device.position.t, \
             src,               \
             device.device_id,  \
             device.serial_no,  \
             device.name,       \
             device.type,       \
             device.description,\
             time.time())

        s = 'INSERT INTO image_metadata (session_id,x,y,z,p,t,src,cam_id,cam_serial_no,cam_name,cam_type,cam_desc,unix_time_start) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?);'
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

    def update_pose_output(self, device: Device, fname:str) -> int:
        if not self._is_initialized:
            return -1
        if device.device_id in self._poses_in_play and len(self._poses_in_play[device.device_id]) > 0:
            p_id = self._poses_in_play[device.device_id][0] #the reason we maintain a list even thoug only one image can be taken at a time per device, is that in case the device signals it is finished and recieves another image request while we are still processing the last.
            db = sqlite3.connect(self._filename)
            cur = db.cursor()
            s = f'select img1_fname, img2_fname from image_metadata WHERE id = {p_id} and unix_time_end is null;'
            cur.execute(s)
            r = cur.fetchone()
            p1 = 'img1_fname'
            p2 = 'img1_md5'
            if r[0] is not None:
                p1 = 'img2_fname'
                p2 = 'img2_md5'
                if r[1] is not None:
                    cur.close()
                    db.close()
                    return -3
            h = hash_file_md5(fname)
            s = f'UPDATE image_metadata SET {p1} = ?, {p2} = ? WHERE id =? and unix_time_end is null;'
            v = (fname,h, p_id)
            cur.execute(s, v)
            cur.close()
            db.commit()
            db.close()
            return p_id
        return -2

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



    

    