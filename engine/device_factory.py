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

from ups import *
from firewall import *
from hypervisor import *
from controller import *
from device import *
from abc import ABC, abstractmethod
from common_libs import *
logger = Logger()


class Abstract_Factory(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def build_device(self):
        pass


class Factory_Server(Abstract_Factory):
    """
    Creational Design Pattern: Abstract Factory
    """
    
    def __init__(self):
        pass

    def build_device(self, params, manager):
        """
        The concrete factory builds server-type objects 
        Args:
            params (dict): parameters necessary for interaction with the server
            manager (BaseManager): Manager of the shared memory accessible by the workers of the multiprocessing code
        Returns:
            BaseManager: Shared memory initialized with an object of type Server
        """

        id = params["id"]
        c_ip = params["c_ip"]
        c_user = params["c_user"]
        c_pass = params["c_pass"]
        h_ip = params["h_ip"]
        h_user = params["h_user"]
        h_pass = params["h_pass"]
        c_vendor = params["vendor"]
        h_type = params.get("h_type", "esxi")

        controller_vendor = {
            "cisco": Controller_Cisco,
            "dell": Controller_Dell

        }
        hypervisor_type = {
            "esxi": ESXi
        }

        controller = controller_vendor[c_vendor](id, c_ip, c_user, c_pass)
        hv = hypervisor_type[h_type](id, h_ip, h_user, h_pass)
        return manager.server(id=id, controller=controller, hypervisor=hv)


class Factory_Security_Appliance(Abstract_Factory):
    def __init__(self):
        pass

    def build_device(self, params, manager):
        """
        The concrete factory builds server-type objects (Abstract Factory design pattern)
        Args:
            params (dict): parameters necessary for interaction with the Security_Appliance
            manager (BaseManager): Manager of the shared memory accessible by the workers of the multiprocessing code
        Returns:
            BaseManager: Shared memory initialized with an object of type Security_Appliance  
        """
        
        id = params["id"]
        ip = params["ip"]
        user = params["user"]
        passw = params["password"]
        vendor = params["vendor"]

        sa_vendor = {
            "fortinet": Firewall_Fortinet
        }
        firewall = sa_vendor[vendor](id=id, ip=ip, user=user, password=passw)
        return manager.sa(id=id, firewall=firewall)


class Factory_Power_Continuity_Appliance(Abstract_Factory):
    def __init__(self):
        pass

    def build_device(self, params, manager):
        """
        The concrete factory builds server-type objects (Abstract Factory design pattern)
        Args:
            params (dict): parameters necessary for interaction with the Power_Continuity_Appliance
            manager (BaseManager): Manager of the shared memory accessible by the workers of the multiprocessing code
        Returns:
            BaseManager: Shared memory initialized with an object of type Power_Continuity_Appliance
        """
        
        id = params["id"]
        vendor = params["vendor"]
        pid = params["pid"]

        ups_vendor = {
            "cyberpower": CyberPowerUPS
        }

        ups = ups_vendor[vendor](id=id, product_id=pid)
        return manager.pca(id=id, ups=ups)
