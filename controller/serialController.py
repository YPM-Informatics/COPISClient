import serial
from serial.tools import list_ports

class SerialController(object):
    def __init__(self):
        super(SerialController, self).__init__()
        self.selected_serial = None
        self.ports = self.getPorts()
        self.bauds = []

    def getPorts(self):
        ports = []

        for n, (portname, desc, hwind) in enumerate(sorted(list_ports.comports())):
            ports.append(portname)
        return ports

    def getBaudRates(self):
        if self.selected_serial:
            standard = [9600, 19200, 38400, 57600, 115200]
            return standard[:standard.index(self.selected_serial.baudrate) + 1]

    def setCurrentSerial(self, port):
        self.selected_serial = serial.Serial(port)
        self.bauds = self.getBaudRates()

