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


import datetime
from operator import truediv
from optparse import Option
from pickle import LIST
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
import copy 
import time
from itertools import groupby
from math import cos, e, sin
from configparser import ConfigParser
from tkinter import filedialog
from exif import Image
from typing import List, Dict, Optional, OrderedDict, Union

_SCIENTIFIC_NOTATION_PATTERN = re.compile(r'[-+]?[\d]+\.?[\d]*[Ee](?:[-+]?[\d]+)?')


def _parse_gcode(gc_str : str) -> OrderedDict:
    result = OrderedDict()
    parsed_data = []
    decimal_found = False  # Track if we've already encountered a decimal point in the number
    num_str = ""  # To accumulate consecutive digits
    gc = ''
    for char in gc_str:
        if char.isdigit() or (len(num_str) == 0 and char == '-'):
            num_str += char  # Accumulate digits
        elif char == "." and not decimal_found:  # Check for decimal point
            num_str += char
            decimal_found = True  # Mark that we've found a decimal point
        else:
            if num_str:  # If we have accumulated digits
                value = float(num_str) if decimal_found else int(num_str)  # Convert to float or int
                parsed_data.append(value)
                result[gc] = value
                num_str = ""  # Reset for the next number
                decimal_found = False  # Reset decimal point tracker
            parsed_data.append(char.upper())  # Append the non-digit character
            gc = char
            result[gc] = None 

    # If the string ends with numbers, append the last accumulated number
    if num_str:
        value = float(num_str) if decimal_found else int(num_str)
        parsed_data.append(value)
        result[gc] = value
    return result

def _hash_file(filename):
    hash_md5 = hashlib.md5()

    with open(filename, "rb") as file:
        chunk = 0

        while chunk != b'':
            chunk = file.read(2 ** 20)
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


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


class COPIS_Image_Stack ():
    def __init__ (self, step_size, step_count):
        self.step_size = step_size
        self.step_count = step_count
        self.image_count =  step_count + 1
        self.step_position = 0  #position of image in stack ) is first image that hasn't moved. Final image should have value of step_count 
        
        


class COPIS_DB_Entry:
    def __init__ (self, db_row : list):
        self.session_id = db_row[0]
        self.id : Union[int, float] = db_row[1]
        self.cam_id = db_row[2]
        self.x = db_row[3]
        self.y = db_row[4]
        self.z = db_row[5]
        self.p = db_row[6]
        self.t = db_row[7]
        #self.{md5_param} = db_row[8]
        self.unix_time_start = db_row[9]
        self.unix_time_end = db_row[10]
        self.group_id = db_row[11]
        self.src = db_row[12]
        self.src_action = db_row[13]
        self.cam_name = db_row[14]
        self.cam_type = db_row[15]
        self.cam_desc = db_row[16]
        self.match_delta = None
        self.buffer_sec = None
        self.is_stack = False
        
        self.image_stack : COPIS_Image_Stack = None
        self._check_stack_params()

        
    def _check_stack_params(self):
        step_size = None
        step_count = None
        gcode =  _parse_gcode(self.src_action)
        if 'C' in gcode and gcode['C'] == 10:
            if 'Z' in gcode:
                step_size = gcode['Z']
            if 'V' in gcode:
                step_count = int(gcode['V'])
            self.group_id = self.id
            self.is_stack = True
            self.image_stack =  COPIS_Image_Stack(step_size,step_count)
            self.group_id = self.id
            
    def set_step_pos(self, step_pos : int):
        if self.image_stack and step_pos > 0:
            self.buffer_sec = None
            self.id = self.id + step_pos / 1000 #max stack size of 1000
            self.image_stack.step_position =  step_pos            
            x, y, z = _get_end_position((self.x, self.y, self.z, self.p, self.t), self.image_stack.step_size * self.image_stack.step_position)
            self.x = x
            self.y = y
            self.z = z
          


class COPIS_Image:
    def __init__ (self, img_filename : str, compute_hash=True):
        self.img_filename = img_filename
        self.base_name, self.file_type = os.path.splitext(img_filename)
        if compute_hash:
            self.hash_code = _hash_file(img_filename)
        else:
            self.hash_code = ''
        self.image_t, self.cam_sn = self._get_img_metadata(img_filename)
        self.cam_id = None
        self.db_matches: List[COPIS_DB_Entry] = []
        
    def __repr__(self):
        return f"File(f_type='{self.img_filename}', cam_id={self.cam_id}, timestamp='{self.image_t}')"
        
    def _get_img_metadata(self, img_filename):
        base = os.path.splitext(img_filename)[0]
        image_t = 0 
        cam_sn = None 

        if os.path.splitext(img_filename)[1].lower() in ('.jpg', 'jpeg'):
            # Exif data has three option for date time: datetime, datetime_original, datetime_digitized.
            # We will default to using datetime_digitized.
            with open(img_filename, 'rb') as image_file:
                my_image = Image(image_file)

            image_t = time.mktime(time.strptime(my_image.datetime_digitized, '%Y:%m:%d %H:%M:%S'))
            # body_serial_number camera_owner_name lens_serial_number
            cam_sn = my_image.body_serial_number
        else:
            jpg = None
            for j in ['.jpg','.jpeg','.JPG','.JPEG']:
                if os.path.exists(base + j):
                    jpg = base + j
                    break;
            if jpg:
                image_t, cam_sn= self._get_img_metadata(jpg)    
            else:
                with exiftool.ExifToolHelper(executable=self.exif_tool_path) as exif_tool:
                    metadata = exif_tool.get_metadata(img_filename)
                    image_t = time.mktime(time.strptime(metadata[0]["EXIF:CreateDate"], '%Y:%m:%d %H:%M:%S'))
                    cam_sn = str(metadata[0]["EXIF:SerialNumber"])
                    

        # Account for any time differential from improperly set cameras.
        #if cam_id in self.exif_time_diffs:
        #    image_t = image_t + self.exif_time_diffs[cam_id]
        return image_t, cam_sn
        

class PoseImgLinker:
    """Implements the ability to link pose images with their recorded metadata."""
    def __init__ (self):
        self._input_folder = None
        self._json_profile = None
        self._profile = None
        self._dbfile = None
        self._db = None
        self._db_cur = None
        self._output_csv = None
        self._exif_tool_path = None
        self._cam_sn_to_id = {}
        self.max_buffer_secs = 5
        self.img_types = {1:'.jpg', 2:None}
        self.exif_time_diffs = {}
        self.save_to_db = False
        self.dry_run = False
        self.move_files = False
        self.hashing_enabled = True
        self.gen_stack_lists = False
        self.bin_by_img_type = False
        self.bin_by_session_output_folder = None
        self.copis_images: List[COPIS_Image] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._db is not None:
            self._db_cur.close() 
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
        self._db = sqlite3.connect(self._dbfile)
        self._db_cur = self._db.cursor()
        

    @property
    def output_csv(self):
        """Returns the ouptut CSV path."""
        return self._output_csv

    @output_csv.setter
    def output_csv(self, out_path):
        self._output_csv = out_path

    @property
    def exif_tool_path(self):
        """Returns the exif tool executable's path."""
        return self._exif_tool_path

    @exif_tool_path.setter
    def exif_tool_path(self, value):
        self._exif_tool_path = value

    def run(self):
        """Runs the pose image linker."""
        if self._input_folder is None or self._dbfile is None or len(self._cam_sn_to_id) == 0:
            raise Exception('invalid parameters')

        ext = ''
        for e in pil.img_types.values():
            if e is not None:
                ext = ext + e + '; '
        file_transfer = "no destination"
        if pil.bin_by_session_output_folder:
            if pil.move_files:
                file_transfer = "move"
            else:
                file_transfer = "copy"
        if pil.dry_run:
            print(f"{'File transfer:'.ljust(20,' ')}{file_transfer} (dry run)")
        print('COPIS Pose Image Linker')
        print(f"{'Version:'.ljust(20,' ')}0.1.0")
        print(f"{'Timestamp:'.ljust(20,' ')}20240920")
        print(f"{''.ljust(75,'-')}")
        print(f"{'Source:'.ljust(20,' ')}{pil.input_folder}")
        print(f"{'Extensions:'.ljust(20,' ')}{ext}")
        print(f"{'Profile:'.ljust(20,' ')}{pil.profile}")
        print(f"{'Database:'.ljust(20,' ')}{pil.dbfile}")
        print(f"{'Buffer time:'.ljust(20,' ')}{pil.max_buffer_secs} seconds")
        print(f"{'Compute hashes:'.ljust(20,' ')}{pil.hashing_enabled}")
        print(f"{'Destination:'.ljust(20,' ')}{pil.bin_by_session_output_folder}")
        print(f"{'Pose metadata:'.ljust(20,' ')}{pil.output_csv}")
        if (pil.bin_by_session_output_folder):
            s = os.path.join(self.bin_by_session_output_folder, 'session_[session #].csv')
            print(f"{''.ljust(20,' ')}{s}")
        print(f"{'File transfer:'.ljust(20,' ')}{file_transfer}")
        print(f"{'Stacklist files:'.ljust(20,' ')}{pil.gen_stack_lists}")

        print(f"{''.ljust(75,'-')}")
        start_time = time.time()
        print(f"{'Scanning:'.ljust(20,' ')}{pil.input_folder}")
        self._discover()
        print(f"{'Scan complete:'.ljust(20,' ')}{round(time.time()-start_time,4)} seconds.")
        start_time = time.time()
        print(f"{'Validating:'.ljust(20,' ')}{pil.input_folder}")
        poses, sessions, unlinked_images = self._validate()
        print(f"{'Validation complete:'.ljust(20,' ')}{round(time.time()-start_time,4)} seconds.")
        start_time = time.time()
        if not pil.dry_run:
            print(f"{'Writing outputs:'.ljust(20,' ')}")
            start_time = time.time()
            self._serialize(poses, sessions, unlinked_images)
            print(f"{'Outputs complete:'.ljust(20,' ')}{round(time.time()-start_time,4)} seconds.")
    
    def _discover(self):
        self.copis_images = []
        file_type_totals= {}
        for f_type in self.img_types.values():
            file_type_totals[f_type] = 0
            if f_type is not None and f_type != '':
                for root, _, files in os.walk(self._input_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if file_path.lower().endswith(f_type):
                            file_type_totals[f_type] = file_type_totals[f_type] + 1
                            c = COPIS_Image(os.path.join(root, file), pil.hashing_enabled)
                            if c.cam_sn not in self._cam_sn_to_id:
                                print(f"{'|-Camera error:'.ljust(20,' ')}Cam serial #{c.cam_sn} from image not in profile.")
                                self.copis_images.clear()
                                return
                            c.cam_id = self._cam_sn_to_id[c.cam_sn]
                            self.copis_images.append(c)
        self.copis_images.sort(key=lambda c: (c.file_type , c.cam_id, c.image_t))
        for k,v in file_type_totals.items():
            if k is not None:
                print(f"{'|'+k.upper().ljust(20,' ')}{v} images found")
        file_type = None
        cam_id = None
        md5_param = None
        fname_param = None
        session_id = None
        session_entries = []
        new_ftype_cam_session = True
        sequential = False
        i = 0
        while i < len(self.copis_images):
            c = self.copis_images[i]
            if c.file_type != file_type:
                new_ftype_cam_session = True
                file_type = c.file_type
                for key, val in self.img_types.items():
                    if val and c.file_type.lower() == val.lower():
                        num = key
                        md5_param = f'img{num}_md5'
                        fname_param = f'img{num}_fname'
            if c.cam_id != cam_id:
                new_ftype_cam_session = True
                cam_id = c.cam_id
            c.db_matches = self._match_image_to_db(c,md5_param) 
            
            if c.db_matches and session_id != c.db_matches[0].session_id:
                new_ftype_cam_session = True
                session_id = c.db_matches[0].session_id
            if c.db_matches and c.db_matches[0].image_stack:
                print(f"{'|-Processing Stack:'.ljust(20,' ')}{c.db_matches[0].image_stack.image_count} images; {file_type}; session #{session_id}; cam #{cam_id};")
                i_start = i
                i_end = i + c.db_matches[0].image_stack.step_count
                if i_end >= len(self.copis_images):
                    #stack index is outside of available images
                    print(f"{'--Stack error:'.ljust(20,' ')}Stack incompete. stack count exceeds avilable images.")
                    i_end = len(self.copis_images) -1
                i+=1 #we already have the start image so incremet for the next.
                step_pos = 1
                while i <= i_end:
                    self.copis_images[i].db_matches = copy.deepcopy(self.copis_images[i_start].db_matches)
                    self.copis_images[i].db_matches[0].set_step_pos(step_pos)  #adjust xyzpt and stack pointer
                    step_pos+=1
                    i+=1
                continue
            if new_ftype_cam_session:
                print(f"{'|-Processing:'.ljust(20,' ')}{file_type}; session #{session_id}; cam #{cam_id};")
                new_ftype_cam_session = False
                cam_session_entries = self._get_copis_db_session_entries(cam_id, session_id, md5_param)
                session_alignment = False
                if c.db_matches and cam_session_entries[0].id == c.db_matches[0].id: #and c.db_matches[0].match_delta == 0:                    
                    print(f"{'|--Image alignment:'.ljust(20,' ')}session #{session_id}; start image aligned")
                    ftype_cam_session_end_idx = i + len(cam_session_entries) -1
                    if ftype_cam_session_end_idx < len(self.copis_images):
                        last_image_matches = self._match_image_to_db(self.copis_images[ftype_cam_session_end_idx],md5_param)
                        if last_image_matches and last_image_matches[0].id == cam_session_entries[-1].id:
                            session_alignment = True
                            print(f"{'|--Image alignment:'.ljust(20,' ')}session #{session_id}; end image aligned")
                if session_alignment:
                    print(f"{'|--Mode:'.ljust(20,' ')}sequential processing")
                    for w in range(1, len(cam_session_entries)):
                        i += 1
                        self.copis_images[i].db_matches.append(cam_session_entries[w]) # copy.deepcopy(cam_session_entries[w])
                else:
                    print(f"{'|--Mode:'.ljust(20,' ')}exif match processing")
            i += 1;
    
    def _get_copis_db_session_entries(self, cam_id, session_id, md5_param: str) -> List[COPIS_DB_Entry]:
        # We subtract a one-second buffer to the start time.
        buffer_sec = -1
        count = 0
        results = []
        while (count == 0 and buffer_sec <= self.max_buffer_secs):
            buffer_sec += 1
            #sql = (f"select session_id, id, cam_id, x, y, z, p, t, {md5_param}, unix_time_start, unix_time_end, group_id, src, src_action, cam_name, cam_type, cam_desc from image_metadata "
            #    f"where cam_id = ? and ? >= (cast(unix_time_start as int) - {buffer_sec}) and ? <= (cast(unix_time_end as int) + {buffer_sec});")
            #below line uses ceil and floor equivilents for start and end time since cameras limited to second precision
            sql = (f"select session_id, id, cam_id, x, y, z, p, t, {md5_param}, unix_time_start, unix_time_end, group_id, src, src_action, cam_name, cam_type, cam_desc from image_metadata "
                f"where cam_id = ? and session_id = ? order by id;")
            data = self._db_cur.execute(sql, (cam_id, session_id))
            rows = data.fetchall()
            count = len(rows)
            for r in rows:
                e = COPIS_DB_Entry(r) 
                results.append(e)
        return results    

    def _match_image_to_db(self, c: COPIS_Image, md5_param: str) -> List[COPIS_DB_Entry]:
        # Account for any time differential from improperly set cameras.
        if c.cam_id in self.exif_time_diffs:
            image_t = image_t + self.exif_time_diffs[c.cam_id]
        # We subtract a one-second buffer to the start time.
        buffer_sec = -1
        count = 0
        results = []
        while (count == 0 and buffer_sec <= self.max_buffer_secs):
            buffer_sec += 1
            #sql = (f"select session_id, id, cam_id, x, y, z, p, t, {md5_param}, unix_time_start, unix_time_end, group_id, src, src_action, cam_name, cam_type, cam_desc from image_metadata "
            #    f"where cam_id = ? and ? >= (cast(unix_time_start as int) - {buffer_sec}) and ? <= (cast(unix_time_end as int) + {buffer_sec});")
            #below line uses ceil and floor equivilents for start and end time since cameras limited to second precision
            sql = (f"select session_id, id, cam_id, x, y, z, p, t, {md5_param}, unix_time_start, unix_time_end, group_id, src, src_action, cam_name, cam_type, cam_desc from image_metadata "
                f"where cam_id = ? and ? >= (cast(unix_time_start as int) - {buffer_sec}) and ? <= (cast(unix_time_end as int ) + (unix_time_end > cast(unix_time_end as int)) + {buffer_sec});")
            data = self._db_cur.execute(sql, (c.cam_id, c.image_t, c.image_t))
            rows = data.fetchall()
            count = len(rows)
            for r in rows:
                unix_time_start = r[9]
                unix_time_end = r[10]
                match_delta = 0
                if c.image_t < unix_time_start:
                   match_delta =  c.image_t - unix_time_start
                elif c.image_t > unix_time_end:
                   match_delta =  c.image_t - unix_time_end
                e = COPIS_DB_Entry(r) 
                e.match_delta = match_delta
                e.buffer_sec = buffer_sec
                results.append(e)
        if len(results) > 0:
            results.sort(key=lambda x: abs(x.match_delta))
        return results
        
    def _validate(self):
        max_buf_used = 0
        poses = []
        sessions = []
        images_not_linked = []
        pose_metadata_row = []
        image_ids = {}  #used to track db entries that may be assosciated with more than one image
                        #since we assign decimal numbers to stacks, this should work fine
        i = 0
        for c in self.copis_images:
            i +=1
            if  not c.db_matches or len(c.db_matches) < 1:
                images_not_linked.append([c.img_filename, "No timestamp match"])
            elif len(c.db_matches) > 1:
                images_not_linked.append([c.img_filename, f"{len(c.db_matches)} timestamp matches"])
            else:
                pseudo_image_id = f'{c.file_type}:{c.db_matches[0].id}'
                if pseudo_image_id in image_ids:
                    image_ids[pseudo_image_id].append(c.img_filename)
                else:
                    image_ids[pseudo_image_id] = []
                    image_ids[pseudo_image_id].append(c.img_filename)
                    buffer_sec = c.db_matches[0].buffer_sec
                    session_id = c.db_matches[0].session_id
                    unix_time_end =  c.db_matches[0].unix_time_end
                    group_id = c.db_matches[0].group_id
                    buffer_sec_str = "na"
                    if buffer_sec is not None:
                        buffer_sec_str =str(buffer_sec)
                        if c.image_t < unix_time_end:
                            buffer_sec = buffer_sec * -1
                        if max(abs(max_buf_used),abs(buffer_sec)) > abs(max_buf_used):
                            max_buf_used = buffer_sec
                    imgs_linked = 1
                    pose_metadata_row = [c.db_matches[0].session_id, c.db_matches[0].id, c.cam_id, c.db_matches[0].x, c.db_matches[0].y, c.db_matches[0].z, c.db_matches[0].p, c.db_matches[0].t, c.img_filename, c.hash_code, str(c.image_t), buffer_sec_str, group_id]
                    if self.bin_by_session_output_folder:
                        session_row = [c.db_matches[0].session_id, c.db_matches[0].id, c.cam_id, c.db_matches[0].x, c.db_matches[0].y, c.db_matches[0].z, c.db_matches[0].p, c.db_matches[0].t, c.img_filename, c.hash_code, str(c.image_t), buffer_sec_str, group_id]
                        sessions.append(session_row)
                poses.append(pose_metadata_row)
        for image_id, filenames in image_ids.items():
            if len(filenames) > 1:
                for filename in filenames:
                    images_not_linked.append([filename, f"{len(filenames)} images match pose with id {image_id}"]) 
        print(f"{'|-Images linked:'.ljust(20,' ')}{len(poses)}")
        print(f"{'|-Images not linked:'.ljust(20,' ')}{len(images_not_linked)}")
        print(f"{'|-Max time buffer:'.ljust(20,' ')}{max_buf_used}")    
        return poses, sessions, images_not_linked

    def _serialize(self, poses, sessions, images_not_linked):    
        dirpath = os.path.dirname(self.output_csv)
        os.makedirs(dirpath, exist_ok=True)
        if images_not_linked:
              name, ext = os.path.splitext(self.output_csv)
              filename = f"{name}_err.csv"
              with open(filename, 'w', encoding='utf-8', newline='\n') as file:
                csv.writer(file).writerow(['img_fname', 'error'])
                for row in images_not_linked:
                    csv.writer(file).writerow(row)
              print(f"{'|-Issues found:'.ljust(20,' ')}{filename}")
              print(f"{'|'.ljust(20,' ')}Please resolve issues and run again.")
              return
        if poses:
            with open(self.output_csv, 'w', encoding='utf-8', newline='\n') as file:
                csv.writer(file).writerow(['session_id', 'image_id', 'cam_id', 'x', 'y', 'z', 'p', 't', 'img_fname', 'img_md5', 'exif_timestamp', 'time_buff', 'group_id'])
                for row in poses:
                    row[1] = row[1] 
                    csv.writer(file).writerow(row)
                print(f"{'|-Output:'.ljust(20,' ')}{self.output_csv}")
        if sessions:
            get_session_id = lambda r: r[0]
            headers = ['session_id', 'image_id', 'cam_id', 'x', 'y', 'z', 'p', 't', 'img_fname', 'img_md5', 'exif_timestamp', 'time_buff', 'group_id']
            sorted_sessions = sorted(sessions, key=get_session_id)
            groups = groupby(sorted_sessions, get_session_id)
            helicon_cmds = []
            for session_id, session_rows in groups:
                session_path = os.path.join(self.bin_by_session_output_folder, 'session_' + str(session_id))
                session_csv = os.path.join(self.bin_by_session_output_folder, 'session_' + str(session_id) + '.csv')
                if not os.path.exists(session_path):
                    os.makedirs(session_path)
                with open(session_csv, 'w', encoding='utf-8', newline='\n') as file:
                    csv.writer(file).writerow(headers)
                    stack_files = []
                    for row in session_rows:
                        img_filename = row[8]
                        img_filename_relative_root = img_filename.replace(self.input_folder, '', 1).lstrip('\\')
                        type_bin = os.path.splitext(img_filename_relative_root)[1].strip('.').upper() if self.bin_by_img_type else ''
                        dest = os.path.join(session_path, type_bin, img_filename_relative_root)
                        #print(dest)
                        if not os.path.exists(os.path.dirname(dest)):
                            os.makedirs(os.path.dirname(dest))
                        if self.move_files:
                            shutil.move(img_filename, dest)
                        else:
                            shutil.copy(img_filename, dest)
                        row[8] = dest # os.path.join('session_' + str(session_id), type_bin, img_filename_relative_root)
                        row[1] = row[1] 
                        csv.writer(file).writerow(row)
                        if pil.gen_stack_lists: 
                            group_id = row[12]
                            if group_id:
                                stacklist_write_mode = 'at'
                                stack_file = os.path.join(self.bin_by_session_output_folder, f"stack_{str(session_id)}_{group_id}.txt")
                                if stack_file not in stack_files:
                                    stack_files.append(stack_file)
                                    stacklist_write_mode = 'wt'
                                    print(f"{'|-Output:'.ljust(20,' ')}{stack_file}")
                                    type_bin = 'TIF' if self.bin_by_img_type else ''
                                    basename = os.path.splitext(os.path.basename(row[8]))[0]
                                    save_filename = os.path.join(session_path, type_bin, basename + ".tif")
                                    save_arg = "-save:" + save_filename
                                    cmd = ['heliconfocus.exe', "-rp:8", "-sp:4", "-mp:1", "-va:3", "-ha:3", "-ra:0", "-ma:5", "-dmf:3", "-im:1", "-ba:1", "-i", stack_file, save_arg, "-silent" ]
                                    helicon_cmds.append(cmd)
                                with open(stack_file, stacklist_write_mode) as stack_file:
                                    stack_file.write(f'{dest}\n')                        
                    print(f"{'|-Output:'.ljust(20,' ')}{session_csv}")    
            if len(helicon_cmds) > 0:  
                helicon_file = os.path.join(self.bin_by_session_output_folder, f"helicon.bat")
                with open(helicon_file, 'wt') as file:
                    for cmd in helicon_cmds:
                        file.write(f"{' '.join(cmd)}\n")  
                print(f"{'|-Output:'.ljust(20,' ')}{helicon_file}")
                        
                    



def show_help():
    """Displays the help guide."""
    print('pose_img_linker.py -i <input images folder> -p <copis ini or json profile> -d <sys db file> -o <output csv file> [options]')
    print('-b <buffer time in sec> default: 5')
    print('-f <img file type 1> default: .jpg')
    print('-e <img file type 2> default: None')
    print('-l <location of exiftool.exe> default (expects exiftool.exe directory to be on the PATH): None')
    print('-c <folder name to copy images organized by session id> default: None')
    print('-t <comma delimited array of time diferential to apply to exif data> default: None')
    print('    format: camid:timediff_sec,camid2:timdiff_sec2...')
    print('    useful if a camera\'s time is set incorrectly.')
    print('-m <no param> move, instead of copy, files to destination> default: False')
    print('-g <no param> organize images by type with the session> default: False')
    print('-z <no param> generate stack lists and helicon batch file> default: False')
    print('-x <no param> disable hashing> default: Hashing enabled')
    
    sys.exit()


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:o:p:d:h:b:f:e:t:c:l:mgzx')
    except getopt.GetoptError as err:
        print(err)
        print('invalid args, for help: pose_img_linker.py -h')
        sys.exit(2)

    pil = PoseImgLinker()

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
        elif opt == '-m':
            pil.move_files = True
        elif opt == '-g':
            pil.bin_by_img_type = True
        elif opt == '-z':
            pil.gen_stack_lists = True
        elif opt == '-t':
            for a in arg.split(','):
                kv = a.split(':')
                if int(kv[0]) in pil.exif_time_diffs:
                    pil.exif_time_diffs[int(kv[0])] = pil.exif_time_diffs[int(kv[0])] + int(kv[1])
                else:
                    pil.exif_time_diffs[int(kv[0])] = int(kv[1])
        elif opt == '-c':
            pil.bin_by_session_output_folder = arg
        elif opt == '-x':
            pil.hashing_enabled = False
        elif opt == '-h':
            show_help()
        else:
            raise ValueError('unhandled option')

    pil.run()
