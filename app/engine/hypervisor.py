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

import ssl
# libs to use API for ESXi
from pyVmomi import vim
from pyVim.connect import Disconnect
from pyVim import connect
from reachability import IP_Reachable
from retry import retry
from abc import ABC, abstractmethod
from common_libs import *
from config_loader import Config_Loader
logger = Logger()
config_loader = Config_Loader()

ACTION_DELAY = config_loader.config["action_retry_delay"]
ACTION_TRIES = config_loader.config["action_retry_tries"]

context = ssl._create_unverified_context()


class HyperVisor(IP_Reachable, ABC):
    def __init__(self, id, ip, user, password):
        IP_Reachable.__init__(self, ip)
        self._id = id
        self._ip = ip
        self._user = user
        self._password = password

    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def logout(self):
        pass

    @abstractmethod
    def get_info(self):
        pass

    @abstractmethod
    def check_login(self):
        pass

    @abstractmethod
    def vms_power_on(self):
        pass

    @abstractmethod
    def vms_power_off(self):
        pass

    @abstractmethod
    def check_vms_powered_on(self):
        pass


class ESXi(HyperVisor):
    def __init__(self, id, ip, user, password):
        super().__init__(id, ip, user, password)

        self._service_instance = None
        self._esxihost = None
        self._info = dict()

    def __get_snapshots(self, vm):
        """
        Get all the snapshots of the requested VM

        Args:
            vm (string): vm to take a snapshot of

        Returns:
            list: list of snapshots associated with that VM
        """
        
        if vm.snapshot:
            return [
                {
                    "name": snapshot.name,
                    "description": snapshot.description,
                    "create_time": snapshot.createTime.strftime("%Y-%m-%d %H:%M:%S")
                }
                for snapshot in vm.snapshot.rootSnapshotList
            ]
        return []

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def login(self):
        """
        Login into ESXi 

        Raises:
            Exception: Something went wrong     
        """
        
        try:
            self._service_instance = connect.SmartConnect(host=self._ip, user=self._user,
                                                          pwd=self._password, sslContext=context)

            content = self._service_instance.RetrieveContent()
            host_view = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.HostSystem], True)
            self._esxihost = host_view.view[0]
            
        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def logout(self):
        """
        Logout from ESXi 

        Raises:
            Exception: Something went wrong     
        """
        
        try:
            Disconnect(self._service_instance)

        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def get_info(self, filter="all"):
        """
        It obtains info from ESXi about HW and all the VMs associated as well

        Args:
            filter (string): filter on the information you want to obtain

        Returns:
            dict: Info requested

        Raises:
            Exception: Something went wrong     
        """
        
        available_filters = ["all", "hw_info", "vm_info"]
        try:
            info = {
                "hw_info": {
                    "hw model": self._esxihost.summary.hardware.model,
                    "cpuModel": self._esxihost.summary.hardware.cpuModel,
                    "numCpuCores": self._esxihost.summary.hardware.numCpuCores,
                    "numCpuThreads": self._esxihost.summary.hardware.numCpuThreads,
                    "cpuMhz": self._esxihost.summary.hardware.cpuMhz,
                    "memorySize": self._esxihost.summary.hardware.memorySize,
                    "quickStats": {
                        "overallCpuUsage": self._esxihost.summary.quickStats.overallCpuUsage,
                        "overallMemoryUsage": self._esxihost.summary.quickStats.overallMemoryUsage,
                        "uptime": self._esxihost.summary.quickStats.uptime
                    },
                    "bootTime": str(self._esxihost.runtime.bootTime),
                    "systemHealthInfo": [{"sensor_name": sensor.name, "status": sensor.currentReading} for sensor in self._esxihost.runtime.healthSystemRuntime.systemHealthInfo.numericSensorInfo]
                },
                "vm_info": [
                    {
                        "name": vm.name,
                        "status": str(vm.runtime.powerState),
                        "memory_mb": vm.summary.config.memorySizeMB,
                        "cpu_count": vm.summary.config.numCpu,
                        "guest_os": vm.summary.config.guestFullName,
                        "vmware_tools_status": str(vm.guest.toolsStatus),
                        "ip_address": vm.guest.ipAddress,
                        "datastore": vm.datastore[0].name if vm.datastore else None,
                        "resource_pool": vm.resourcePool.name if vm.resourcePool else None,
                        "uuid": vm.summary.config.uuid,
                        "host": vm.runtime.host.name,
                        "cluster": vm.resourcePool.parent.name if vm.resourcePool and vm.resourcePool.parent else None,
                        "network_adapters": [
                            {
                                "name": adapter.deviceInfo.label,
                                "mac_address": adapter.macAddress,
                            }
                            for adapter in vm.config.hardware.device if isinstance(adapter, vim.vm.device.VirtualEthernetCard)
                        ],
                        "snapshots": self.__get_snapshots(vm),
                        "cpu_usage_mhz": vm.summary.quickStats.overallCpuUsage if (vm.runtime.powerState == "poweredOn") else None,
                        "ram_usage_mb":  vm.summary.quickStats.guestMemoryUsage if (vm.runtime.powerState == "poweredOn") else None
                    }
                    for vm in self._esxihost.vm
                ]
            }

            if filter == "all" or (filter not in available_filters):
                return info
            else:
                return info[filter]

        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def check_login(self):
        """
        It neeeded to understand if the ESXi session is still operational

        Raises:
            Exception: Something went wrong
        """
        
        try:
            if self._esxihost.summary.runtime.connectionState == "connected":
                return True
            else:
                return False
        except Exception as err:
            logger.info(err)
            return False

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def vms_power_on(self, vm_names=[]):
        """
        It turns on all VMs specified in the input

        Args:
            vm_names (list): list of VM to turn on

        Returns:
            list: VMs turned on

        Raises:
            Exception: Something went wrong
        """
        
        powered_on = []
        try:
            for vm in self._esxihost.vm:
                if vm_names:
                    for vm_name in vm_names:
                        if vm["name"] == vm_name:
                            try:
                                if vm["status"] == "poweredOff":
                                    vm.PowerOn()
                                    powered_on.append(vm_name)
                            except Exception as err:
                                logger.info(err)
                                continue
                else:
                    try:
                        if vm["status"] == "poweredOff":
                            vm.PowerOn()
                            powered_on.append(vm_name)
                    except Exception as err:
                        logger.info(err)
                        continue
            return powered_on
        except Exception as err:
            logger.info(err)
            raise

    @retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def vms_power_off(self, vm_names=[]): 
        """
        It turns off all VMs specified in the input

        Args:
            vm_names (list): list of VM to turn on

        Returns:
            list: VMs turned off

        Raises:
            Exception: Something went wrong
        """
        
        powered_off = []
        try:
            for vm in self._esxihost.vm:
                if vm_names:
                    for vm_name in vm_names:
                        if vm["name"] == vm_name:
                            try:
                                if vm["status"] == "poweredOn":
                                    vm.PowerOff()
                                    powered_off.append(vm_name)
                            except Exception as err:
                                logger.info(err)
                                continue
                else:
                    try:
                        if vm["status"] == "poweredOn":
                            vm.PowerOff()
                            powered_off.append(vm_name)
                    except Exception as err:
                        logger.info(err)
                        continue

            return powered_off
        except Exception as err:
            logger.info(err)
            raise

    @ retry(delay=ACTION_DELAY, tries=ACTION_TRIES)
    def check_vms_powered_on(self):
        """
        It gets all the VMs on

        Returns:
            list: VMs currently on

        Raises:
            Exception: Something went wrong
        """
        
        powered_on = []
        try:
            for vm in self._esxihost.vm:
                try:
                    if vm["status"] == "poweredOn":
                        powered_on.append(vm.name)
                except Exception as err:
                    logger.info(err)
                    continue
            return powered_on
        except Exception as err:
            logger.info(err)
            raise
