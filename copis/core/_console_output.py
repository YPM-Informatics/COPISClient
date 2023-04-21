# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""Console Output Class."""

import threading
import time

from pydispatch import dispatcher

from copis.helpers import dispatch_msg

class ConsoleOutput:
    """Implement console output operations."""

    def __init__(self, client):
        self._client = client

    def log(self, signal: str, msg: str) -> None:
        """Dispatch a message to the console."""
        client = self._client

        if client:
            if client.is_gui_loaded:
                dispatcher.send(signal, message=msg)
            else:
                dispatch_thread = threading.Thread(
                    target=self._dispatch_on_gui_loaded,
                    name='console output thread',
                    daemon=True,
                    kwargs={
                        "signal": signal,
                        "message": msg
                    })

                dispatch_thread.start()
        else:
            dispatch_msg(None, signal, msg)

    def _dispatch_on_gui_loaded(self, signal, message):
        while not self._client.is_gui_loaded:
            time.sleep(.001)

        dispatcher.send(signal, message=message)
