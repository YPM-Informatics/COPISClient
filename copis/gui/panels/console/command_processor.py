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

    def __init__(self, parent) -> None:
        self._console = parent
        self._protocol = ''

    def process(self, cmd_line: str) -> None:
        """Processes the given command."""
        protocol_prompt = f'<{self._protocol}>' if len(self._protocol) > 0 else ''
        self._console.print(f'{protocol_prompt}$ {cmd_line}')

        self._console.on_command_cleared()

        argv = shlex.split(cmd_line)

        if len(argv) < 1:
            self._console.print('No command provided.')

        self.switch(argv[0], argv[1:])

    def switch(self, cmd: str, opts) -> None:
        """Switch statement implementation for commands list."""
        def use():
            protocol = opts[0].lower()
            if len(protocol) < 1 or protocol not in self._PROTOCOLS:
                self._console.print('No valid protocol provided. Usage: \'use <protocol>\'; \
                    where <protocol> is \'edsdk\' or \'serial\'.')
                return

            self._protocol = protocol
            self._console.print(f'Using {self._protocol}.')

        def release():
            self._console.print(f'Protocol {self._protocol} released.')
            self._protocol = ''

        def connect():
            if self._protocol == '':
                self._console.print('No protocol to connect with.')
            elif self._protocol == 'edsdk':
                cam_index = '0' if len(opts) < 1 else opts[0]

                if cam_index.isdigit():
                    self._console.core.edsdk.connect(int(cam_index))
                else:
                    self._console.print('Invalid operation. \'Usage: connect <device_index>\'; \
                        where <device_index> in an integer.')
            else:
                self._console.print(f'Protocol \'{self._protocol}\' not implemented.')

        def disconnect():
            if self._protocol == '':
                self._console.print('No protocol to disconnect from.')
            elif self._protocol == 'edsdk':
                self._console.core.edsdk.disconnect()
            else:
                self._console.print(f'Protocol \'{self._protocol}\' not implemented.')

        def shoot():
            if self._protocol != 'edsdk':
                self._console.print('A device needs to be connected via \'edsdk\' \
                    in order to shoot.')
            else:
                if len(opts) < 1:
                    self._console.core.edsdk.take_picture()
                elif opts[0].isdigit():
                    if self._console.core.edsdk.connect(int(opts[0])):
                        self._console.core.edsdk.take_picture()
                else:
                    self._console.print('Invalid operation. \'Usage: shoot <device_index>\';  \
                        where <device_index> in an integer.')

        def list_():
            if self._protocol == '':
                self._console.print('No protocol to list items for.')
            elif self._protocol == 'edsdk':
                devices = self._console.core.edsdk.device_list

                if len(devices) > 0:
                    for i, item in enumerate(devices):
                        (device, is_connected) = item
                        status = " - connected" if is_connected else ""
                        desc = device.szDeviceDescription.decode("utf-8")
                        self._console.print(f'\t{i}: {desc}{status}')
                else:
                    self._console.print('No devices found.')
            else:
                self._console.print(f'Protocol \'{self._protocol}\' not implemented.')

        def default():
            self._console.print("Command not implemented.")

        cmds = {
            'use': use,
            'release': release,
            "list": list_,
            'connect': connect,
            'disconnect': disconnect,
            'shoot': shoot
        }

        cmds.get(cmd, default)()
