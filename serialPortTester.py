import os
import pty
from serial import Serial
import threading

def serial_listener(port):
    while True:
        res = b""
        while not res.endswith(b"\r\n"):
            res += os.read(port, 1)
        print("Command: %s" % res)

        if res == b"QPGS\r\n":
            os.write(port, b"correct result\r\n")
        else:
            os.write(port, b"I don't understand\r\n")


def test_serial():
    master, slave = pty.openpty()
    s_name = os.ttyname(slave)

    thread = threading.Thread(target=serial_listener, args=[master])
    thread.start()

    serial = Serial(s_name, 2400, timeout=1)
    serial.write(b'test2\r\n')
    res = b""

    while not res.endswith(b'\r\n'):
        res += serial.read()
    print("result: %s" % res)
    ser.write(b'QPGS\r\n')
    res = b""

    while not res.endswith(b'\r\n'):
        res += serial.read()
    print("result: %s" % res)

test_serial()