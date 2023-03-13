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

import re
import sys
import shutil
import getopt
import time
import sqlite3
import os
import csv
import hashlib
import json
import exiftool
import tkinter as tk

from itertools import groupby
from math import cos, sin
from configparser import ConfigParser
from tkinter import filedialog
from exif import Image


_SCIENTIFIC_NOTATION_PATTERN = re.compile(r'[-+]?[\d]+\.?[\d]*[Ee](?:[-+]?[\d]+)?')


def _hash_file(filename):
    hash_md5 = hashlib.md5()

    with open(filename, "rb") as file:
        chunk = 0

        while chunk != b'':
            chunk = file.read(2 ** 20)
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def _parse_src_action(cmd):
    segments = re.split('([a-zA-Z])', cmd)
    g_code = 0
    a_args = []

    for i, segment in enumerate(segments):
        if len(segment) > 0 and segment.upper() in 'CGM':
            g_code = f'{segment}{segments[i + 1]}'
        elif len(segment) > 0 and segment.upper() in 'XYZPTFSV':
            a_args.append((segment, segments[i + 1]))
    return (g_code, a_args)


def _sanitize_number(value: float) -> float:
    """Sanitizes a number approaching zero:
    signed zero and tiny number at 5 or more decimal places."""
    if _SCIENTIFIC_NOTATION_PATTERN.match(str(value)):
        value = float(f'{value:.4f}')

    return value if value != 0.0 else 0.0


def _get_end_position(start, distance):
    x, y, z, p, t = start
    d_places = 3
    sin_p = round(sin(p), d_places)
    cos_p = round(cos(p), d_places)
    sin_t = round(sin(t), d_places)
    cos_t = round(cos(t), d_places)

    # The right formula for this is:
    #   new_x = x + (dist * sin(pan) * cos(tilt))
    #   new_y = y + (dist * sin(tilt))
    #   new_z = z + (dist * cos(pan) * cos(tilt))
    # But since our axis is rotated 90dd clockwise around the x axis so
    # that z points up we have to adjust the formula accordingly.
    end_x = _sanitize_number(x + (distance * sin_p * cos_t))
    end_y = _sanitize_number(y + (distance * cos_p * cos_t))
    end_z = _sanitize_number(z - (distance * sin_t))

    return (end_x, end_y, end_z)


def _detect_stacks(img_data_item):
    def get_action_arg(key: str, a_args):
        key = key.upper()
        return next(filter(lambda a: a[0].upper() == key, a_args), (key, None))[1]

    d_map = map(lambda d: d['rows'], img_data_item)
    flat = [i for r in d_map for i in r]
    uniq_entries = sorted(list(set(flat)), key=lambda e: e[2])
    uniq_cams = list(set(map(lambda i: i[2], flat)))
    cam_group = {}

    # Detect computed entries and remove then from img_data_item and mark them for db deletion.
    computed = [e[1] for e in list(filter(lambda e: e[1] != e[11], uniq_entries))]

    if len(computed):
        uniq_entries = list(filter(lambda e: e[1] == e[11], uniq_entries))

        for i in img_data_item:
            i['rows'] = [r for r in i['rows'] if r[1] not in computed]

            # Also blank out the hash code.
            for idx in range(len(i['rows'])):
                row = i['rows'][idx]
                i['rows'][idx] = (row[0:8] + (None,) + row[9:])

    if len(uniq_entries) == len(uniq_cams):
        img_data_item = sorted(img_data_item, key=lambda d: d['image_t'])

        for entry in uniq_entries:
            src, src_action = entry[12:14]

            if src_action:
                parsed = _parse_src_action(src_action)
                if parsed[0].upper() == 'C10':
                    step_size = get_action_arg('Z', parsed[1])
                    step_count = get_action_arg('V', parsed[1])

                    if not step_count or not step_size:
                        raise Exception('Missing required stack parameters.')

                    step_size = float(step_size)
                    step_count = int(step_count)

                    entry_count = len(list(filter(lambda d, e=entry: d['rows'][0][2] == e[2], img_data_item)))

                    if entry_count != step_count + 1:
                        raise Exception('Mismatched stack step count vs images discovered.')

                    for item in img_data_item:
                        if len(item['rows']) > 0 and item['rows'][0][2] == entry[2]:
                            cam_id = item['rows'][0][2]
                            group = cam_group.get(cam_id)

                            # Because tuples are immutable, we have to convert them to lists before we can assign to them.
                            item['rows'] = list(map(list, item['rows']))

                            if not group:
                                x, y, z, p, t = item['rows'][0][3:8]
                                unix_time_start, unix_time_end = item['rows'][0][9:11]
                                group_id = item['rows'][0][1]
                                cam_name, cam_type, cam_desc = item['rows'][0][14:17]
                                cam_group[cam_id] = {
                                    'x': x,
                                    'y': y,
                                    'z': z,
                                    'p': p,
                                    't': t,
                                    'unix_time_start': unix_time_start,
                                    'unix_time_end': unix_time_end,
                                    'group_id': group_id,
                                    'cam_name': cam_name,
                                    'cam_type': cam_type,
                                    'cam_desc': cam_desc
                                }
                                item['rows'][0][11] = group_id
                            else:
                                x, y, z, p, t = map(group.get, ('x', 'y', 'z', 'p', 't'))
                                x, y, z = _get_end_position((x, y, z, p, t), step_size)
                                group['x'] = x
                                group['y'] = y
                                group['z'] = z
                                item['rows'][0][1] = None # Null out the entry id so we know it's an insert instead of an update.
                                item['rows'][0][3] = x
                                item['rows'][0][4] = y
                                item['rows'][0][5] = z
                                item['rows'][0][6] = p
                                item['rows'][0][7] = t
                                item['rows'][0][9] = group['unix_time_start']
                                item['rows'][0][10] = group['unix_time_end']
                                item['rows'][0][11] = group['group_id']
                                item['rows'][0][12] = src
                                item['rows'][0][13] = src_action
                                item['rows'][0][14] = group['cam_name']
                                item['rows'][0][15] = group['cam_type']
                                item['rows'][0][16] = group['cam_desc']
    return computed


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
        self._exif_tool_path = None
        self._cam_sn_to_id = {}
        self._bin_by_session = False
        self.max_buffer_secs = 5
        self.img_types = {1:'.jpg', 2:None}
        self.exif_time_diffs = {}
        self.save_to_db = False
        self.bin_by_session_output_folder = None

        self._file_data = {}
        self._db_data = {}

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
        img_data = {}

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

        self._file_data[self.output_csv] = [['session_id','image_id','cam_id','x','y','z','p','t','img_fname','img_md5','exif_timestamp','time_buff']]

        for ftype, lof in dof.items():
            num = 0
            img_data[ftype] = []

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

                image_t = time.mktime(time.strptime(my_image.datetime_digitized, '%Y:%m:%d %H:%M:%S'))
                # body_serial_number camera_owner_name lens_serial_number
                cam_sn = my_image.body_serial_number
                cam_id = self._cam_sn_to_id[cam_sn]

                # Account for any time differential from improperly set cameras.
                if cam_id in self.exif_time_diffs:
                    image_t = image_t + self.exif_time_diffs[cam_id]

                # We subtract a one-second buffer to the start time.
                buffer_sec = -1
                count = 0

                while (count == 0 and buffer_sec <= self.max_buffer_secs):
                    buffer_sec += 1
                    sql = (f"select session_id, id, cam_id, x, y, z, p, t, {md5_param}, unix_time_start, unix_time_end, group_id, src, src_action, cam_name, cam_type, cam_desc from image_metadata "
                        f"where cam_id = ? and ? >= (cast(unix_time_start as int) - {buffer_sec}) and ? <= (cast(unix_time_end as int) + {buffer_sec});")
                    data = cur.execute(sql, (cam_id, image_t, image_t))
                    rows = data.fetchall()
                    count = len(rows)

                img_data[ftype].append({
                    'cam_sn': cam_sn,
                    'md5_param': md5_param,
                    'fname_param': fname_param,
                    'img_filename': img_filename,
                    'hash_code': hash_code,
                    'image_t': image_t,
                    'buffer_sec': buffer_sec,
                    'rows': rows
                })
        cur.close()
        self._db.close()

        self._process_discovered_images(img_data)

    def _process_discovered_images(self, img_data: dict):
        max_buf_used = 0
        poses = []
        sessions = []
        db_updates = []
        db_inserts = []
        db_deletes = []

        for ftype, img_data_item in img_data.items():
            imgs_linked = 0
            deletes = _detect_stacks(img_data_item)

            if self.save_to_db:
                db_deletes.extend(deletes)

            for data in img_data_item:
                print(data.pop('cam_sn'))

                results = self._process_discovered_image(data)

                if results[2]:
                    poses.append(results[2])
                if results[3]:
                    sessions.append(results[3])
                if results[4]:
                    db_updates.append(results[4])
                if results[5]:
                    db_inserts.append(results[5])

                if max(abs(max_buf_used),abs(results[0])) > abs(max_buf_used):
                    max_buf_used = results[0]
                imgs_linked += results[1]
            print(str(imgs_linked), ' ', str(ftype), '(s) linked')
        print('max time buffer: ', str(max_buf_used), ' seconds.')

        self._serialize_results(poses, sessions, db_updates, db_inserts, db_deletes)

    def _serialize_results(self, poses, sessions, db_updates, db_inserts, db_deletes):
        new_img_ids = {}

        if db_deletes or db_updates or db_inserts:
            self._db = sqlite3.connect(self._dbfile)
            cur = self._db.cursor()

        if db_deletes:
            sql = 'DELETE FROM image_metadata where id = ?;'
            cur.executemany(sql, [(d_id,) for d_id in db_deletes])

        if db_updates:
            for update in db_updates:
                keys, params = map(update.get, ('keys', 'params'))
                sql = f'UPDATE image_metadata SET {keys[0]} = ?, {keys[1]} = ?, group_id = ? where id = ?;'
                cur.execute(sql, params)

        if db_inserts:
            for insert in db_inserts:
                keys, params = map(insert.get, ('keys', 'params'))
                sql = f'INSERT INTO image_metadata (session_id, cam_id, x, y, z, p, t, {keys[0]}, {keys[1]}, unix_time_start, unix_time_end, group_id, src, src_action, cam_name, cam_type, cam_desc) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'
                cur.execute(sql, params)

                # Save the new image id with the unique hash code as the key.
                new_img_ids[params[7]] = cur.lastrowid

        if db_updates or db_inserts:
            cur.close()
            self._db.commit()
            self._db.close()

        if poses:
            with open(self.output_csv, 'w', encoding='utf-8', newline='\n') as file:
                csv.writer(file).writerow(['session_id', 'image_id', 'cam_id', 'x', 'y', 'z', 'p', 't', 'img_fname', 'img_md5', 'exif_timestamp', 'time_buff', 'group_id'])

                for row in poses:
                    new_img_id = new_img_ids.get(row[9])
                    # print(f'new img id: {new_img_id}, row[1]: {row[1]}, row: {row}')
                    row[1] = row[1] or new_img_id
                    csv.writer(file).writerow(row)

        if sessions:
            get_session_id = lambda r: r[0]

            headers = ['session_id', 'image_id', 'cam_id', 'x', 'y', 'z', 'p', 't', 'img_fname', 'img_md5', 'exif_timestamp', 'time_buff', 'group_id']
            sorted_sessions = sorted(sessions, key=get_session_id)
            groups = groupby(sorted_sessions, get_session_id)

            for session_id, session_rows in groups:
                session_path = os.path.join(self.bin_by_session_output_folder, 'session_' + str(session_id))
                session_csv = os.path.join(self.bin_by_session_output_folder, 'session_' + str(session_id) + '.csv')

                if not os.path.exists(session_path):
                    os.makedirs(session_path)

                with open(session_csv, 'w', encoding='utf-8', newline='\n') as file:
                    csv.writer(file).writerow(headers)

                    for row in session_rows:
                        img_filename = row[8]
                        img_filename_relative_root = img_filename.replace(self.input_folder, '', 1).lstrip('\\')
                        dest = os.path.join(session_path, img_filename_relative_root)

                        if not os.path.exists(os.path.dirname(dest)):
                            os.makedirs(os.path.dirname(dest))

                        shutil.copy(img_filename, dest)

                        row[8] = os.path.join('session_' + str(session_id), img_filename_relative_root)
                        new_img_id = new_img_ids.get(row[9])
                        row[1] = row[1] or new_img_id
                        csv.writer(file).writerow(row)

    def _process_discovered_image(self, inputs):
        rows = inputs['rows']
        buffer_sec = inputs['buffer_sec']
        img_linked = 0
        pose_metadata_row = None
        session_row = None
        db_update_row = None
        db_insert_row = None

        if len(rows) < 1:
            pose_metadata_row = ['No timestamp match', '', '', '', '', '', '', '', inputs['img_filename'], inputs['hash_code'], str(inputs['image_t']), str(buffer_sec), '']
        elif len(rows) > 1:
            pose_metadata_row = ['>1 timestamp match', '', '', '', '', '', '', '', inputs['img_filename'], inputs['hash_code'], str(inputs['image_t']), str(buffer_sec), '']
        else:
            session_id, image_id, cam_id = rows[0][0:3]
            img_md5 = rows[0][8]
            unix_time_end = rows[0][10]
            group_id = rows[0][11]

            if inputs['image_t'] < unix_time_end:
                buffer_sec = buffer_sec * -1

            if img_md5 not in ('', None, inputs['hash_code']):
                print('houston we have a problem prior sync, with diff hash detected')
                inputs['hash_code'] = ':'.join(('hash conflict', inputs['hash_code'], img_md5))
            else:
                img_linked = 1
                pose_metadata_row = [*rows[0][0:8], inputs['img_filename'], inputs['hash_code'], str(inputs['image_t']), str(buffer_sec), group_id]

                if self.bin_by_session_output_folder:
                    session_row = [*rows[0][0:8], inputs['img_filename'], inputs['hash_code'], str(inputs['image_t']), str(buffer_sec), group_id]
                if self.save_to_db:
                    if image_id:
                        db_update_row = {
                            'keys': (inputs['md5_param'], inputs['fname_param']),
                            'params': (inputs['hash_code'], inputs['img_filename'], group_id, image_id)
                        }
                    else:
                        db_insert_row = {
                            'keys': (inputs['md5_param'], inputs['fname_param']),
                            'params': (session_id, cam_id, *rows[0][3:8], inputs['hash_code'], inputs['img_filename'], *rows[0][9:])
                        }
        return (buffer_sec, img_linked, pose_metadata_row, session_row, db_update_row, db_insert_row)


def show_help():
    """Displays the help guide."""
    print('pose_img_linker.py -i <input images folder> -p <copis ini or json profile> -d <sys db file> -o <output csv file> [options]')
    print('-b <buffer time in sec> default: 5')
    print('-f <img file type 1> default: .jpg')
    print('-e <img file type 2> default: None')
    print('-l <location of exiftool.exe> default (expects exiftool.exe directory to be on the PATH): None')
    print('-s <update database> default: False')
    print('-c <folder name to copy images organized by session id> default: None')
    print('-t <comma delimited array of time diferential to apply to exif data> default: None')
    print('    format: camid:timediff_sec,camid2:timdiff_sec2...')
    print('    useful if a camera\'s time is set incorrectly.')
    sys.exit()


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:o:p:d:h:b:f:e:t:c:l:s')
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
        elif opt == '-l':
            pil.exif_tool_path = arg
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
