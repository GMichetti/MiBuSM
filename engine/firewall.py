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

import re
from utils import SSH_Access
from retry import retry
from reachability import IP_Reachable
from abc import ABC, abstractmethod
from common_libs import *
from config_loader import Config_Loader
logger = Logger()

config_loader = Config_Loader()
ACTION_DELAY = config_loader.config["action_retry_delay"]
ACTION_TRIES = config_loader.config["action_retry_tries"]


class Firewall(IP_Reachable, ABC):
    def __init__(self, id, ip, user, password):
        IP_Reachable.__init__(self, ip)
        self._id = id
        self._ip = ip
        self._user = user
        self._password = password
        self._session = None
        self._logged_in = False

    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def logout(self):
        pass

    @abstractmethod
    def send_command(self):
        pass

    @abstractmethod
    def get_info(self):
        pass

    @abstractmethod
    def get_status(self):
        pass


class Firewall_Fortinet(Firewall):

    def __init__(self, id, ip, user, password):
        super().__init__(id, ip, user, password)
        self._id = id
        self._ip = ip
        self._user = user
        self._password = password
        self._session = None
        self._pmko_session = SSH_Access(id=self._id,
                                                   ip=self._ip, user=self._user, password=self._password)

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def login(self):
        """
        Login into the Fortigate firewall both via FortigateAPI and via Paramiko SSH session

        Raises:
            Exception: Something went wrong
        """
        
        try:
            # paramiko connection to gather global performance info
            self._pmko_session.login()
        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def logout(self):
        """
        Logout from Fortigate firewall

        Raises:
            Exception: Something went wrong
        """

        try:
            self._session.logout()
        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def get_info(self):
        """
        Get info from Fortigate firewall about interfaces and hardware utilization

        Raises:
            Exception: Something went wrong
        """

        try:

            CMD = 'get system performance status'
            res_cmd = self.send_command(CMD)

            cpu_pattern = r"CPU states: (\d+)% user (\d+)% system (\d+)% nice (\d+)% idle"
            memory_pattern = r"Memory: (\d+)k total, (\d+)k used \(([\d.]+)%\)"
            network_usage_pattern = r"Average network usage: (\d+) \/ (\d+) kbps in 1 minute, (\d+) \/ (\d+) kbps in 10 minutes, (\d+) \/ (\d+) kbps in 30 minutes"
            virus_pattern = r"Virus caught: (\d+) total in "
            ips_pattern = r"IPS attacks blocked: (\d+) total in "

            cpu_match = re.search(cpu_pattern, res_cmd)
            memory_match = re.search(memory_pattern, res_cmd)
            network_usage_match = re.search(network_usage_pattern, res_cmd)
            virus_match = re.search(virus_pattern, res_cmd)
            ips_match = re.search(ips_pattern, res_cmd)

            cpu_dict = {}
            memory_dict = {}
            network_usage_dict = {}
            virus_dict = {}
            ips_dict = {}

            if cpu_match:
                cpu_dict = {
                    'user': cpu_match.group(1),
                    'system': cpu_match.group(2),
                    'nice': cpu_match.group(3),
                    'idle': cpu_match.group(4)
                }

            if memory_match:
                memory_dict = {
                    'total': memory_match.group(1),
                    'used': memory_match.group(2),
                    'percentage_used': memory_match.group(3)
                }

            if network_usage_match:
                network_usage_dict = {
                    '1_min_tx': network_usage_match.group(1),
                    '1_min_rx': network_usage_match.group(2),
                    '10_min_tx': network_usage_match.group(3),
                    '10_min_rx': network_usage_match.group(4),
                    '30_min_tx': network_usage_match.group(5),
                    '30_min_rx': network_usage_match.group(6)
                }

            if virus_match:
                virus_dict = {
                    'total': virus_match.group(1)
                }

            if ips_match:
                ips_dict = {
                    'total': ips_match.group(1)
                }

            res = {
                "cpu": cpu_dict,
                "memory": memory_dict,
                "network": network_usage_dict,
                "virus_match": virus_dict,
                "ips": ips_dict
            }
            return res

        except Exception as err:
            logger.error(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def get_status(self):
        """
        It neeeded to understand if the Fortigate session is still operational

        Raises:
            Exception: Something went wrong
        """
        
        try:
            # if self._session != None and self.get_info():
            if self._pmko_session.check_session():
                return True
            else:
                return False
        except Exception as err:
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def send_command(self, cmd):
        """
        Send command to Fortigate Firewall

        Args:
            cmd (string): command to execute via SSH CLI session

        Returns:
            string: result of the action

        Raises:
            Exception: Something went wrong
        """
        
        try:
            return self._pmko_session.exe(cmd)

        except Exception as err:
            logger.error(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def reboot(self):
        """
        Send reboot command to Fortigate Firewall

        Returns:
            string: result of the action

        Raises:
            Exception: Something went wrong
        """     
        
        try:
            return self._pmko_session.exe_with_confirm(cmd="execute reboot", confirmation_keyword="This operation will reboot the system !")
        except Exception as err:
            logger.error(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def shutdown(self):
        """
        Send shutdown command to Fortigate Firewall

        Returns:
            string: result of the action

        Raises:
            Exception: Something went wrong
        """        
           
        try:
            return self._pmko_session.exe_with_confirm(cmd="execute shutdown", confirmation_keyword="This operation will reboot the system !")
        except Exception as err:
            logger.error(err)
            raise
