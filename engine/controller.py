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

# libs for PowerEdge servers via IPMI
# NOTE: IPMI needs to be enabled in some Dell PowerEdge models. Check IDRAC settings
import pyghmi.ipmi.command as ipmi
from pyghmi.ipmi.command import Command

# libs for Cisco servers
from imcsdk.imchandle import ImcHandle
from imcsdk.apis.server.serveractions import server_power_up, server_power_down_gracefully, server_power_state_get, _wait_for_power_state, server_power_cycle
from reachability import IP_Reachable
from retry import retry
from abc import ABC, abstractmethod
from common_libs import *
from config_loader import Config_Loader
logger = Logger()

config_loader = Config_Loader()
ACTION_DELAY = config_loader.config["action_retry_delay"]
ACTION_TRIES = config_loader.config["action_retry_tries"]


class Controller(IP_Reachable, ABC):
    def __init__(self, id, ip, user, password):
        IP_Reachable.__init__(self, ip)
        self._id = id
        self._ip = ip
        self._user = user
        self._password = password
        self._session = None

    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def logout(self):
        pass

    @abstractmethod
    def check_login(self):
        pass

    @abstractmethod
    def power_on(self):
        pass

    @abstractmethod
    def power_off(self):
        pass

    @abstractmethod
    def reboot(self):
        pass

    @abstractmethod
    def get_server_power_state(self):
        pass


class Controller_Cisco(Controller):

    def __init__(self, id, ip, user, password):
        super().__init__(id, ip, user, password)

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def login(self):
        """
        Log in to the server
        """

        try:
            self._session = ImcHandle(
                ip=self._ip, username=self._user, password=self._password, auto_refresh=True)
            self._session.login()

        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def check_login(self):
        """
        Check that MiBu is still logged in the server
        """

        try:
            if self._session != None and self._session.cookie != None:
                if self._session._validate_connection():
                    logger.info(
                        f"server: {self._id} controller already logged-in")
                    return True
                else:
                    logger.info(
                        f"server: {self._id} controller needs to be reconnected")
                    return False
            else:
                logger.info(f"server: {self._id} controller NOT logged-in")
                return False

        except Exception as err:
            logger.info(err)
            return False

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def logout(self):
        """
        Log out from the server
        """

        try:
            self._session.logout()
        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def power_on(self):
        """
        Turning on the server via controller
        """

        try:
            server_power_up(self._session, "sys/rack-unit-1")
            logger.info(f"waiting for power-on server: {self._id}")
            _wait_for_power_state(self._session, state="on")
            logger.info(f"power-on server: {self._id} OK")
        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def power_off(self):
        """
        Turning off the server via controller
        """

        try:
            logger.info(f"waiting for power-off server: {self._id}")
            server_power_down_gracefully(self._session, "sys/rack-unit-1")
            logger.info(f"power-off server: {self._id} OK")

        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def reboot(self):
        """
        Reboot the server via controller
        """

        try:
            logger.info(f"waiting for power-cycle server: {self._id}")
            server_power_cycle(self._session, "sys/rack-unit-1")
            _wait_for_power_state(self._session, state="on")
            logger.info(f"power-cycle server: {self._id} OK")
        except Exception as err:
            logger.info(err)
        raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def get_server_power_state(self):
        """
        It is used to understand if the server is on or off
        """

        try:
            res = server_power_state_get(self._session, "sys/rack-unit-1")
            return res
        except Exception as err:
            logger.info(err)
            raise


class Controller_Dell(Controller):

    def __init__(self, id, ip, user, password):
        super().__init__(id, ip, user, password)

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def login(self):
        """
        Log in to the server
        """

        try:
            self._session = ipmi.Command(
                bmc=self._ip, userid=self._user, password=self._password, keepalive=True)

        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def check_login(self):
        """
        Check that MiBu is still logged in the server otherwise login
        """

        try:
            if self._session != None:
                if (bool(self._session._get_device_id())) :
                    return True
                else:
                    return False
            else:
                return False

        except Exception as err:
            logger.info(err)
            return False

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def logout(self):
        """
        Log out from the server
        """

        try:
            self._session.ipmi_session.logout()
        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def power_on(self):
        """
        Turning on the server via controller
        """

        try:
            self._session.set_power("on")
            logger.info(f"power-on server: {self._id} OK")
        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def power_off(self):
        """
        Turning off the server via controller
        """

        try:
            self._session.set_power("softoff")
            logger.info(f"power-off server: {self._id} OK")
        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def reboot(self):
        """
        Reboot the server via controller
        """

        try:
            self._session.set_power("reset")
            logger.info(f"power-cycle server: {self._id} OK")
        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def get_server_power_state(self):
        """
        It is used to understand if the server is on or off
        """

        try:
            res = self._session._get_power_state()
            return res
        except Exception as err:
            logger.info(err)
            raise
