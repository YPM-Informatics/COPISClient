"""TODO"""

import serial
from serial.tools import list_ports


class SerialController(object):

    def __init__(self):
        super(SerialController, self).__init__()
        self.selected_serial = None
        self.ports = self.get_ports()
        self.bauds = []

    def get_ports(self):
        ports = []

        for n, (portname, desc, hwind) in enumerate(sorted(list_ports.comports())):
            ports.append(portname)
        return ports

    def get_bauds(self):
        if self.selected_serial:
            standard = [9600, 19200, 38400, 57600, 115200]
            return standard[:standard.index(self.selected_serial.baudrate) + 1]

    def set_current_serial(self, port):
        try:
            self.selected_serial = serial.Serial(port)
            self.selected_serial.close()
            self.bauds = self.get_bauds()
            return True
        except serial.serialutil.SerialException:
            return False
