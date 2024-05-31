# This file is a part of MiBu.
#
# Copyright (C) 2024 Giuseppe Michetti <gius.michetti@gmail.com>
#
# MiBu is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# MiBu is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
import inspect

try:
    from config_loader import Config_Loader
except ModuleNotFoundError:
    from .config_loader import Config_Loader

try:
    import fcntl
except ImportError:
    import msvcrt
    
class SizeLimitedFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', maxBytes=0, encoding=None, delay=0):
        self.maxBytes = maxBytes
        self.current_size = os.path.getsize(filename) if os.path.exists(filename) else 0
        super().__init__(filename, mode, encoding, delay)

    def shouldRollover(self, record):
        if self.maxBytes > 0:
            self.current_size += len(self.format(record))  # Calculate current log record size
            return self.current_size > self.maxBytes
        return False

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        self.current_size = 0
        super().doRollover()

class Logger:
    _instance = None
    _file_lock = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cl = Config_Loader()
            cls._instance.setup_logger(cl.config)
            cls._file_lock = FileLock(cl.config["log_lock_file"])
        return cls._instance
    
    def _get_caller(self):
        """Needed to get the caller name"""
        
        stack = inspect.stack()
        caller = stack[2]
        return caller.filename

    def setup_logger(self, config):
        """
        Logger setup

        Args:
            config (dict): used to get the configuration data
        """    
        
        self.logger = logging.getLogger("MiBu")
        self.logger.setLevel(logging.DEBUG)
        log_path = config["log_path"]
        max_log_size = config["max_bytes"]
        file_handler = SizeLimitedFileHandler(filename=log_path, maxBytes=max_log_size)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message):
        """It writes an info level message"""
        
        if self._file_lock.acquire():
            try:
                logger = self.logger
                logger.info(self._get_caller() + " : " + str(message))
            finally:
                self._file_lock.release()
                
    def warning(self, message):
        """It writes a warning level message"""
        
        if self._file_lock.acquire():
            try:
                logger = self.logger
                logger.warning(self._get_caller() + " : " + str(message))
            finally:
                self._file_lock.release()

    def error(self, message):
        """It writes an error level message"""
        
        if self._file_lock.acquire():
            try:
                logger = self.logger
                logger.error(self._get_caller() + " : " + str(message))
            finally:
                self._file_lock.release()

class FileLock:
    """
    Since the log file will be used by three concurrent
    processes we have a semaphore mechanism
    """
    
    def __init__(self, filename):
        self.filename = filename
        self.handle = None

    def acquire(self):
        """
        acquisition of the lock file. This way no other process can write to the log file
        """
        
        self.handle = open(self.filename, 'w')
        try:
            if os.name == 'posix':
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            elif os.name == 'nt':
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_LOCK, 1)
        except IOError:
            return False
        return True

    def release(self):
        """
        stopping the acquisition of the lock file. This way othjer process can lock the resource
        """
        
        if self.handle:
            if os.name == 'posix':
                fcntl.flock(self.handle, fcntl.LOCK_UN)
            elif os.name == 'nt':
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            self.handle.close()

