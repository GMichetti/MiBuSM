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

from abc import ABC, abstractmethod
import hid
import socket
from retry import retry
from common_libs import *
logger = Logger()


class Reachability(ABC):

    @abstractmethod
    def is_reachable(self):
        pass


class IP_Reachable(Reachability):
    def __init__(self, ipOrName):
        self._ipOrName = ipOrName

    @retry(delay=1, tries=1)
    def is_reachable(self, port=80, timeout=2):  
        """
        It checks if a IP device is reachable

        Args:
            port (integer): port used by the socket
            timeout (integer): timeout

        Raises:
            ConnectionError: device isn't reachable
            Exception: general error
        """
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        # logger.info(f"ping ip: {self._ipOrName} KO")
        try:
            s.connect((self._ipOrName, int(port)))
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        except ConnectionError as error:
            logger.info(f"ping ip: {self._ipOrName} KO")
            raise
        except Exception as error:
            logger.info(f"ping ip: {self._ipOrName} KO")
            raise


class USB_Reachable(Reachability):
    
    def __init__(self, vid, pid):
        self._vid = vid
        self._pid = pid

    def is_reachable(self):
        """
        It checks if a USB device is reachable

        Raises:
            Exception: general error
        """       
        
        try:
            hid.enumerate(self._vid, self._pid)
        except Exception as error:
            logger.info(f"reachabiliy usb: {self._vid}/{self._pid} KO")
            raise
