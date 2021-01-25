from ctypes import *
from time import sleep
import os
from enum import *
import datetime
import serial
import serial.tools.list_ports
import random
import math
import decimal
ser = serial.Serial()
import EDSDKLib
import pythoncom

#If 32 bit Cannon UPNP app is loaded, EDSK will crash.

#import win32event
#import pythoncom

def getPanTiltAnglesToCenterPoint(cX, cY, cZ, x, y, z):
    p_theta = math.atan2((cX - x), (cY - y)); #now calculate angle of camera poitning back to center
    p = round(math.degrees(p_theta), 2)
    dx = cX - x;
    dy = cY - y;
    dz = cZ - z;
    t_theta = math.atan2(dz, math.sqrt(dx * dx + dy * dy));
    t = round(math.degrees(t_theta), 2);
    return p,t
def move_pointCamtoCenter(x,y,z):
    p, t = getPanTiltAnglesToCenterPoint(0, 0, 0, x, y, z);
    f = 1000
    cmd = "G0X" + str(x) + "Y" + str(y) + "Z" + str(z) + "P" + str(p) + "T" + str(t) + "F" + str(f) + "\r"
    ser.write(cmd.encode())


def generateRandom(minX,maxX,minY,maxY,minZ,maxZ, numImages):
    pointsXYZPT = []
    for i in range(0,10):
        x = random.randint(minX,maxX)
        y = random.randint(minY,maxY)
        z = random.randint(minZ,maxZ)
        #p = random.randint(minP,maxP)
        #t = random.randint(minT,maxT)
        p, t = getPanTiltAnglesToCenterPoint(0, 0, -230, x, y, z);
        pointsXYZPT.append([x,y,z,p,t])
    return pointsXYZPT
def randomizer():
    counter = 0
    cmd = "G0X0Z0P0T0F1000\r"
    print(cmd)
    ser.write(cmd.encode())
    doZ = False
    a = 180
    for k in range(0,10):
        for i in range(0,10):
            print(ser.read_all())
            x = random.randint(-150,150)
            y = random.randint(-150,150)
            p = random.randint(-90,90)
            t = random.randint(-90,90)
            if not doZ:
                f = random.randint(1000,2000)
                cmd = "G0X" + str(x) + "Y" + str(y) + "P" + str(p) + "T" + str(t) + "F" + str(f) + "\r"
                cmd2 = "G0X0Y0P0T0F1000\r"
            else:
                z = random.randint(-150,150)
                f = 1000
                cmd = "G0X" + str(x) + "Y" + str(y) + "Z" + str(z) + "P" + str(p) + "T" + str(t) + "F" + str(f) + "\r"
                cmd2 = "G0X0Y0Z0P0T0F1000\r"
            ser.write(cmd.encode())
            doZ = not doZ
            sleep(5)
        ser.write(cmd2.encode())
        input("Press Enter for next batch.")
    input("Press Enter to quit...")

def float_range(start, stop, step):
  while start < stop:
    yield float(start)
    start = start + float(step)

def generateCylinderPositions(cX, cY, r, cNumPoints, Zmin, Zmax, Zstep, cZ = None):
    pointsXYZPT = []
    for z in float_range(Zmin,Zmax + Zstep ,Zstep):
        pointsXYZPT.extend(generateCircularPositions(cX,cY,r,cNumPoints,z=z, cZ=cZ))
    return pointsXYZPT

def generateCircularPositions(cX, cY, r, cNumPoints, cZ = None, z=None, t=None):
    pointsXYZPT = []
    for i in range(0,cNumPoints):
        c_theta = i * ((2 * math.pi) / cNumPoints)
        x = round(float(cX + (r * math.sin(c_theta))), 2);
        y = round(float(cY + (r * math.cos(c_theta))),2);
        p_theta = math.atan2((cX - x), (cY - y)) #now calculate angle of camera pointing back to cente
        p = round(math.degrees(p_theta), 2)
        if cZ != None:
            dx = cX - x
            dy = cY - y
            if z == None:
                dz = 0
            else:
                dz = cZ - z
            t_theta = math.atan2(dz, math.sqrt(dx * dx + dy * dy))
            t = round(math.degrees(t_theta), 2);
        pointsXYZPT.append([x,y,z,p,t])
    return pointsXYZPT


def generateTurnTableMovements(degree_Increment, arcSize=360):
    pointsXYZPT = []
    p = 0
    while p <= arcSize and p < 360:
        pointXYZPT = [0,0,0,p,0]
        pointsXYZPT.append(pointXYZPT)
        p = p + degree_Increment
    return pointsXYZPT


def generateSphericalPositions(cX, cY,cZ, r, cNumPoints):
    pointsXYZPT = []
    for i in range(0,cNumPoints):
        c_theta = i * ((2 * math.pi) / cNumPoints)
        for k in range(0,cNumPoints):
            # see http://stackoverflow.com/questions/12229950/the-x-angle-between-two-3d-vectors
            c_theta2 = k * ((2 * math.pi) / cNumPoints)
            x = round((r * math.sin(c_theta2) * math.sin(c_theta)), 2)
            y = round((r * math.cos(c_theta2) * math.sin(c_theta)), 2)
            z = round((r * math.cos(c_theta)), 2)
            p_theta = math.atan2((cX - x), (cY - y)) #now calculate angle of camera pointing back to cente
            p = round(math.degrees(p_theta), 2)
            dx = cX - x
            dy = cY - y
            dz = cZ - z
            #alt = toDegrees(atan2(y, sqrt(x*x + z*z)))
            t_theta = math.atan2(dz, math.sqrt(dx * dx + dy * dy))
            t = round(math.degrees(t_theta), 2);
            #do not add location if duplicate of previous location ie. poles)
            #since we start at poles and make circles in xy plane as we move to bottonm poles, polar locations will have a sequential set of repeats
            pointXYZPT = [x,y,z,p,t]
            if pointXYZPT not in pointsXYZPT:
                pointsXYZPT.append(pointXYZPT)
    return pointsXYZPT

def dumpPly(pointsXYZPT):
    print(pointsXYZPT)
    f = open("debug.ply", "w")
    f.write("ply\nformat ascii 1.0\nelement vertex " + str(len(pointsXYZPT)) + "\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nelement face 0\nproperty list uchar int vertex_index\nend_header\n");
    for pt in pointsXYZPT:
        x,y,z = pt[0:3]
        if x == None:
            x = 0
        if y == None:
            y = 0
        if z == None:
            z = 0
        f.write(str(x))
        f.write(' ')
        f.write(str(y))
        f.write(' ')
        f.write(str(z))
        f.write(' 100 100 100 \n') #RGB values for pt
    f.close()



def runPoints(pointsXYZPT, f = 900, shutter=True, delay_sec = 0, useEDSDK=True, focalPlanes=1, stepSize=2):
    if shutter:
        if useEDSDK:
            directory = "images\\" + now.isoformat()[:-7].replace(':', '-') + "\\"
            if not os.path.exists(directory):
                os.makedirs(directory)
    counter = 0
    global WaitingForImage
    z = pointsXYZPT[0][2]
    for pointXYZPT in pointsXYZPT:
        if z != None and pointXYZPT[2] != None:
            dz = abs(pointXYZPT[2]-z)
            if dz > 3:
                f = 1000
        z = pointXYZPT[2]
        cmd = generateCMD(pointXYZPT,f)
        print(cmd)
        ser.write(cmd.encode())
        if shutter:
            if useEDSDK:
                outputfile = 'XYZPT_' + '_'.join(map(str, pointXYZPT))
                sleep(.5)
                if focalPlanes == 1:
                    outputfile = os.path.join(directory, ('0_' + outputfile +'.jpg'))
                    SnapPhoto_EDSDK(outputfile)
                    print(outputfile)
                    while WaitingForImage:
                        pass
                else:
                    for k in range(0,focalPlanes):
                        f = os.path.join(directory, (str(k) + '_' + outputfile +'.jpg'))
                        SnapPhoto_EDSDK(f)
                        while WaitingForImage:
                            pass
                        print(f)
                        StepFocus_EDSDK(stepSize)
                    for k in range(0,focalPlanes): #return focus
                        StepFocus_EDSDK(-(stepSize))
                sleep(.5)
            else:
                cmd = "G4P750\r"
                ser.write(cmd.encode())
                cmd = "C0P1000\r"
                ser.write(cmd.encode())
                cmd="G4P750\r"
                ser.write(cmd.encode())

        if delay_sec > 0:
            sleep(delay_sec) #ensure we don't overun any serial buffers -> for dev only




def generateCMD(pointXYZPT, f):
    x,y,z,p,t = '','','','',''
    if pointXYZPT[0] != None:
        x = "X" + str(pointXYZPT[0])
    if pointXYZPT[1]  != None:
        y = "Y" + str(pointXYZPT[1])
    if pointXYZPT[2]  != None:
        z = "Z" + str(pointXYZPT[2])
    if pointXYZPT[3]  != None:
        p = "P" + str(pointXYZPT[3])
    if pointXYZPT[4]  != None:
        t = "T" + str(pointXYZPT[4])
    if f  != None:
        f = "F" + str(f)
    return "G0" + x + y + z + p + t + f + "\r"

def SnapPhoto_EDSDK(outputFile):
    global WaitingForImage
    global camref
    global ImageFilename
    ImageFilename = outputFile
    WaitingForImage = True
    _edsdk.EdsSendCommand(camref, 0, 0)
    #_edsdk.EdsSendCommand(camref, 4, EDSDKLib.EdsShutterButton.CameraCommand_ShutterButton_Completely.value)
    #_edsdk.EdsSendCommand(camref, 4, EDSDKLib.EdsShutterButton.CameraCommand_ShutterButton_OFF.value)
    while WaitingForImage:
        pythoncom.PumpWaitingMessages()
    sleep(.5)

def StepFocus_EDSDK(stepSizeDir):
    global camref
    if stepSizeDir > 0 and stepSizeDir < 4:
        if stepSizeDir == 1:
            param = _edsdk.EvfDriveLens_Far1
        elif stepSizeDir == 2:
            param = _edsdk.EvfDriveLens_Far2
        elif stepSizeDir == 3:
            param = _edsdk.EvfDriveLens_Far3
    elif stepSizeDir < 0 and stepSizeDir > -4:
        if stepSizeDir == -1:
            param = _edsdk.EvfDriveLens_Near1
        elif stepSizeDir == -2:
            param = _edsdk.EvfDriveLens_Near2
        elif stepSizeDir == -3:
            param = _edsdk.EvfDriveLens_Near3
    else:
        return
    _edsdk.EdsSendCommand(camref, _edsdk.CameraCommand_DriveLensEvf, param)
    #pythoncom.PumpWaitingMessages()
    sleep(.5)

def _generate_file_name():
    global ImageFolder
    global ImagePrefix
    global ImageIndex
    #now = datetime.datetime.now()
    #file_name = ImageFolder + "IMG_" + now.isoformat()[:-7].replace(':', '-') + ".jpg"
    if (ImageFolder) and (not os.path.isdir(ImageFolder)):
        os.mkdir(ImageFolder)
    #if !os .path.isdir(ImageFolder):

    file_name = ImageFolder + ImagePrefix + str(ImageIndex)  + ".jpg"
    ImageIndex =  ImageIndex +1;
    return file_name

def _download_image(image):
    try:
        global ImageFilename
        dir_info = _edsdk.EdsGetDirectoryItemInfo(image)
        #file_name = _generate_file_name()
        #ImageFilename =  file_name
        stream = _edsdk.EdsCreateFileStream(ImageFilename, 1, 2)
        _edsdk.EdsDownload(image, dir_info.size, stream)
        _edsdk.EdsDownloadComplete(image)
        _edsdk.EdsRelease(stream)
        #print("Image is saved as " + file_name + ".")
        global WaitingForImage
        WaitingForImage = False
    except Exception as e:
        print("An exception occurred while downloading an image: " + e.args[0])

ObjectHandlerType = WINFUNCTYPE(c_int,c_int,c_void_p,c_void_p)
def _handle_object(event, object, context):
    #print('object handler called')
    if event == _edsdk.ObjectEvent_DirItemRequestTransfer or event == _edsdk.ObjectEvent_DirItemRequestTransferDT :
        _download_image(object)
    return 0
object_handler = ObjectHandlerType(_handle_object)

PropertyHandlerType = WINFUNCTYPE(c_int,c_int,c_int,c_int,c_void_p)
def _handle_property(event, property, param, context):
    #print('property handler called')
    return 0
property_handler = PropertyHandlerType(_handle_property)

StateHandlerType = WINFUNCTYPE(c_int,c_int,c_int,c_void_p)
def _handle_state(event, state, context):
    #print('state handler called')
    if event == _edsdk.StateEvent_WillSoonShutDown:
        try:
            _edsdk.EdsSendCommand(context, 1, 0)
        except Exception as e:
            print("An exception occurred while handling the state change event: " + e.args[0])
    return 0
state_handler = StateHandlerType(_handle_state)

WaitingForImage = False
ImageFilename = None
ImageFolder = ""
ImageIndex = 0
ImagePrefix = ""
camref = None

if __name__ == "__main__":
    _edsdk = EDSDKLib.EDSDK()
    _edsdk.EdsInitializeSDK()
    pythoncom.CoInitialize()
    c_cam_list = c_void_p(None)
    c_cam_list = _edsdk.EdsGetCameraList()
    numCams = _edsdk.EdsGetChildCount(c_cam_list)
    print(numCams, "camera(s) detected")
    if numCams > 0:
        c = 0
        if numCams > 1:
            c = int(input("select a camera index: "))
        camref = _edsdk.EdsGetChildAtIndex(c_cam_list, c)
        _edsdk.EdsRelease(c_cam_list)
        _edsdk.EdsOpenSession(camref)
        _edsdk.EdsSetPropertyData(camref, _edsdk.PropID_SaveTo, 0, 4, EDSDKLib.EdsSaveTo.Host.value)
        _edsdk.EdsSetCapacity(camref,  EDSDKLib.EdsCapacity(10000000,512,1))
        _edsdk.EdsSetObjectEventHandler(camref, _edsdk.ObjectEvent_All, object_handler, None)
        _edsdk.EdsSetPropertyEventHandler(camref, _edsdk.PropertyEvent_All, property_handler, camref)
        _edsdk.EdsSetCameraStateEventHandler(camref, _edsdk.StateEvent_All, state_handler, camref)
        _edsdk.EdsSetPropertyData(camref, _edsdk.PropID_Evf_OutputDevice, 0, sizeof(c_uint), _edsdk.EvfOutputDevice_TFT)

    ports = serial.tools.list_ports.comports()
    for i in range(0, len(ports)):
        print('[' + str(i) + ']',ports[i].device, ports[i].description)
    i = input("select a port: ")
    if i != 'q' and i != '':
        ser = serial.Serial(ports[int(i)].device, 115200, timeout=1)  # open serial port
        while True:
            while ser.in_waiting > 0:
                ser_bytes = ser.readline()
                print(ser_bytes)
            cmd = input("Enter CMD (# to list): ").upper()
            now = datetime.datetime.now()
            ImageFolder = ""
            ImagePrefix = "IMG_" + now.isoformat()[:-7].replace(':', '-') + "_"
            if cmd.startswith('#'):
                if cmd == '#':
                    print("#CENTER")
                    print("#SPHERE")
                    print("#RANDOM")
                    print("#CIRCLE")
                    print("#CYLINDER")
                    print("#TURNTABLE")
                    print("#STEP")
                    print("#QUIT")
                elif cmd == '#CENTER':
                    runPoints([[0,0,0,0,0]],shutter=False)
                elif cmd == '#SPHERE':
                        r = float(input('Enter Radius: '))
                        n = int(input('Enter Number of  Images at Equator: '))
                        pointsXYZPT = generateSphericalPositions(0,0,0,r,n)
                        dumpPly(pointsXYZPT)
                        runPoints(pointsXYZPT)
                elif cmd == '#RANDOM':
                    minX = float(input('minX: '))
                    maxX = float(input('maxX: '))
                    minY = float(input('minY: '))
                    maxY = float(input('maxY: '))
                    minZ = float(input('minZ: '))
                    maxZ = float(input('maxZ: '))
                    n = int(input('Enter Number of  Images: '))
                    pointsXYZPT = generateRandom(minX,maxX,minY,maxY,minZ,maxZ, n)
                    dumpPly(pointsXYZPT)
                    runPoints(pointsXYZPT, f = 2400)
                elif cmd == '#CIRCLE':
                    r = float(input('Enter Radius: '))
                    n = int(input('Enter Number of  Images: '))

                    pointsXYZPT = generateCircularPositions(0,0,r,n, cZ=-230, z=-100)
                    dumpPly(pointsXYZPT)
                    runPoints(pointsXYZPT,f=2000)
                elif cmd == '#CYLINDER':
                    r = float(input('Enter Radius: '))
                    n = int(input('Enter Number of  Images at each Z: '))
                    zmin = float(input('Enter min Z: '))
                    zmax = float(input('Enter max Z: '))
                    zstep = float(input('Enter Z step: '))
                    pointsXYZPT = generateCylinderPositions(0,0,r,n,zmin,zmax,zstep, cZ=-230)
                    dumpPly(pointsXYZPT)
                    runPoints(pointsXYZPT, f=2000)
                elif cmd == '#TURNTABLE':
                    ImageFolder = "TT_" + now.isoformat()[:-7].replace(':', '-') + "\\"
                    ImagePrefix = ""
                    n = int(input('Enter Degree Increment: '))
                    d = int(input('Enter Arc Size (Degrees): '))
                    s = int(input('Enter Delay Per Shot (Secs): ')) #3
                    ss = int(input('Enter Focal Step Size (+/-) 1 to 3): ')) #2
                    nfp = int(input('Enter No. Focal Planes: ')) #10
                    pointsXYZPT = generateTurnTableMovements(n, arcSize=d)
                    runPoints(pointsXYZPT, delay_sec=s, stepSize=ss, focalPlanes=nfp)
                elif cmd == '#SNAP':
                    SnapPhoto_EDSDK("IMG_" + now.isoformat()[:-7].replace(':', '-') + ".jpg")
                elif cmd == '#STEP':
                    ss = int(input('Enter Focal Step Size (+/-) 1 to 3): ')) #2
                    nfp = int(input('Enter No. Focal Planes: ')) #10
                    outputFile = "IMG_" + now.isoformat()[:-7].replace(':', '-') + ".jpg"
                    for k in range(0,nfp):
                        SnapPhoto_EDSDK(str(k) + "_" + outputFile)
                        StepFocus_EDSDK(ss)
                    for k in range(0,nfp): #return focus
                        StepFocus_EDSDK(-(ss))
                        sleep(1)

                elif cmd == '#QUIT':
                    break
            else:
                ser.write(cmd.encode())
        ser.close()
    if camref != None:
        _edsdk.EdsCloseSession(camref)
        _edsdk.EdsRelease(camref)
        _edsdk.EdsTerminateSDK()