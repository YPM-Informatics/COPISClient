#!/usr/bin/env python3

import configparser
from pathlib import Path


class AppConfig():
    def __init__(self):
        # whether or not the config file needs to be saved
        self._dirty = False

        self._config = None

    def set_defaults(self):
        """Override missing or keys with their defaults."""
        # TODO
        pass

    def load(self):
        """Read config file.

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
        print('configparser testing: please ignore output')
        print([[option for option in self._config[section]] for section in self._config.sections()])

    def save(self):
        """Writes self._storage into specified config file.
        TODO
        """
        path = self.config_path()
        self._dirty = False

    def get(self, value):
        """Get value of specified key.
        TODO
        """
        if self._config is None:
            return False
        pass

    @property
    def config(self):
        return self._config

    def dirty(self):
        self._dirty = True

    def update_config_dir(self, dir):
        """TODO"""
        pass

    def exists(self):
        return self.config_path().exists()

    def config_path(self):
        """Return path to config file.

        (from PrusaSlicer)
        TODO: set data directory?
        """
        # Unix: ~/.COPIS
        # Windows : "C:\Users\username\AppData\Roaming\COPIS" or "C:\Documents and Settings\username\Application Data\COPIS"
        # Mac : "~/Library/Application Support/COPIS"
        return Path('./copis.ini')

    def __iter__(self):
        """TODO"""
        return
