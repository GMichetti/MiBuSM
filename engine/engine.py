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

import time
from multiprocessing import Process
from multiprocessing.managers import BaseManager
import inspect
from device_factory import *
from common_libs import *
from power_continuity_observer import Power_Continuity_Status
from config_loader import Config_Loader
from worker import Worker
from message_broker import Queue
from internal_db import Internal_DB

config_loader = Config_Loader()
logger = Logger()

PROCESSORS = config_loader.config["max_workers"]
HEARTBEAT = config_loader.config["polling_cycle_heartbeat"]
WAITING_TIME = config_loader.config["waiting_time"]
MSG_BROKER = config_loader.config["msg_broker"]
REQUEST_QUEUE = config_loader.config["msg_broker_request_queue"]
DB = config_loader.config["internal_db"]
DEV_LIST_COLLECTION = config_loader.config["internal_db_devs_list"]
DEV_INFO_COLLECTION = config_loader.config["internal_db_devs_info"]


class Engine(object):

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Engine, cls).__new__(cls)
            cls._devices_created = list()
            cls._power_continuity_observers = list()
            cls._extra = dict()
            cls._request_queue = None
            cls.dev_list_db = None
            cls._dev_info_db = None
            cls._power_continity_subject = None
            cls._power_continuity_status = None
            cls._f_reset_engine = False

        return cls._instance

    @property
    def devices_created(self):
        return self._devices_created

    def _get_device_by_id(self, id):
        """
        Get device object from the id

        Args:
            id (string): device id

        Returns:
            device: device object related to the id

        Raises:
            ValueError: more than one device with the same device id
        """

        dev = [dev for dev in self._devices_created if dev.id() == id]
        if len(dev) == 0:
            logger.error("Error: No device instantiated with the id: {id}")
        elif len(dev) > 1:
            logger.error(
                "Error: More than one device associated with the id: {id}")
            raise ValueError(
                "Error: More than one device associated with the id")
        else:
            return dev[0]

    def _build_devices(self, devices_to_create: list, manager: BaseManager):
        """
        build the devices via Factory 

        Args:
            devices_to_create (list): device id
            manager (BaseManager): necessary to be able to access the device by different workers (multiprocessing)

        Raises:
            ValueError: more than one device with the same device id
        """

        factory_selector = {
            "server": Factory_Server,
            "firewall": Factory_Security_Appliance,
            "ups": Factory_Power_Continuity_Appliance
        }
        self.dev_list_db.insert({"devs_list": devices_to_create})
        for dev in devices_to_create:
            factory = factory_selector[dev["dev_type"]]()
            instance = factory.build_device(dev, manager)
            self._devices_created.append(instance)

    def _build_power_continuity_observers(self, manager):
        """
        Build all the observers (devices that need to be notified if the power continuity appliance loses power)

        Args:
            manager (BaseManager): necessary to be able to access the device by different workers (multiprocessing)

        Returns:
            object: with the status and the subject or a empty dict if power continuity appliance is found
        """

        self._power_continuity_observers = [
            dev for dev in self._devices_created if "shutdown_forced" in dir(dev)]

        self._power_continity_subject = next((dev for dev in self._devices_created if type(
            dev).__name__ == "AutoProxy[pca]"), None)

        if self._power_continity_subject is not None:

            power_continuity_status = manager.pcs()
            [power_continuity_status.subject_attach(
                observer) for observer in self._power_continuity_observers]

            return {"power_continuity_status": power_continuity_status,
                    "power_continuity_subject_id": self._power_continity_subject.id()}

        else:
            logger.info("No Power Continuity Appliance found")
            return {}

    def _spawn_processors(self):
        """
        Starts a new process (up to a preset limit) for each action injected into the engine

        Raises:
            Exception: any problem found during this process
        """

        try:
            processes = []
            for _ in range(PROCESSORS):
                if self._request_queue.get_length() > 0:
                    data = self._request_queue.dequeue()
                    if "reset" in data:
                        self._f_reset_engine = True
                        break
                    device_id = data["id"]
                    action = data["action"]
                    params = data.get("params", None)
                    processes.append(Process(target=Worker.dispatcher, args=(
                        self._get_device_by_id(device_id), device_id, action, params, self._extra)))
            for process in processes:
                process.start()
            for process in processes:
                process.join()
        except Exception as err:
            logger.info(err)
            raise

    def _initialize_broker_and_db(self):
        """
        Initialize message broker and db

        Raises:
            Exception: in problem is found during initalization (exit from the process)
        """

        logger.info("initializing message broker...")
        try:
            self._request_queue = Queue(MSG_BROKER, REQUEST_QUEUE)
            self.dev_list_db = Internal_DB(DB, DEV_LIST_COLLECTION)
            self._dev_info_db = Internal_DB(DB, DEV_INFO_COLLECTION)
        except Exception as err:
            logger.error(f"can't initialize msg broker and/or db: {err}")
            exit(0)

    def _initialize_shared_mem(self):
        """
        Initialize shared memory

        Raises:
            Exception: in problem is found during initalization (exit from the process)
        """

        logger.info("initializing shared memory/proxy device objects")
        BaseManager.register('server', Server)
        BaseManager.register('sa', Security_Appliance)
        BaseManager.register('pca', Power_Continuity_Appliance)
        BaseManager.register('pcs', Power_Continuity_Status)

    def _status_reset(self, mem_n_db=True, queue=True):
        """
        Broker queue flushed or/and all collections and memory dropped

        Args:
            mem_n_db (booean): drop db and shared memory
            queue(boolean): flush message broker queue

        Raises:
            Exception: in problem is found during reset (exit from the process)
        """
        if mem_n_db:
            try:
                logger.info("reset engine memory and/or db")
                self.dev_list_db.clean_collection()
                # self._dev_info_db.clean_collection()
                self._devices_created = list()
                self._power_continuity_observers = list()
                self._power_continity_subject = None
                self._f_reset_engine = False
            except Exception as err:
                logger.error(f"can't reset engine memory: {err}")
                exit(0)
        if queue:
            try:
                logger.info("reset engine queue")
                self._request_queue.flush_queue()
            except Exception as err:
                logger.error(f"can't reset engine status: {err}")
                exit(0)

    def start_n_run_engine(self):
        """
        Core method. It searches for new actions to perform getting them from the message broker

        Raises:
            Exception: in problem is found during the running (exit from the process)
        """

        self._initialize_broker_and_db()
        self._initialize_shared_mem()

        while True:
            with BaseManager() as manager:
                while True:
                    try:
                        if self._request_queue.get_length() == 0:
                            logger.info(
                                "Waiting for incoming messages from Service...")
                            time.sleep(WAITING_TIME)
                            continue
                        else:
                            logger.info("new message ready")
                            break
                    except Exception as err:
                        logger.error(
                            f"can't initialize get initial mgs: {err}")
                        exit(0)

                msg = None
                try:
                    logger.info("extracting the message from the queue")
                    msg = self._request_queue.dequeue()
                except Exception as err:
                    logger.error(
                        f"can't get device to build: {err}")

                if "reset" in msg:
                    logger.info("resetting engine!")
                    self._status_reset(mem_n_db=True, queue=False)

                elif "build" in msg:
                    try:
                        self._build_devices(msg["build"], manager)
                        logger.info("building power continuity observers")
                        self._extra["power_continuity"] = self._build_power_continuity_observers(
                            manager)
                        self._status_reset(mem_n_db=False, queue=True)
                    except Exception as err:
                        logger.error(
                            f"can't build the devices: {err}")

                    time.sleep(WAITING_TIME)
                    logger.info("starting polling devices...")

                    while True:
                        try:
                            self._spawn_processors()
                            time.sleep(HEARTBEAT)
                            if self._f_reset_engine == True:
                                logger.info("engine reset !")
                                self._status_reset(mem_n_db=True, queue=False) 
                                time.sleep(WAITING_TIME)
                                break
                        except Exception as err:
                            logger.error(
                                f"error during core loop: {err}")
                            continue
                else:
                    while True:
                        try:
                            if self._request_queue.get_length() > 0:
                                self._request_queue.dequeue()
                                continue
                            else:
                                break
                        except Exception as err:
                            logger.error(
                                f"can't reset initial msgs: {err}")
                            exit(0)


def run():
    e = Engine()
    e.start_n_run_engine()


if __name__ == "__main__":
    run()
