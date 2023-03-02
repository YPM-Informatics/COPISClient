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

"""Provide the COPIS MonitoredList Class."""

from pydispatch import dispatcher


class MonitoredList(list):
    """Data structure that implements a monitored list.

    Just a regular list, but sends notifications when changed or modified.
    """
    def __init__(self, signal: str, iterable=None) -> None:
        if iterable is None:
            iterable = []

        super().__init__(iterable)
        self.signal = signal

    def clear(self, dispatch=True) -> None:
        super().clear()

        if dispatch:
            self._dispatch()

    def append(self, __object) -> None:
        super().append(__object)
        self._dispatch()

    def extend(self, __iterable) -> None:
        super().extend(__iterable)
        self._dispatch()

    def pop(self, __index: int):
        value = super().pop(__index)
        self._dispatch()
        return value

    def insert(self, __index: int, __object) -> None:
        super().insert(__index, __object)
        self._dispatch()

    def remove(self, __value) -> None:
        super().remove(__value)
        self._dispatch()

    def reverse(self) -> None:
        super().reverse()
        self._dispatch()

    def __setitem__(self, key, value) -> None:
        super().__setitem__(key, value)
        self._dispatch()

    def __delitem__(self, key) -> None:
        super().__delitem__(key)
        self._dispatch()

    def _dispatch(self) -> None:
        """This is necessary because unpickling a 'List' subclass calls 'extend' to populate the
        '__iterable__' even before the object's instance attributes are set. This causes dispatching
        to fail while unpickling the object because 'signal' does not yet exist. But dispatching
        does not need to happen for an object being unpickled because it's just a monitored list
        being restored and not technically being actively changed. Besides, there is no need to
        dispatch if there's no registered signal."""

        if 'signal' in self.__dict__:
            dispatcher.send(self.signal)
