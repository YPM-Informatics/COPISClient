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

"""Simple pose metadata linker."""

import sys
import shutil
import getopt
import time
import sqlite3
import os
import csv
import hashlib
import json
import tkinter as tk

from configparser import ConfigParser
from tkinter import filedialog
from exif import Image


def _hash_file(filename):
    hash_md5 = hashlib.md5()

    with open(filename, "rb") as file:
        chunk = 0

        while chunk != b'':
            chunk = file.read(2 ** 20)
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def use_gui():
    """Executes the pose image linker in a GUI."""
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


class PoseImgLinker:
    """Implements the ability to link pose images with their recorded metadata."""
    def __init__ (self):
        self._input_folder = None
        self._json_profile = None
        self._profile = None
        self._dbfile = None
        self._db = None
        self._output_csv = None
        self._cam_sn_to_id = {}
        self._bin_by_session = False
        self.max_buffer_secs = 5
        self.img_types = {1:'.jpg', 2:None}
        self.exif_time_diffs = {}
        self.save_to_db = False
        self.bin_by_session_output_folder = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._db is not None:
            self._db.close()

    @property
    def input_folder(self):
        """Returns the input folder."""
        return self._input_folder

    @input_folder.setter
    def input_folder(self, input_dir):
        if not os.path.exists(input_dir):
            raise FileNotFoundError("Image input folder not found")

        self._input_folder = input_dir

    @property
    def profile(self):
        """Returns the profile path."""
        return self._profile

    @profile.setter
    def profile(self, profile_path):
        if not os.path.exists(profile_path):
            raise FileNotFoundError("Profile not found")

        self._profile = profile_path
        ext = os.path.splitext(profile_path)[1]

        if ext.lower() == '.ini':
            config_parser = ConfigParser()
            config_parser.read(profile_path)

            if 'Project' in config_parser and 'profile_path' in config_parser['Project'] and os.path.exists(config_parser['Project']['profile_path']):
                profile_path = config_parser['Project']['profile_path']
                ext = os.path.splitext(profile_path)[1]
            else:
                raise Exception('Profile path not referenced in ini')

        if ext.lower() == '.json':
            with open(profile_path, 'r', encoding='utf-8') as file:
                self._json_profile = json.load(file)

            for dvc in self._json_profile['devices']:
                if 'id' in dvc and 'serial_no' in dvc:
                    self._cam_sn_to_id[dvc['serial_no']] = dvc['id']
        else:
            raise Exception('Invalid profile name')

    @property
    def dbfile(self):
        """Returns the database path."""
        return self._dbfile

    @dbfile.setter
    def dbfile(self, db_path):
        if not os.path.exists(db_path):
            raise FileNotFoundError("DB file not found")

        self._dbfile = db_path

    @property
    def output_csv(self):
        """Returns the ouptut CSV path."""
        return self._output_csv

    @output_csv.setter
    def output_csv(self, out_path):
        self._output_csv = out_path

    def run(self):
        """Runs the pose image linker."""
        if self._input_folder is None or self._dbfile is None or len(self._cam_sn_to_id) == 0:
            raise Exception('invalid parameters')

        dof = {}

        for f_type in self.img_types.values():
            if f_type is not None and f_type != '':
                dof[f_type] = []

                for root, _, files in os.walk(self._input_folder):
                    for file in files:
                        file_path = os.path.join(root, file)

                        if file_path.lower().endswith(f_type):
                            dof[f_type].append(os.path.join(root, file))

        for key, val in dof.items():
            print(f'{len(val)} {key}(s) discovered')

        self._db = sqlite3.connect(self._dbfile)
        cur = self._db.cursor()

        with open(self.output_csv, 'w', encoding='utf-8', newline='\n') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['session_id','image_id','cam_id','x','y','z','p','t','img_fname','img_md5','exif_timestamp','time_buff'])
            imgs_linked = 0
            max_buf_used = 0
            num = 0

            for ftype, lof in dof.items():
                imgs_linked = 0
                for key, val in self.img_types.items():
                    if ftype == val:
                        num = key
                md5_param = f'img{num}_md5'
                fname_param = f'img{num}_fname'
                for file_path in lof:
                    img_filename = file_path

                    hash_code = _hash_file(img_filename)
                    # Exif data has three option for date time: datetime, datetime_original, datetime_digitized.
                    # We will default to using datetime_digitized.
                    with open(img_filename, 'rb') as image_file:
                        my_image = Image(image_file)

                    image_t  = time.mktime(time.strptime(my_image.datetime_digitized,'%Y:%m:%d %H:%M:%S'))
                    # body_serial_number camera_owner_name lens_serial_number
                    cam_sn = my_image.body_serial_number
                    cam_id = self._cam_sn_to_id[cam_sn]

                    if cam_id in self.exif_time_diffs: # Account for any time differential from improperly set cameras.
                        image_t = image_t + self.exif_time_diffs[cam_id]

                    # We subtract a one-second buffer to the start time.
                    buffer_sec = -1
                    count = 0

                    while (count == 0 and buffer_sec <= self.max_buffer_secs):
                        buffer_sec +=1
                        sql = f"select session_id,id,cam_id,x,y,z,p,t,{md5_param}, unix_time_start, unix_time_end from image_metadata where cam_id = ? and ? >= (cast(unix_time_start as int) - {buffer_sec}) and ? <= (cast(unix_time_end as int) + {buffer_sec}); "
                        data = cur.execute(sql,(cam_id,image_t,image_t))
                        rows = data.fetchall()
                        count = len(rows)

                    # max_buf_used = max(max_buf_used,buffer_sec)
                    if len(rows) < 1:
                        csvwriter.writerow(['No timestamp match','','','','','','',img_filename,hash_code,str(image_t),str(buffer_sec)])
                    elif len(rows) > 1:
                        csvwriter.writerow(['>1 timestamp match','','','','','','',img_filename,hash_code,str(image_t),str(buffer_sec)])
                    else:
                        for row in rows:
                            t_end = row[10]

                            if image_t < t_end:
                                buffer_sec = buffer_sec * -1

                            if max(abs(max_buf_used),abs(buffer_sec)) > abs(max_buf_used):
                                max_buf_used = buffer_sec

                            img_md5 = row[8]
                            image_id = row[1]

                            if img_md5 not in ('', None, hash_code):
                                print('houston we have a problem prior sync, with diff hash detected')
                                hash_code = ':'.join(('hash conflict',hash_code,img_md5))
                            else:
                                imgs_linked += 1

                                if self.bin_by_session_output_folder:
                                    session_path = os.path.join(self.bin_by_session_output_folder,'session_' + str(row[0]))
                                    session_csv = os.path.join(self.bin_by_session_output_folder,'session_' + str(row[0]) + '.csv')
                                    is_new_csv = not os.path.exists(session_csv)

                                    if not os.path.exists(session_path):
                                        os.makedirs(session_path)

                                    img_filename_relative_root = img_filename.replace(self.input_folder, '', 1).lstrip('\\')
                                    dest = os.path.join(session_path, img_filename_relative_root)

                                    if not os.path.exists(os.path.dirname(dest)):
                                        os.makedirs(os.path.dirname(dest))

                                    shutil.copy(img_filename, dest)
                                    # img_filename = img_filename_relative_root

                                    with open(session_csv, 'a+', encoding='utf-8', newline='\n') as session_csvfile:
                                        session_csvwriter = csv.writer(session_csvfile)

                                        if is_new_csv:
                                            session_csvwriter.writerow(['session_id','image_id','cam_id','x','y','z','p','t','img_fname','img_md5','exif_timestamp','time_buff'])  

                                        file_path = os.path.join('session_' + str(row[0]), img_filename_relative_root)
                                        session_csvwriter.writerow(row[0:8] + (file_path, hash_code, str(image_t), str(buffer_sec)))

                                if self.save_to_db:
                                    sql = f'UPDATE image_metadata SET {md5_param} = ?, {fname_param} = ? where id = ?;'
                                    val = (hash_code,img_filename,image_id)
                                    cur.execute(sql, val)

                            csvwriter.writerow(row[0:8] + (img_filename,hash_code,str(image_t), str(buffer_sec)))
                print(str(imgs_linked), ' ', str(ftype), '(s) linked')
            print('max time buffer: ', str(max_buf_used), ' seconds.')
        self._db.commit()
        cur.close()
        self._db.close()


def show_help():
    """Displays the help guide."""
    print('pose_img_linker.py -i <input images folder> -p <copis ini or json profile> -d <sys db file> -o <output csv file> [options]')
    print('-b <buffer time in sec> default: 5')
    print('-f <img file type 1> default: .jpg')
    print('-e <img file type 2> default: None')
    print('-s <update database> default: False')
    print('-c <folder name to copy images organized by session id> default: None')
    print('-t <comma delimited array of time diferential to apply to exif data> default: None')
    print('    format: camid:timediff_sec,camid2:timdiff_sec2...')
    print('    useful if a camera\'s time is set incorrectly.')
    sys.exit()


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:o:p:d:h:b:f:e:t:c:s')
    except getopt.GetoptError as err:
        print(err)
        print('invalid args, for help: pose_img_linker.py -h')
        sys.exit(2)

    pil = PoseImgLinker()

    #pil.profile =  'profiles\\ypm_three.json'
    #pil.dbfile = 'C:\\Users\\nelson\\Desktop\\olivia_multiple_labels_new\\copis.db'
    #pil.input_folder = 'C:\\Users\\nelson\\Desktop\\olivia_multiple_labels_new'
    #pil.output_csv = 'C:\\Users\\nelson\\Desktop\\olivia_multiple_labels_new\\test2.csv'
    #pil.bin_by_session_output_folder = 'C:\\Users\\nelson\\Desktop\\olivia_multiple_labels_new_binned'
    #pil.img_types[2] = '.cr2'
    #pil.save_to_db = False

    if len(opts) == 0:
        show_help()

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
        elif opt == '-c':
            pil.bin_by_session_output_folder = arg
        elif opt == '-h':
            show_help()
        else:
            raise ValueError('unhandled option')

    pil.run()
