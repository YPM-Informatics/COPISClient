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

"""Console Command Processor."""

import shlex


class _CommandProcessor:
    """Handles console commands processing and execution.

    Args:
        parent: Pointer to a parent console panel.
    """
    _PROTOCOLS = ['edsdk', 'serial']

    def __init__(self, core, console = None) -> None:
        self._core = core
        self._console = console
        self._protocol = ''

    def process(self, cmd_line: str) -> None:
        """Processes the given command."""
        protocol_prompt = f'<{self._protocol}>' if len(self._protocol) > 0 else ''
        self._print(f'{protocol_prompt}$ {cmd_line}')

        if self._console is not None:
            self._console.on_command_cleared()

        argv = shlex.split(cmd_line)

        if len(argv) < 1:
            self._print('No command provided.')

        self.switch(argv[0], argv[1:])

    # pylint: disable=too-many-statements
    def switch(self, cmd: str, opts) -> None:
        """Switch statement implementation for commands list."""
        def use():
            protocol = '' if len(opts) < 1 else opts[0].lower()
            if len(protocol) < 1 or protocol not in self._PROTOCOLS:
                self._print('No valid protocol provided. Usage: \'use <protocol>\';',
                    ' where <protocol> is \'edsdk\' or \'serial\'.')
                return

            self._protocol = protocol
            self._print(f'Using {self._protocol}.')

        def release():
            if self._protocol == 'edsdk':
                self._core.edsdk.disconnect()
            elif self._protocol == 'serial':
                self._core.serial.terminate()
            self._print(f'Protocol {self._protocol} released.')
            self._protocol = ''

        def connect():
            if self._protocol == '':
                self._print('No protocol to connect with.')
            elif self._protocol == 'edsdk':
                cam_index = '0' if len(opts) < 1 else opts[0]

                if cam_index.isdigit():
                    self._core.edsdk.connect(int(cam_index))
                    self._protocol(f'Connected to camera {cam_index}')
                else:
                    self._print('Invalid operation. Usage: \'connect <device_index>\';',
                        ' where <device_index> in an integer.')
            elif self._protocol == 'serial':
                if len(opts) == 1 or (len(opts) > 1 and opts[0] not in ['-b', '--baudrate']):
                    self._print('Invalid operation. Usage: \'connect -b[--baudrate] <baud_rate>\';',
                        ' where <baud_rate> in an integer.')
                    return

                baud = str(self._core.serial.BAUDS[-1]) if len(opts) < 1 else opts[1]

                if baud.isdigit():
                    if self._core.serial.open_port(int(baud)):
                        self._print(f'Connected via serial at baud rate {baud}.')
                else:
                    self._print('Invalid operation. Usage: \'connect -b[--baudrate] <baud_rate>\';',
                        ' where <baud_rate> in an integer.')

        def disconnect():
            if self._protocol == '':
                self._print('No protocol to disconnect from.')
            elif self._protocol == 'edsdk':
                self._core.edsdk.disconnect()
            else:
                self._core.serial.close_port()

            self._print('Disconnected.')

        def shoot():
            if self._protocol == '':
                self._print('No protocol to shoot from.')
            elif self._protocol == 'edsdk':
                if len(opts) < 1:
                    self._core.edsdk.take_picture()
                elif opts[0].isdigit():
                    if self._core.edsdk.connect(int(opts[0])):
                        self._core.edsdk.take_picture()
                else:
                    self._print('Invalid operation. Usage: \'shoot <device_index>\';',
                        ' where <device_index> in an integer.')
            elif self._protocol == 'serial':
                if not self._core.serial.is_port_open:
                    self._print('A serial port needs to be open in order to shoot.')
                else:
                    cmd = 'C0S1'
                    if len(opts) < 1:
                        self._core.serial.write(cmd)
                    elif opts[0].isdigit():
                        index = int(opts[0])
                        if index > 0:
                            self._core.serial.write(f'>{index}{cmd}')
                        else:
                            self._core.serial.write(cmd)
                    else:
                        self._print('Invalid operation. Usage: \'shoot <device_index>\';',
                            ' where <device_index> in an integer.')

        def list_():
            if self._protocol == '':
                self._print('No protocol to list items for.')
            elif self._protocol == 'edsdk':
                devices = self._core.edsdk.device_list

                if len(devices) > 0:
                    for i, item in enumerate(devices):
                        (device, is_connected) = item
                        status = ' - connected' if is_connected else ''
                        desc = device.szDeviceDescription.decode('utf-8')
                        self._print(f'\t{i}: {desc}{status}')
                else:
                    self._print('No devices found.')
            elif self._protocol == 'serial':
                devices = self._core.serial.port_list

                if len(devices) > 0:
                    for device in devices:
                        status = ' - connected' if device.connection is not None and \
                            device.connection.is_open else ''
                        active = ' - selected' if device.is_active else ''
                        self._print(f'\t{device.name}: {status}{active}')
                else:
                    self._print('No devices found.')

        def refresh():
            if self._protocol != 'serial':
                self._print('this command is only allowed for serial protocol.')
            else:
                self._print('Refreshing...')
                self._core.serial.update_port_list()
                self._print('refreshed.')
                list_()

        def select():
            if self._protocol != 'serial':
                self._print('this command is only allowed for serial protocol.')
            else:
                if len(opts) < 1:
                    self._print('No port provided. Usage: \'select <port_name>\';',
                        ' where <port_name> is a string.')
                else:
                    port = self._core.serial.select_port(opts[0])
                    self._print(f'{opts[0]} {"not " if port is None else ""}selected.')

        def default():
            self._print("Command not implemented.")

        cmds = {
            'use': use,
            'release': release,
            "list": list_,
            'connect': connect,
            'disconnect': disconnect,
            'shoot': shoot,
            'refresh': refresh,
            'select': select
        }

        cmds.get(cmd, default)()

    def _print(self, *msgs):
        msg = ''.join(msgs)
        if self._console is None:
            print(msg)
        else:
            self._console.print(msg)
