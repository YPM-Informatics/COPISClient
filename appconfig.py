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

"""AppConfig class."""

import configparser
from pathlib import Path
from typing import Optional


class AppConfig():
    """Manage saving, loading, and parsing a configuration file.

    Attributes:
        config: A configparser.ConfigParser instance.
        dirty: A boolean indicating if a config value has been modified or not.
            Only saves when dirty is True.
    """

    def __init__(self) -> None:
        """Inits AppConfig."""
        self._config = None
        self._dirty = False

    def set_defaults(self) -> None:
        """Override missing or keys with their defaults.

        TODO
        """
        pass

    def load(self) -> bool:
        """Read config file.

        Raises:
            IOError: If config file could not be loaded.

        Returns:
            True if config file loaded without error, False otherwise.

        TODO: look into property trees (c++ Boost), perhaps instead of storing
        the ConfigParser we could store the property tree instead
        """
        path = self.config_path()
        try:
            self._config = configparser.ConfigParser()
            self._config.read(path)
        except configparser.Error:
            raise IOError(
                'Error reading COPIS config file.\n'
                'Try to manually delete the file to recover from the error.\n')
        finally:
            pass
        return True

    def save(self) -> bool:
        """Save config file.

        Returns:
            True if config file saved without error, False otherwise.
        """
        if not self._dirty:
            return True

        with open(self.config_path(), 'w') as configfile:
            self._config.write(configfile)
            self._dirty = False
        return True

    @property
    def config(self) -> Optional[configparser.ConfigParser]:
        return self._config

    @config.setter
    def config(self, value: configparser.ConfigParser) -> None:
        self._config = value
        self._dirty = True

    @property
    def dirty(self) -> bool:
        return self._dirty

    @dirty.setter
    def dirty(self, value: bool) -> None:
        self._dirty = value

    def update_config_dir(self, dir: Path) -> None:
        """Update config file directory given the dir Path. TODO
        """
        self._dirty = True

    def exists(self) -> bool:
        """Return if the config path exists or not."""
        return self.config_path().exists()

    def config_path(self) -> Path:
        """Return path to config file.

        TODO: set data directory?
        """
        # Unix: ~/.COPIS
        # Windows : "C:\Users\username\AppData\Roaming\COPIS" or "C:\Documents and Settings\username\Application Data\COPIS"
        # Mac : "~/Library/Application Support/COPIS"
        return Path('./copis.ini')

    def __iter__(self):
        """TODO"""
        yield
