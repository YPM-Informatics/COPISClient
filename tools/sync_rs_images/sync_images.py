import datetime
import time
import sqlite3
from exif import Image
import os
import csv
import hashlib
import json
import tkinter as tk
from tkinter import filedialog



def hash_file(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
       chunk = 0
       while chunk != b'':
           chunk = f.read(2 ** 20)
           hash_md5.update(chunk)
    return hash_md5.hexdigest()

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

if os.path.exists(db_file) and os.path.exists(sn_file):

    f = open(sn_file)
    cam_sn_to_id = json.load(f)
    f.close()
    lof = []

    for root, dirs, files in os.walk(src_path):
        for file in files:
            f = os.path.join(root,file)
            if (f.lower().endswith('.jpg')):
                lof.append(os.path.join(root,file))
    
    db = sqlite3.connect(db_file)
    cur = db.cursor()
    with open(out_file, 'w', encoding='utf-8', newline='\n') as csvfile:
        csvwriter = csv.writer(csvfile)  
        csvwriter.writerow(['image_id','cam_id','x','y','z','p','t','img_filename','img_hash','exif_timestamp'])  
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
            cam_id = cam_sn_to_id[cam_sn]
            
            #we subtract a onesecond buffer to the start time
            s = "select id,cam_id,x,y,z,p,t,ext_info from image_metadata where cam_id = ? and ? >= cast(unix_time_start as int) -1 and ? <= cast(unix_time_end as int)"
            data = cur.execute(s,(cam_id,image_t,image_t))
            rows = data.fetchall()
            if len(rows) <1:
                csvwriter.writerow(['No timestamp match','','','','','',img_filename,h,str(image_t)])  
            elif len(rows) > 1:
                csvwriter.writerow(['>1 timestamp match','','','','','',img_filename,h,str(image_t)])
            else:
                for row in rows:
                    ext_info = row[7] 
                    image_id = row[0]
                    if ext_info == '':
                        s = 'UPDATE image_metadata SET ext_info = ? where id = ?;'
                        v = (h,image_id)
                        cur.execute(s, v)
                        db.commit()
                    elif h == ext_info:
                        print('previously synced, skipping update')
                    else:
                        print('houston we have a problem prior sync, with diff hash detected')
                        h = ':'.join(('hash conflict',h,ext_info))
                    csvwriter.writerow(row[0:7] + (img_filename,h,str(image_t)))

    cur.close()
    db.close()
    


 
