import sys
import getopt
import datetime
import time
import sqlite3
import os
import csv
import hashlib
import json
import math
from configparser import ConfigParser
import tkinter as tk
from exif import Image
from tkinter import filedialog
from copis import store
#simple pose metadata linker

def hash_file(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
       chunk = 0
       while chunk != b'':
           chunk = f.read(2 ** 20)
           hash_md5.update(chunk)
    return hash_md5.hexdigest()

def use_gui():
    root = tk.Tk()
    root.withdraw()
    print('Syncing COPIS Images')
    print('Select a root image folder:')
    src_path = filedialog.askdirectory(initialdir = os.path.dirname(os.path.realpath(__file__)))
    print(src_path)

    print('Select a sys_db file:')
    db_file = filedialog.askopenfilename(initialdir = os.path.dirname(os.path.realpath(__file__)),filetypes=[('COPIS DB Files',['.db'])] )
    print(db_file)

    print('Select your serial number to cam_id mappings file file:')
    sn_file = filedialog.askopenfilename(initialdir = os.path.dirname(os.path.realpath(__file__)), filetypes=[('Mapping File',['.json'])] )
    print(sn_file)

    print('Save output to:')
    out_file = filedialog.asksaveasfilename(initialdir = os.path.dirname(os.path.realpath(__file__)))
    print(out_file)

    

class Pose_Img_Linker:
    def __init__ (self):
        self._input_folder = None
        self._json_profile = None
        self._dbfile = None
        self._db = None
        self._output_csv = None
        self._cam_sn_to_id = {}
        self.max_buffer_secs = 5
        self.img_types = {1:'.jpg',2:None}
        self.exif_time_diffs = {}
        self.save_to_db = False
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        if self._db != None:
            self._db.close()
    
    @property
    def input_folder(self):
        return self._input_folder
    @input_folder.setter
    def input_folder(self, x):
        if (not os.path.exists(x)):
            raise FileNotFoundError("Image input folder not found")
        self._input_folder = x
    
    @property
    def profile(self):
        return self._profile
    @profile.setter
    def profile(self, x):
        if (not os.path.exists(x)):
            raise FileNotFoundError("Profile not found")
        ext = os.path.splitext(x)[1]
        if ext.lower() == '.ini':
            cp = ConfigParser()
            cp.read(x)
            if 'Project' in cp and 'profile_path' in cp['Project'] and os.path.exists(cp['Project']['profile_path']):
                x = cp['Project']['profile_path']
                ext = os.path.splitext(x)[1]
            else:
                raise Exception('Profile path not referenced in ini')
        if ext.lower() == '.json':
            f = open(x)
            _json_profile = json.load(f)
            f.close()
            for d in _json_profile['devices']:
                if 'id' in d and 'serial_no' in d:
                    #print (d['serial_no'])
                    self._cam_sn_to_id[d['serial_no']] = d['id']
        else:
            raise Exception('Invalid profile name')
    
    @property
    def dbfile(self):
        return self._dbfile
    @dbfile.setter
    def dbfile(self, x):
        if (not os.path.exists(x)):
            raise FileNotFoundError("DB file not found")
        self._dbfile = x

    @property
    def output_csv(self):
        return self._output_csv
    @output_csv.setter
    def output_csv(self, x):
        self._output_csv = x
    

    def run(self):
        if self._input_folder == None or self._dbfile == None or len(self._cam_sn_to_id) == 0:
            raise Exception('inavalid parameters')
        dof = {}
        for f_type in self.img_types.values():
            if f_type != None and f_type != '':
                dof[f_type] = []
                for root, dirs, files in os.walk(self._input_folder):
                    for file in files:
                        f = os.path.join(root,file)
                        if (f.lower().endswith(f_type)):
                            dof[f_type].append(os.path.join(root,file))
        for k,v in dof.items():
            print(f'{len(v)} {k}(s) discovered')
        self._db = sqlite3.connect(self._dbfile)
        cur = self._db.cursor()
        with open(self.output_csv, 'w', encoding='utf-8', newline='\n') as csvfile:
            csvwriter = csv.writer(csvfile)  
            csvwriter.writerow(['session_id','image_id','cam_id','x','y','z','p','t','img_fname','img_md5','exif_timestamp','time_buff'])  
            imgs_linked = 0
            max_buf_used = 0
            n = 0
            for ftype, lof in dof.items():
                imgs_linked = 0
                for k, v in self.img_types.items():
                    if ftype == v:
                        n = k
                md5_param = f'img{n}_md5'
                fname_param = f'img{n}_fname'
                for f in lof:
                    img_filename = f
                    h = hash_file(img_filename)
                    #exif data has three option for date time:datetime,datetime_original,datetime_digitized
                    #we will default to using datetime_digitized
                    with open(img_filename, 'rb') as image_file:
                        my_image = Image(image_file)
                    image_dt = datetime.datetime.strptime(my_image.datetime_digitized,'%Y:%m:%d %H:%M:%S')
                    image_t  = time.mktime(time.strptime(my_image.datetime_digitized,'%Y:%m:%d %H:%M:%S'))
                    #body_serial_number camera_owner_name lens_serial_number
                    cam_sn = my_image.body_serial_number
                    cam_id = self._cam_sn_to_id[cam_sn]
                    if cam_id in self.exif_time_diffs: #account for any time differential from improperly set cameras
                        image_t = image_t + self.exif_time_diffs[cam_id]
                    #we subtract a onesecond buffer to the start time
                    buffer_sec = -1
                    c = 0
                    while (c == 0 and buffer_sec <= self.max_buffer_secs):
                        buffer_sec +=1
                        s = f"select session_id,id,cam_id,x,y,z,p,t,{md5_param}, unix_time_start, unix_time_end from image_metadata where cam_id = ? and ? >= (cast(unix_time_start as int) - {buffer_sec}) and ? <= (cast(unix_time_end as int) + {buffer_sec}); "
                        data = cur.execute(s,(cam_id,image_t,image_t))
                        rows = data.fetchall()
                        c = len(rows)
                    #max_buf_used = max(max_buf_used,buffer_sec)
                    if len(rows) <1:
                        csvwriter.writerow(['No timestamp match','','','','','','',img_filename,h,str(image_t),str(buffer_sec)])  
                    elif len(rows) > 1:
                        csvwriter.writerow(['>1 timestamp match','','','','','','',img_filename,h,str(image_t),str(buffer_sec)])
                    else:
                        for row in rows:
                            t_start = row[9]
                            t_end = row[10]
                            if image_t < t_end:
                                buffer_sec = buffer_sec * -1
                            if max(abs(max_buf_used),abs(buffer_sec)) >  abs(max_buf_used):
                                   max_buf_used = buffer_sec
                            img_md5 = row[8] 
                            image_id = row[1]
                            if img_md5 != '' and img_md5 != None and img_md5 != h:
                                print('houston we have a problem prior sync, with diff hash detected')
                                h = ':'.join(('hash conflict',h,img_md5))
                            #elif h == img_md5:
                                #print('previously synced, skipping update')
                            #    imgs_linked+=1
                            else:
                                imgs_linked+=1
                                if self.save_to_db:
                                    s = f'UPDATE image_metadata SET {md5_param} = ?, {fname_param} = ? where id = ?;'
                                    v = (h,img_filename,image_id)
                                    cur.execute(s, v)    
                            csvwriter.writerow(row[0:8] + (img_filename,h,str(image_t), str(buffer_sec)))
                print(str(imgs_linked), ' ', str(ftype), '(s) linked')
            print('max time buffer: ', str(max_buf_used), ' seconds.')
        self._db.commit()
        cur.close()
        self._db.close()
        
    
def showHelp():
    print('pose_img_linker.py -i <input images folder> -p <copis ini or json profile> -d <sys db file> -o <output csv file> [options]')
    print('-b <buffer time in sec> default: 5')
    print('-f <img file type 1> default: .jpg')
    print('-e <img file type 2> default: None')
    print('-s <update databse> default: False')
    print('-t <comma delimited array of time diferential to apply to exif data> default: None')
    print('    format: camid:timediff_sec,camid2:timdiff_sec2...')
    print('    useful if a camera\'s time is set incorrectly.')
    sys.exit()

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:o:p:d:h:b:f:e:t:s')
    except getopt.GetoptError as err:
        print(err)
        print('invalid args, for help: pose_img_linker.py -h')
        sys.exit(2)
    
    pil = Pose_Img_Linker()    

    #pil.profile =  'profiles\\ypm_three.json'
    #pil.dbfile = 'C:\\Users\\nelson\\Desktop\\images_for_olivia_ren\\copis.db'
    #pil.input_folder = 'C:\\Users\\nelson\\Desktop\\images_for_olivia_ren\\west_campus_dataset_2' 
    #pil.output_csv = 'test2.csv'
    #pil.img_types[2] = '.cr2'
    #pil.save_to_db = True
    if len(opts) == 0:
        showHelp()
        sys.exit()
    for opt, arg in opts:
        if opt == '-i':
             pil.input_folder = arg
        elif opt == '-o':
            pil.output_csv = arg
        elif opt == '-p':
            pil.profile = arg
        elif opt == '-d':
            pil.dbfile = arg
        elif opt == '-b':
            if int(arg) >= 0:
                pil.max_buffer_secs = int(arg)
            else:
                raise ValueError('invalid buffer time') 
        elif opt == '-f':
            pil.img_types[1] = arg
        elif opt == '-e':
            pil.img_types[2] = arg
        elif opt == '-s':
            pil.save_to_db = True
        elif opt == '-t':
            for a in arg.split(','):
                kv = a.split(':')
                if int(kv[0]) in pil.exif_time_diffs:
                    pil.exif_time_diffs[int(kv[0])] = pil.exif_time_diffs[int(kv[0])] + int(kv[1])
                else:
                    pil.exif_time_diffs[int(kv[0])] = int(kv[1])
        elif opt == '-h':
            showHelp()
            sys.exit()
        else:
            raise ValueError('unhandled option') 

    pil.run()
        
       