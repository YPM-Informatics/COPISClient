
import sys
import csv
import os
import getopt
from PIL import Image, ImageDraw, ImageFont


search_root = None 
output_folder = None 
grid_width = 5
grid_height = 5
crop_w = 3750
crop_h = 2500
frame_w =1500
frame_h =1000
font_size = 65
resume = False

def compress(input_folder):
    for f in os.listdir(input_folder):
         if f.endswith(".jpg"):
            p = os.path.join(input_folder, f)
            img = Image.open(p)
            img_w, img_h = img.size
            img.thumbnail((img_w/2,img_h/2), Image.ANTIALIAS)
            img.save(p, 'JPEG', quality=80)
            print(p)

def compose():
    
    session_files = []
    past_sessions = []
    
    if resume:
        for f in os.listdir(output_folder):
            if f.startswith("session_") and f.endswith(".jpg"):
                past_sessions.append(f.replace(".jpg",""))

    for path, subdirs, files in os.walk(search_root):
        for f in files:
            if f.startswith("session_") and f.endswith(".csv"):
                if (f.replace(".csv","") not in past_sessions):
                    session_files.append(os.path.join(path, f))
                    print(os.path.join(path, f))

    for session_csv in session_files:
        session_root = os.path.split(session_csv)[0]
        output_fname = os.path.join(output_folder, os.path.split(session_csv)[1].replace('.csv','.jpg'))
        output_fname_80 = os.path.join(output_folder, ("r80_" + os.path.split(session_csv)[1].replace('.csv','.jpg')))
        composite = Image.new('RGB', (grid_width * frame_w , grid_height * frame_h), (255, 255, 255, 255))
        composite_w, composite_h = composite.size
        with open(session_csv, "r") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            row = 0
            col = 0
            for lines in csv_reader:
                if row == grid_height:
                    break;
                img_fname = os.path.join(session_root,lines['img_fname']) 
                meta = 'X:'+ str(lines['x']) +'; Y:'+ str(lines['y']) + '; Z:' + str(lines['z']) + '\nP:'+ str(lines['p']) + '; T:' + str(lines['t']) + '\nCam:'+ str(lines['cam_id'])
                print(img_fname)
                img = Image.open(img_fname)
                img_w, img_h = img.size
                img_mid_w = img_w/2
                img_mid_h = img_h/2
                crop_left = img_mid_w - crop_w/2
                crop_top = img_mid_h - crop_h/2
                crop_right = img_mid_w + crop_w/2
                crop_bottom = img_mid_h + crop_h/2
                img = img.crop((crop_left,crop_top,crop_right,crop_bottom))
                img.thumbnail((frame_w, frame_h), Image.ANTIALIAS)
                img_draw = ImageDraw.Draw(img)
           
                img_draw.text((0, 0), meta, fill=(255, 127, 0), font=ImageFont.truetype('arial.ttf', font_size), stroke_width=1, stroke_fill='black')
                offset = (col * frame_w, row* frame_h) 
                composite.paste(img, offset)
            
                if col == grid_width -1:
                    col = 0
                    row = row+1
                else:
                    col = col+1
        composite.save(output_fname, 'JPEG', quality=100)
        composite.save(output_fname_80, 'JPEG', quality=80)



def show_help():
    """Displays the help guide."""
    print('compose.py -i <root session folder> -o <output folder> [options]')
    print('-r <number of rows composed> default: 5')
    print('-c <number of columns composed> default: 5')
    print('-w <width of center region to crop out> default: 3750')
    print('-h <height of center region to crop out> default: 2500')
    print('-x <width of single frame element> default: 1500')
    print('-y <height of single frame to element> default: 1000')
    print('-f <font size> default: 65')
    print('-t resumes a previous run') 
    

if __name__ == "__main__":
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:o:r:c:w:h:x:y:f:t')
    except getopt.GetoptError as err:
        print(err)
        show_help()
        sys.exit()
    
    for opt, arg in opts:
        if opt == '-i':
            search_root = arg
        elif opt == '-o':
            output_folder = arg
        elif opt == '-r':
            grid_height = int(arg)
        elif opt == '-c':
            grid_width = int(arg)
        elif opt == '-w':
            crop_w = int(arg)
        elif opt == '-h':
            crop_h =int(arg)
        elif opt == '-x':
            frame_w = int(arg)
        elif opt == '-y':
            frame_h =int(arg)
        elif opt == '-f':
            font_size = int(arg)
        elif opt == '-t':
            resume = True
        else:
            print('unhandled option')
            show_help()
            sys.exit()

    if search_root is None or output_folder is None:
        show_help()
        sys.exit()
    
    compose()
