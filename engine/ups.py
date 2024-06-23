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


from retry import retry
from libs.usb_vendor_xref import CODE
import hid
from libs.usb import USB
from reachability import USB_Reachable
from abc import ABC, abstractmethod
from common_libs import *
from config_loader import Config_Loader
logger = Logger()

config_loader = Config_Loader()
ACTION_DELAY = config_loader.config["action_retry_delay"]
ACTION_TRIES = config_loader.config["action_retry_tries"]


class UPS(ABC):
    def __init__(self, id):
        self._id = id

    @abstractmethod
    def get_info(self):
        pass


class CyberPowerUPS(UPS, USB_Reachable):

    def __init__(self, id, product_id):
        super().__init__(id)
        self._vendor_id = CODE["cyberpower"]
        if isinstance(product_id, str):
            self._product_id = int(product_id, 16)
        else:
            self._product_id = product_id
        USB_Reachable.__init__(self, self._vendor_id, self._product_id)
        self._device = None
        self._ups = None

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def login(self):
        """
        Login to the USB Cyberpower UPS
        """

        try:
            if not self._device:
                device_item = hid.enumerate(
                    self._vendor_id, self._product_id).pop()
                logger.info(
                    f"trying to login Cyberpower UPS with PID: {self._product_id}")
                self._device = hid.device()
                self._device.open_path(device_item['path'])
        except Exception as err:
            logger.error(err)

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def logout(self):
        """
        There is nothing to do here
        """

        pass

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def get_info(self):
        """
        It gets info from Cyberpower UPS

        Args:
            radius (float): Il raggio del cerchio.

        Returns:
            dict: status of the UPS

        Raises:
            Exception: if something went wrong
        """

        try:
            logger.info(
                f"trying to get info about Cyberpower UPS with PID: {self._product_id}")
            self._ups = USB(self._device)
            return self._ups.dict_status()

        except Exception as error:
            logger.info(error)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def get_status(self):
        """
        It gets the status. Needed to confirm that
        we can still get data from get_info method

        Returns:
            string: product name

        Raises: 
            Exception: if something went wrong
        """

        try:
            logger.info(
                f"trying to get status about Cyberpower UPS with PID: {self._product_id}")
            self._ups = USB(self._device)
            return self._ups.iname()  # trying to get the product name
        except Exception as error:
            logger.info(error)
            return False
