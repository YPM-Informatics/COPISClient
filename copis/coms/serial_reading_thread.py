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
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

"""Provides COPIS Serial Reading Thread"""


import ast
import threading
import time

from serial import Serial

class SerialReadingThread(threading.Thread):
    """Implements the ability to continuously read a serial connection's output"""

    def __init__(self, connection: Serial):
        threading.Thread.__init__(self)
        self._connection = connection
        self._response_stack = []

    def run(self):
        while self._connection.is_open:
            time.sleep(0.001)
            while self._connection.is_open and self._connection.in_waiting:
                p_bytes = self._connection.readline().decode()
                self._parse_output(p_bytes)

                if self._connection.in_waiting == 0:
                    idle_response = \
                        next(filter(lambda r: r['ssf'] == 0, self._response_stack), None)

                    if idle_response is not None:
                        # TODO: broadcast OK.
                        # TODO: fix serial.serialutil.SerialException:
                        # ClearCommError failed (OSError(9, 'The handle is invalid.', None, 6))
                        # that occurs on serial port close.
                        pass

                    self._response_stack.clear()

    def _parse_output(self, data: str) -> None:
        data = data.strip('\r\n')
        if data.startswith('<') and data.endswith('>'):
            data = data.lstrip('<').rstrip('>')

            segments = data.split(',', 2)
            segments = [tuple(s.split(':')) for s in segments]
            mapped = map(_stringify, segments)

            result = '{' + ', '.join(mapped) + '}'

            self._response_stack.append(ast.literal_eval(result))
        else:
            return

def _stringify(data):
    if ',' in data[1]:
        value = '{{"X": {0}, "Y": {1}, "Z": {2}, "P": {3}, "T": {4}}}'.format(*data[1].split(','))
        return f'"{data[0]}": {value}'

    return f'"{data[0]}": {data[1]}'
