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
from reachability import Reachability
from power_continuity_observer import Power_Continuity_Observer
from abc import ABC
from common_libs import *
from config_loader import Config_Loader
from device_status import Device_Status
logger = Logger()



class Device(Reachability, ABC):
    def __init__(self, id):
        self._id = id

    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def logout(self):
        pass

    @abstractmethod
    def get_info():
        pass

    @abstractmethod
    def get_status():
        pass

    def id(self):
        return self._id

    def power_on(self):
        logger.warning(f"power-on device: {self._id}: no action associated!")

    def shutdown(self):
        logger.warning(f"shutdown device: {self._id}: no action associated!")


class Server(Device, Power_Continuity_Observer):

    def __init__(self, id, controller, hypervisor):
        super().__init__(id)
        self._controller = controller
        self._hypervisor = hypervisor

    @property
    def controller(self):
        return self._controller

    @property
    def hv(self):
        return self._hypervisor

    def controller_login(self):
        """
        server controller login

        Returns:
            dict: a result made by boolean and message string
        """

        try:
            self._controller.is_reachable()
            self._controller.login()
            logger.info(f"login controller server id: {self._id} OK")
            return {"result": True}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": f"can't login into controller: {err}"}

    def controller_logout(self):
        """
        server controller logout

        Returns:
            dict: a result made by boolean and message string
        """

        try:
            if self.check_controller_status()["result"]:
                self._controller.is_reachable()
                self._controller.logout()
                logger.info(f"logout controller server id: {self._id} OK")
                return {"result": True}
            else:
                return {"result": False, "msg": f"can't communicate with controller"}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": f"can't logout from controller: {err}"}

    def hypervisor_login(self):
        """
        server hypervisor login

        Returns:
            dict: a result made by boolean and message string
        """

        try:
            self._hypervisor.is_reachable()
            self._hypervisor.login()
            return {"result": True}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": f"can't logout from controller: {err}"}

    def hypervisor_logout(self):
        """
        server hypervisor logout

        Returns:
            dict: a result made by boolean and message string
        """

        try:
            if self.get_status()["result"]:
                self._hypervisor.logout()
                return {"result": True}
            else:
                {"result": False, "msg": f"can't communicate with HV"}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": f"can't logout from hypervisor: {err}"}

    def check_controller_status(self):
        """
        server controller status

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"check controller status: {self._id}")
        try:
            self._controller.is_reachable()
            res = self._controller.check_login()
            return {"result": res}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": f"can't check controller status: {err}"}

    def check_hv_status(self):
        """
        server hv status

        Returns:
            dict: a result made by boolean and message string
        """
        logger.info(f"login hv: {self._id}")
        try:
            self._hypervisor.is_reachable()
            res = self._hypervisor.check_login()
            return {"result": res}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": f"can't check controller status: {err}"}

    def get_status(self):
        """
        Get Server status

        Returns:
            dict: return a dict with the corrisponding code status
        """

        logger.info(f"server id: {self._id} getting status")
        try:

            # controller (should be always on)
            if not self.check_controller_status()["result"]:
                self.controller_login()
                if not self.check_controller_status()["result"]:
                    return {"result": Device_Status.UNREACHABLE.value}

            # hypervisor
            if not self.check_hv_status()["result"]:
                self.hypervisor_login()
                if not self.check_hv_status()["result"]:
                    return {"result": Device_Status.REACHABLE.value}
                else:
                    {"result": Device_Status.LOGGED.value}
            else:
                return {"result": Device_Status.LOGGED.value}

        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": Device_Status.UNREACHABLE.value, "msg": f"can't check server status: {err}"}

    def is_reachable(self):
        """
        check if the server is reachable, both as regards the controller and as regards the hypervisor

        Returns:
            dict: a result made by boolean and message string
        """

        controller_reachability = False
        hv_reachability = False
        try:
            self._controller.is_reachable()
            controller_reachability = True
        except (ConnectionError, Exception) as err:
            logger.info(err)

        try:
            self._hypervisor.is_reachable()
            hv_reachability = True
        except (ConnectionError, Exception) as err:
            logger.info(err)

        res = {"controller_reachability": controller_reachability,
               "hv_reachability": hv_reachability
               }
        return res

    def power_on_vms(self, vms):
        """
        Power on a list of virtual machines
        Args:
            vms (list): list of vms

        Returns:
            dict: a result made by boolean and message string
        """
        try:
            logger.info(f"hv server id: {self._id} power on vms: {str(vms)}")
            if self.get_status()["result"] == Device_Status.REACHABLE.value:
                return {"result": self._hypervisor.vms_power_on(vms)}
            else:
                return {"result": False, "msg": "can't communicate with HV"}
        except (Exception) as err:
            return {"result": False, "msg": f"can't communicate with HV: {err}"}

    def power_off_vms(self, vms):
        """
        Power off a list of virtual machines
        Args:
            vms (list): list of vms

        Returns:
            dict: a result made by boolean and message string
        """
        try:
            logger.info(f"hv server id: {self._id} power off vms: {str(vms)}")
            if self.get_status()["result"] == Device_Status.REACHABLE.value:
                return {"result": self._hypervisor.vms_power_off(vms)}
            else:
                return {"result": False, "msg": f"can't communicate with HV"}
        except (Exception) as err:
            return {"result": False, "msg": f"can't communicate with HV: {err}"}

    def get_vms_on(self):
        """
        Gets the list of running virtual machines

        Returns:
            dict: a result made by boolean and message string
        """
        try:
            logger.info(f"hv server id: {self._id} check vms on")
            if self.get_status()["result"] == Device_Status.REACHABLE.value:
                vms = self._hypervisor.check_vms_powered_on()
                return {"result": vms}
            else:
                return {"result": False, "msg": f"can't communicate with HV"}
        except (Exception) as err:
            return {"result": False, "msg": f"can't communicate with HV: {err}"}

    def get_server_power_state(self):
        """
        Gets the state of the server obtained by the controller

        Returns:
            dict: a result made by boolean and message string
        """
        try:
            logger.info(f"hv server id: {self._id} check vms on")
            if self.check_controller_status()["result"]:
                res = self._controller.get_server_power_state()
                logger.info(f"power status server id: {self._id} = {res}")
                return {"result": res}
            else:
                return {"result": False, "msg": "can't communicate with controller"}
        except (Exception) as err:
            return {"result": False, "msg": f"can't communicate with controller: {err}"}

    def power_on(self):
        """
        Power on the server

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"power-on server: {self._id}")
        try:
            if self.check_controller_status()["result"]:
                self._controller.power_on()
                return {"result": True}
            else:
                return {"result": False, "msg": f"can't communicate with controller"}
        except (Exception) as err:
            logger.info(err)
            return {"result": False, "msg": f"can't set power on server: {err}"}

    def shutdown(self):
        """
        Power off the server

        Returns:
            dict: a result made by boolean and message string
        """
        try:
            logger.info(f"power-off server: {self._id}")
            ip_r = self.is_reachable()
            if not ip_r["controller_reachability"] and not ip_r["hv_reachability"]:
                return {"result": False, "msg": f"can't communicate with HV"}

            if self.get_status()["result"] == Device_Status.LOGGED.value:
                vms_active = self._hypervisor.check_vms_powered_on()
                if vms_active == []:
                    self._controller.power_off()
                    return {"result": True}
                else:
                    return {"result": False, "msg": f"can't shut down the server with the VMs active: {str(vms_active)}"}
            else:
                return {"result": False, "msg": "can't log in the HV"}
        except (Exception) as err:
            return {"result": False, "msg": f"can't communicate with HV: {err}"}

    def get_info(self, filter="all"):
        """
        Gets info from the hypervisor

        Args:
            filter (string): filter based on hardware data, VMs data or all (default)

        Returns:
            dict: a result made by boolean and message string
        """
        try:
            logger.info(f"get info: {self._id}")
            if self.get_status()["result"] == Device_Status.LOGGED.value:
                try:
                    # self._controller.is_reachable()
                    res = self._hypervisor.get_info(filter=filter)
                    return {"result": res}
                except (ConnectionError, Exception) as err:
                    logger.info(err)
                    return {"result": False, "msg": f"can't get server info: {err}"}
            else:
                return {"result": False, "msg": f"can't communicate with HV"}
        except (Exception) as err:
            return {"result": False, "msg": f"can't communicate with HV: {err}"}

    def reboot(self):
        """
        Reboot the server

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"power-cycle server: {self._id}")
        try:
            if self.check_controller_status()["result"]:
                self._controller.is_reachable()
                self._controller.reboot()
                return {"result": True}
            else:
                return {"result": False, "msg": f"can't communicate with controller"}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": f"can't reboot the server: {err}"}

    def login(self):
        """
        Login the server

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"server: {self._id} login")
        ip_r = self.is_reachable()
        if ip_r["hv_reachability"]:
            try:
                if self.get_status()["result"]:
                    return {"result": True}
                else:
                    try:
                        self.hypervisor_login()
                        return {"result": True}
                    except Exception as err:
                        return {"result": False, "msg": err}
            except:
                try:
                    self.hypervisor_login()
                except Exception as err:
                    return {"result": False, "msg": err}
        else:
            return {"result": False, "msg": ip_r}

    def logout(self):
        """
        Logout the server

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"server : {self._id} logout")

        if self.get_status()["result"]:
            ip_r = self.is_reachable()
            if ip_r["hv_reachability"]:
                try:
                    self.hypervisor_logout()
                    return {"result": True}
                except Exception as err:
                    return {"result": False, "msg": err}
            else:
                return {"result": False, "msg": ip_r}
        else:
            return {"result": False, "msg": f"can't communicate with HV"}

    def shutdown_forced(self):
        """
        It is used to forcefully shutdown the server even if some 
        VMs are still running. In this case, them will be turned off first.
        This method is internally used by power_continuity_observer

        Returns:
            dict: a result made by boolean and message string
        """
        try:
            logger.info(f"server : {self._id} shutdown forced requested")
            ip_r = self.is_reachable()
            if not ip_r["controller_reachability"] and not ip_r["hv_reachability"]:
                return {"result": False, "msg": f"can't communicate with HV"}

            if self.get_status()["result"] == Device_Status.LOGGED.value:
                if self.power_off_vms():
                    if not self.check_controller_status()["result"]:
                        self.controller_login()
                    if self.get_server_power_state()["result"] == "on":
                        if self.set_server_power_off() and self.controller_logout():
                            return {"result": True}
                        else:
                            return {"result": False, "msg": "could not poweroff or log off from controller"}
                    else:
                        return {"result": False, "msg": "server already powered off, but could be still logged into controller"}
                else:
                    return {"result": False, "msg": "could not poweroff with running vms"}
            else:
                return {"result": False, "msg": f"can't communicate with HV"}
        except (Exception) as err:
            return {"result": False, "msg": f"can't communicate with controller: {err}"}


class Security_Appliance(Device):
    def __init__(self, id, firewall):
        super().__init__(id)
        self._fw = firewall

    def is_reachable(self):
        """
        Check if the security appliance is reachable

        Returns:
            dict: a result made by boolean and message string
        """

        try:
            self._fw.is_reachable()
            return {"result": True}
        except (ConnectionError, Exception) as err:
            return {"result": False, "msg": f"Security_Appliance not IP reachable: {err}"}

    def login(self):
        """
        Login to the security appliance

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"login Security_Appliance id: {self._id}")
        try:
            self._fw.is_reachable()
            if not self._fw.get_status():
                self._fw.login()
            return {"result": True}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": "can't login in the Security Appliance"}

    def logout(self):
        """
        Logout to the security appliance

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"logout Security_Appliance id: {self.id}")
        try:
            self._fw.is_reachable()
            if self._fw.get_status():
                self._fw.logout()
            return {"result": True}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": "can't logout from the Security Appliance"}

    def reboot(self):
        """
        Reboot the security appliance device

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"reboot security appliace: {self._id}")
        try:
            self._fw.is_reachable()
            if self._fw.get_status():
                self._fw.reboot()
                return {"result": True}
            else:
                return {"result": False}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": f"can't revoot the Security Appliance: {err}"}

    def get_info(self):
        """
        Get data info from the security appliance

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"get info Security_Appliance id: {self._id}")
        try:
            self._fw.is_reachable()
            res = self._fw.get_info()
            return {"result": res}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": f"can't get Security_Appliance info: {err}"}

    def get_status(self):
        """
        Get status from the power security appliance

        Returns:
            dict: return a dict with the corrisponding code status
        """

        logger.info(f"get info Security_Appliance id: {self._id}")
        try:
            self._fw.is_reachable()
            status = bool(self._fw.get_status())
            if status:
                return {"result": Device_Status.LOGGED.value}
            else:
                self.login()
                status = Device_Status.LOGGED.value if bool(
                    self._fw.get_status()) else Device_Status.REACHABLE.value
                return {"result": status}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": Device_Status.UNREACHABLE.value, "msg": f"can't get Security_Appliance info: {err}"}


class Power_Continuity_Appliance(Device):
    def __init__(self, id, ups):
        super().__init__(id)
        self._ups = ups

    def is_reachable(self):
        """
        Check if the power continuity appliance is still reachable

        Returns:
            dict: a result made by boolean and message string
        """

        try:
            self._ups.is_reachable()
            return {"result": True}
        except (ConnectionError,  Exception) as err:
            return {"result": False, "msg": f"UPS not reachable: {err}"}

    def login(self):
        """
        Login to the power continuity appliance

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"login UPS id: {self._id}")
        try:
            self._ups.is_reachable()
            self._ups.login()
            return {"result": True}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": "can't login in the UPS"}

    def logout(self):
        """
        Logout to the power continuity appliance

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"logout UPS id: {self._id}")
        try:
            self._ups.is_reachable()
            self._ups.logout()

            return {"result": True}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": "can't logout in the UPS"}

    def get_info(self):
        """
        Get data info from the power continuity appliance

        Returns:
            dict: a result made by boolean and message string
        """

        logger.info(f"get info for UPS id: {self._id}")
        try:
            self._ups.is_reachable()
            return {"result": self._ups.get_info()}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result": False, "msg": "can't get info from the UPS"}

    def get_status(self):
        """
        Get status from the power continuity appliance

        Returns:
            dict: return a dict with the corrisponding code status
        """

        logger.info(f"get status for UPS id: {self._id}")
        try:
            self._ups.is_reachable()
            status = bool(self._ups.get_status())
            if status:
                return {"result": Device_Status.LOGGED.value}
            else:
                self.login()
                status = Device_Status.LOGGED.value if bool(
                    self._ups.get_status()) else Device_Status.REACHABLE.value
                return {"result": status}
        except (ConnectionError,  Exception) as err:
            logger.info(err)
            return {"result":  Device_Status.UNREACHABLE.value, "msg": "can't get status from the UPS:"}
