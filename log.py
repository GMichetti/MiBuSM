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
import fcntl
import datetime
import zipfile

try:
    from config_loader import Config_Loader
except ModuleNotFoundError:
    from .config_loader import Config_Loader

try:
    import fcntl
except ImportError:
    import msvcrt


config_loader = Config_Loader()

LOCK_FILE = config_loader.config["log_lock_file"]
LOG_FILE = config_loader.config["log_file_path"]
LOG_MAX_SIZE = config_loader.config["log_max_bytes"]


class Logger:
    def __init__(self):

        self.filename = LOG_FILE
        self.max_size = LOG_MAX_SIZE
        self.lock = FileLock(LOCK_FILE)


    def _archive_log(self):
        """
        It archives old log files
        """

        timestamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        zip_filename = f"{timestamp}_mibu_log.zip"
        zip_filepath = os.path.join(os.path.dirname(self.filename), zip_filename)
        
        if not os.path.exists(zip_filepath):
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED, allowZip64=True):
                pass
        
        with zipfile.ZipFile(zip_filepath, 'a', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
            zipf.write(self.filename, os.path.basename(self.filename))
        

        with open(self.filename, 'w'):
            pass
        
        self.current_size = 0

    def _log(self, level, message):
        """
        Internal log method to write on the log file
        """

        if self.lock.acquire():
            try:
                timestamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
                msg = f"{timestamp} - {level} - {message}\n"
                msg_len = len(msg)

                self.current_size = os.path.getsize(self.filename) if os.path.exists(self.filename) else 0
                if self.current_size + msg_len > LOG_MAX_SIZE:
                    self._archive_log()

                with open(self.filename, 'a') as f:
                    f.write(msg)
                self.current_size += msg_len

            finally:
                self.lock.release()

    def info(self, message):
        """
        Logging with INFO level
        """
        self._log('INFO', message)

    def warning(self, message):
        """
        Logging with WARNING level
        """
        self._log('WARNING', message)

    def error(self, message):
        """
        Logging with ERROR level
        """
        self._log('ERROR', message)


class FileLock:
    """
    Since the log file will be used by three concurrent
    processes we have a semaphore mechanism
    """
    
    def __init__(self, filename):
        self.filename = filename
        self.handle = None

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def acquire(self):
        """
        Acquisition of the lock file. This way no other process can write to the log file
        """

        self.handle = open(self.filename, 'w')
        try:
            if os.name == 'posix':
                fcntl.flock(self.handle, fcntl.LOCK_EX)
            elif os.name == 'nt':
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_LOCK, 1)
        except (IOError,ValueError):
            return False
        except Exception as err:
            return False
        return True

    def release(self):
        """
        Releasing the lock file. This way other processes can lock the resource
        """

        try:
            if self.handle:
                if os.name == 'posix':
                    fcntl.flock(self.handle, fcntl.LOCK_UN)
                elif os.name == 'nt':
                    msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
                self.handle.close()
        except (IOError,ValueError):
            return False
        except Exception as err:
            return False
        return True