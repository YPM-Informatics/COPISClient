#!/usr/bin/env python3

import configparser
from pathlib import Path


class AppConfig():
    def __init__(self):
        self._config = None
        # whether or not the config file needs to be saved
        self._dirty = False

    def set_defaults(self):
        """Override missing or keys with their defaults.
        TODO"""
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
        return True

    def save(self):
        """Save config."""
        if not self._dirty:
            return True

        with open(self.config_path(), 'w') as configfile:
            self._config.write(configfile)
            self._dirty = False
        return True

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value
        self._dirty = True

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    def update_config_dir(self, dir):
        """TODO"""
        self._dirty = True

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
