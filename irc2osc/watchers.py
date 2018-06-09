import os
import asyncio
import logging

logger = logging.getLogger(__name__)


class FileWatcher:
    """
    Class to handle actions on file change
    """
    def __init__(self, filename, change_func, loop=None, check_interval=60):
        self._last_modified = self.get_last_modified_time(filename)
        self.check_interval = check_interval

        self.filename = filename
        self.change_func = change_func

        self.loop = loop if loop is not None else asyncio.get_event_loop()

    def get_last_modified_time(self, filename):
        """
        Returns the last time the file was modified
        """
        return os.stat(filename).st_mtime

    def check_watched_file(self):
        """
        Check if the watched file has changed.  If so, run function passed on
        init
        """
        current_last_mod = self.get_last_modified_time(self.filename)

        if current_last_mod != self._last_modified:
            self._last_modified = current_last_mod
            self.change_func()

        self.loop.call_later(self.check_interval, self.check_watched_file)

    def start(self):
        """
        Initiate the watching loop
        """
        self.loop.call_later(self.check_interval, self.check_watched_file)
