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

"""Provides the COPIS G-codes."""

from enum import Enum, auto

class Gcode(Enum):
    """G-code commands."""

    C0 = auto()
    """Shutter press via remote shutter."""
    C1 = auto()
    """Autofocus via remote shutter."""
    C10 = auto()
    """Focus stack via remote shutter."""

    G0 = auto()
    """Rapid linear movement."""
    G1 = auto()
    """Linear movement."""
    G2 = auto()
    """Clockwise arc movement."""
    G3 = auto()
    """Counter clockwise arc movement."""
    G4 = auto()
    """Pause device."""
    G17 = auto()
    """XY plane."""
    G18 = auto()
    """ZX plane."""
    G19 = auto()
    """YZ plane."""
    G28 = auto()
    """Homing."""
    G90 = auto()
    """Absolute distance mode."""
    G91 = auto()
    """Relative distance mode."""
    G92 = auto()
    """Set axis position(s)."""

    M0 = auto()
    """Pause processing."""
    M17 = auto()
    """Enable all motors."""
    M18 = auto()
    """Disable all motors."""
    M24 = auto()
    """Resume processing."""
    M120 = auto()
    """Scan for connected cards - Only applicable on main controller."""
    M360 = auto()
    """Toggle multi-turn"""
    M511 = auto()
    """Toggle device locked."""
    M998 = auto()
    """Reboot - V## Parameter is optional. Any value greater than 0 allows
        any prior buffered action to finish execution before reboot."""

    E0 = auto()
    """Shutter press via EDSDK.

    :tag `experimental`

    """
    E1 = auto()
    """Autofocus via EDSDK.

    :tag `experimental`

    """
    E10 = auto()
    """Focus stack via EDSDK.

    :tag `experimental`

    """
