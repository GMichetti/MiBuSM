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

import uuid
import time
import paramiko
from retry import retry
try:
    from common_libs import *
except ModuleNotFoundError:
    from .common_libs import *
from config_loader import Config_Loader

config_loader = Config_Loader()
logger = Logger()


__all__ = ["get_timestamp", "add_meta_to_action", "SSH_Access", "get_object_by_action_id"]


def get_object_by_action_id(data_list, action_id):
    """
    It returns an action dict inside a list o by the action_id
    
    Returns:
        dict|None: the corrisponding dict
    
    """
    for item in data_list:
        if item.get("action_id") == action_id:
            return item
    return None


def get_timestamp():
    """
    Get a timestamp

    Returns:
        string: current timestamp.
    """

    return time.time()


def add_meta_to_action(action):
    """
    It adds metadata to the passed action

    Args:
        action (string): action that you want to extend with metadata

    Returns:
        dict: encapsulated action with the corrisponding metadata 
    """

    uuid4 = uuid.uuid4()
    return {
        "action": action,
        "action_id": str(uuid4),
        "action_time_req": get_timestamp()
    }


class SSH_Access():

    def __init__(self, id, ip, user, password):
        self._id = id
        self._ip = ip
        self._user = user
        self._password = password
        self._ssh_client = paramiko.SSHClient()
        self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    @retry(delay=2, tries=2)
    def login(self):  
        """
        Login to the device via Paramiko/SSH
        """
        
        try:
            self._ssh_client.connect(
                self._ip, username=self._user, password=self._password)

        except Exception as e:
            logger.error(
                f"Error: can't login (API paramiko) to device id: {self._id} : {e}")

    @retry(delay=2, tries=2)
    def logout(self):
        """
        It closes the SSH/Paramiko session
        """
        
        try:
            self._ssh_client.close()

        except Exception as e:
            if e == "SSH session not active":
                self.login()
            logger.error(
                f"Error: can't logout (API paramiko) to device id: {self._id} : {e}")
            
    @retry(delay=2, tries=2)
    def check_session(self):
        """
        It checks if the session is still active

        Returns:
            boolean: true if the session is still active
        """
        
        try:
            transport = self._ssh_client.get_transport()
            if transport is not None and transport.is_active():
                return True
            return False

        except Exception as e:
            logger.error(
                f"Error: session not active (API paramiko) device id: {self._id} : {e}")
            return False

    @retry(delay=2, tries=2)
    def exe(self, cmd):
        """
        It executes the action passed via input

        Args:
            cmd (string): action you want to execute

        Returns:
            string: the result of the corrisponding action
        """
        
        try:
            stdin, stdout, stderr = self._ssh_client.exec_command(cmd)
            return stdout.read().decode('utf-8')

        except Exception as e:
            if e == "SSH session not active":
                self.login()

            logger.error(
                f"Error: can' execute action (API paramiko) to device id: {self._id} : {e}")

    @retry(delay=2, tries=2)
    def exe_with_confirm(self, cmd, confirmation_keyword):
        """
        It executes the action passed via input
        This command is needed in case there is a confirmation prompt

        Args:
            cmd (string): action you want to execute

        Returns:
            string: the result of the corrisponding action
        """
        
        stdin, stdout, stderr = self._ssh_client.exec_command(cmd)
        errors = stderr.read().decode('utf-8')
        output = stdout.read().decode('utf-8')
        if confirmation_keyword in output:
            time.sleep(1)
            self._send_confirmation('y\n')
            output += stdout.channel.recv(1024).decode('utf-8')

        if errors:
            output += "Errors occurred:\n" + errors

        return output

    def _send_confirmation(self, confirmation):
        """
        It replies to the confirmation prompt

        Args:
            confirmation (string): word used to confirmation
        """
        
        stdin, stdout, stderr = self._ssh_client.exec_command(confirmation)
        stdout.channel.recv_exit_status()
