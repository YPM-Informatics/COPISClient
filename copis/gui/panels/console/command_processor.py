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

"""Console Command Processor."""

import shlex

from copis.helpers import print_echo_msg

# pylint: disable=protected-access
class _CommandProcessor:
    """Handle console commands processing and execution.

    Args:
        parent: Pointer to a parent console panel.
    """
    _PROTOCOLS = ['edsdk', 'serial']

    def __init__(self, core) -> None:
        self._core = core
        self._protocol = ''

    def process(self, cmd_line: str) -> None:
        """Processe the given command."""
        protocol_prompt = f'<{self._protocol}>' if len(self._protocol) > 0 else ''
        self._print(f'{protocol_prompt}$ {cmd_line}')

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
                self._core.disconnect_edsdk()
            elif self._protocol == 'serial':
                self._core.terminate_serial()
            self._print(f'Protocol {self._protocol} released.')
            self._protocol = ''

        def connect():
            if self._protocol == '':
                self._print('No protocol to connect with.')
            elif self._protocol == 'edsdk':
                cam_index = '0' if len(opts) < 1 else opts[0]

                if cam_index.isdigit():
                    if self._core.connect_edsdk(int(cam_index)):
                        self._print(f'Connected to camera {cam_index}')
                    else:
                        self._print(f'Unable to connect to camera {cam_index}')
                else:
                    self._print('Invalid operation. Usage: \'connect <device_index>\';',
                        ' where <device_index> in an integer.')
            elif self._protocol == 'serial':
                if len(opts) == 1 or (len(opts) > 1 and opts[0] not in ['-b', '--baudrate']):
                    self._print('Invalid operation. Usage: \'connect -b[--baudrate] <baud_rate>\';',
                        ' where <baud_rate> in an integer.')
                    return

                baud = str(self._core.serial_bauds[-1]) if len(opts) < 1 else opts[1]

                if baud.isdigit():
                    if self._core.connect_serial(int(baud)):
                        self._print(f'Connected via serial at baud rate {baud}.')
                else:
                    self._print('Invalid operation. Usage: \'connect -b[--baudrate] <baud_rate>\';',
                        ' where <baud_rate> in an integer.')

        def disconnect():
            if self._protocol == '':
                self._print('No protocol to disconnect from.')
            elif self._protocol == 'edsdk':
                self._core.disconnect_edsdk()
            else:
                self._core._serial.close_port()

            self._print('Disconnected.')

        def shoot():
            if self._protocol == '':
                self._print('No protocol to shoot from.')
            elif self._protocol == 'edsdk':
                if len(opts) < 1:
                    self._core.snap_edsdk_picture()
                elif opts[0].isdigit():
                    if self._core.connect_edsdk(int(opts[0])):
                        self._core.snap_edsdk_picture()
                else:
                    self._print('Invalid operation. Usage: \'shoot <device_index>\';',
                        ' where <device_index> in an integer.')
            elif self._protocol == 'serial':
                if not self._core.is_serial_port_connected:
                    self._print('A serial port needs to be open in order to shoot.')
                else:
                    cmd = 'C0P500'
                    if len(opts) < 1:
                        self._core._serial.write(cmd)
                    elif opts[0].isdigit():
                        index = int(opts[0])
                        if index > 0:
                            self._core._serial.write(f'>{index}{cmd}')
                        else:
                            self._core._serial.write(cmd)
                    else:
                        self._print('Invalid operation. Usage: \'shoot <device_index>\';',
                            ' where <device_index> in an integer.')

        def list_():
            if self._protocol == '':
                self._print('No protocol to list items for.')
            elif self._protocol == 'edsdk':
                devices = self._core.edsdk_device_list

                if len(devices) > 0:
                    for i, item in enumerate(devices):
                        (device, is_connected) = item
                        status = ' - connected' if is_connected else ''
                        desc = device.szDeviceDescription.decode('utf-8')
                        self._print(f'\t{i}: {desc}{status}')
                else:
                    self._print('No devices found.')
            elif self._protocol == 'serial':
                devices = self._core.serial_port_list

                if len(devices) > 0:
                    for device in devices:
                        status = ' - connected' if device.is_connected else ''
                        active = ' - selected' if device.is_active else ''
                        self._print(f'\t{device.name}: {status}{active}')
                else:
                    self._print('No devices found.')

        def refresh():
            if self._protocol != 'serial':
                self._print('this command is only allowed for serial protocol.')
            else:
                self._print('Refreshing...')
                self._core.update_serial_ports()
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
                    port = self._core.select_serial_port(opts[0])
                    self._print(f'{opts[0]} {"not " if port is None else ""}selected.')

        def optimize():
            if (len(opts) < 0):
                self._print('Optimization parameters required. See documentation')
                return
            elif (opts[0].lower() == 'pan'):   
                 #perform pan optimization
                 self._core.optimize_all_poses_pan_angles()
                 self._core.select_pose(self._core.selected_pose) #reselect the current selected pose (if one was selected) to update variables in transorm panel
                 self._print('Pan optimization completed.')
            elif (opts[0].lower() == 'random'):   
                 self._core.optimize_all_poses_randomize() #poor preformance on large pose sets. Likely due to monitored list. Will have to look into it one day.
                 self._core.select_pose(self._core.selected_pose) 
                 self._print('Pose set randomization completed.')
            else:
               self._print('Invalid optimization parameters required. See documentation')

        def default():
            # self._print("Command not implemented.")
            if not self._core.is_serial_port_connected:
                self._print('A serial port needs to be open in order to shoot.')
            else:
                self._core._serial.write(cmd)
         

        cmds = {
            'use': use,
            'release': release,
            "list": list_,
            'connect': connect,
            'disconnect': disconnect,
            'shoot': shoot,
            'refresh': refresh,
            'select': select,
            'optimize': optimize
        }

        cmds.get(cmd, default)()

    def _print(self, *msgs):
        msg = ''.join(msgs)
        print_echo_msg(self._core.console, msg)
