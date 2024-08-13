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
from .common_libs import *
from .internal_db import Internal_DB
from .message_broker import Queue
from config_loader import Config_Loader
from operator import itemgetter
from .utils import add_meta_to_action, get_object_by_action_id
from .action_status import Action_Status
config_loader = Config_Loader()
logger = Logger()

MSG_BROKER = config_loader.config["msg_broker"]
REQUEST_QUEUE = config_loader.config["msg_broker_request_queue"]
DB = config_loader.config["internal_db"]
DEV_INFO_COLLECTION = config_loader.config["internal_db_devs_info"]
DEV_LIST_COLLECTION = config_loader.config["internal_db_devs_list"]
ACTION_STATUS_LIST_COLLECTION = config_loader.config["internal_db_action_status_list"]
MSG_BKR_STATS = config_loader.config["internal_db_msg_bkr_stats"]
LOGS_PATH = config_loader.config["log_file_path"]


class Service(object):

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Service, cls).__new__(cls)
            cls._request_queue = None
            cls._db_devices_info = None
            cls._db_devices_list = None
            cls._db_action_status_list = None
            cls._msg_bkr_stas_db = None

        return cls._instance

    def initialize(self):
        """
        It initializes DB and the message broker

        Returns:
            boolean: True, if it's all ok

        """
        try:
            self._request_queue = Queue(MSG_BROKER, REQUEST_QUEUE)
            self._db_devices_info = Internal_DB(DB, DEV_INFO_COLLECTION)
            self._db_devices_list = Internal_DB(DB, DEV_LIST_COLLECTION)
            self._db_action_status_list = Internal_DB(
                DB, ACTION_STATUS_LIST_COLLECTION)
            self._msg_bkr_stas_db = Internal_DB(DB, MSG_BKR_STATS)
            return True
        except Exception as err:
            logger.error(f"can't initialize msg broker and/or db: {err}")
            return False

    def get_msg_bkr_queue(self):
        """
        It initializes DB and the message broker

        Returns:
            dict: data representing the message broker queue lenght values
            with a timestamp for each value
        """

        try:
            data = list(self._msg_bkr_stas_db.find({"_id": "001"}))[0]
            return data
        except Exception as err:
            logger.error(f"can't get mibu msg broker queue history: {err}")
            return {}

    def get_throughput(self, dev_list):
        """
        It returns a list of througput values of MiBu (Job/s).
        Each value has a timestamp associated

        Args:
            dev_list (float): list of devices

        Returns:
            list: list of throughput values
        """

        try:
            ids = list(map(itemgetter("id"), dev_list))
            data = list(self._db_devices_info.find({"_id": {"$in": ids}}))
        except Exception as err:
            logger.error(f"can't get mibu througput: {err}")
            return []

        all_devs_delta = []
        for dev in data:
            dev_delta = []
            for el in dev["get_status"]:
                dev_delta.append(
                    {"delta": el['delta_t'], "timestamp": el['res_timestamp']})
            all_devs_delta.append(dev_delta)

        min_length = min(len(lst) for lst in all_devs_delta)
        for lst in all_devs_delta:
            while len(lst) > min_length:
                lst.pop(0)

        res = []
        if len(all_devs_delta) > 0:
            avg_delta = []
            dev_len = len(data)
            delta_len = len(all_devs_delta[0])

            for idx in range(delta_len):
                delta_tmp = 0
                timestamp_tmp = 0
                for group in all_devs_delta:

                    delta_tmp = delta_tmp + group[idx]['delta']
                    timestamp_tmp = timestamp_tmp + group[idx]['timestamp']
                    avg_delta.insert(
                        idx, {"delta": delta_tmp, "timestamp": timestamp_tmp})

                avg_delta[idx]["delta"] /= dev_len
                avg_delta[idx]["timestamp"] /= dev_len
                res.append(
                    {"delta": pow(avg_delta[idx]["delta"], -1), "timestamp": avg_delta[idx]["timestamp"]})

        return res

    def read_log_files(self):
        """
        It returns all the log files 

        Returns:
            list: list of strings representing the logs
        """

        path_splitted = []

        if os.name == 'posix':
            path_splitted = LOGS_PATH.split("/")
            path_splitted[0]= '/'
        else:
            path_splitted = LOGS_PATH.split("\\")
            path_splitted.insert(1, "\\")

        folder = os.path.join(*path_splitted[:-1])

        if not os.path.exists(folder):
            logger.error(f"The logs folder '{folder}' doesn't exist")
            return []

        contents = []
        try:
            file_path = os.path.join(folder, path_splitted[-1])
            with open(file_path, 'r') as f:
                content = f.read()
                contents.append(content)
        except Exception as err:
            logger.error(f"can't extract data from log files")
            return []

        return contents

    def register_devices(self, devs: list):
        """
        It register the devices to be used by the engine

        Args:
            devs (list): list of devicecs to be registered

        Returns:
            booean: True, if it's all ok
        """

        try:
            self._request_queue.enqueue({"build": devs})
            return True
        except Exception as err:
            logger.error(f"can't send message to register devices: {err}")
            return False

    def reset_engine(self):
        """
        Message headed to the engine to force a reset of the engine itself
        """

        try:
            self._request_queue.enqueue({"reset": []})
            return True
        except Exception as err:
            logger.error(f"can't send message to reset engine: {err}")
            return False

    def get_action_status(self, action_ids):
        """
        Return the status of a given actions

        Args:
            action_ids(list): uuid representing a a list of action

        Returns:
            enum: status of the selected actions
        """

        results = []
        for action_id in action_ids:
            try:
                criteria = {"action_id": action_id}
                res_from_action_status_db = self._db_action_status_list.find_one(
                    criteria)
                if res_from_action_status_db:

                    res = {"action_id": res_from_action_status_db["action_id"], "action_status": Action_Status(
                        res_from_action_status_db["action_status"]).name}

                    if Action_Status(res_from_action_status_db["action_status"]) == Action_Status.COMPLETED:
                        criteria = {
                            "_id": res_from_action_status_db["device_id"]}
                        res_from_devices_info_db = self._db_devices_info.find_one(
                            criteria)
                        global_action = res_from_devices_info_db.get(res_from_action_status_db["action"], "")
                        if global_action:
                            res.update({"result": get_object_by_action_id(
                                global_action, res_from_action_status_db["action_id"])})

                    results.append(res)
                else:
                    results.append({action_id: False})
            except Exception as err:
                logger.error(
                    f"can't get the status of the selected action: {err}")
                results.append({action_id: False})
        return results
    

    def send_to_devices(self, msgs):
        """
        Send messages/commands to devices

        Args:
            msgs (dict): messages to devices including the id of the device

        Returns:
            boolean: True, if it's all ok
        """

        try:

            msgs_enh = list(map(lambda msg: {
                            "id": msg["id"], "action": add_meta_to_action(msg["action"])}, msgs))

            req_map = list(
                map(lambda msg: {"action_id": msg["action"]["action_id"],
                                 "action_status": Action_Status.REQUESTED.value,
                                 "device_id": msg["id"],
                                 "action": msg["action"]["action"],
                                 "req_timestamp": msg["action"]["action_time_req"]}, msgs_enh))
            self._db_action_status_list.insert_many(req_map)

            list(map(lambda msg: self._request_queue.enqueue(msg), msgs_enh))
            return True
        except Exception as err:
            logger.error(f"can't send requested commands to devices: {err}")
            return False

    def get_registered_device_by_id(self, id):
        """
        Get registered device by id

        Args:
            id (string): device id

        Returns:
            dict: device, None if not found
        """

        reg_devs = self.get_registered_devices()
        for dev in reg_devs:
            if dev['id'] == id:
                return dev
        return None

    def get_registered_devices(self, only_ids=False):
        """
        Get all registered devices (id,name,dev_type_h_ip attributes)

        Args:
            only_ids (boolean): if you need only the id for each device

        Returns:
            list: all registered devices
        """

        dev_list = list(self._db_devices_list.find({}))
        if len(dev_list) > 0:
            dev_list = dev_list[0].get("devs_list", [])
            params = ["id"] if only_ids else [
                "id", "name", "dev_type", "ip", "h_ip"]
            return list(map(lambda x: {param: x[param] if param in x else "_" for param in params}, dev_list))
        else:
            return []

    def get_data_from_devices(self, dev_list):
        """
        Get data from devices

        Args:
            dev_list (list): list of devices you want to get data from

        Returns:
            list: data for each device of the dev_list 
        """

        try:
            ids = list(map(itemgetter("id"), dev_list))
            data = list(self._db_devices_info.find({"_id": {"$in": ids}}))
            dev_map = {dev["id"]: dev for dev in dev_list}
            for d in data:
                dev = dev_map.get(d["_id"])
                if dev:
                    d["name"] = dev["name"]
                    d["type"] = dev["dev_type"]
                    d["ip_address"] = dev.get("ip", "")

            return data

        except Exception as err:
            logger.error(f"can't get info requested from devices: {err}")
            return []

    def get_data_from_device_model(self, devices):
        """
        Get data from the device model

        Args:
            devices (list): list of devices got from the model

        Returns:
            list: data for each device
        """

        result = []
        for device in devices:
            device_dict = {
                "id": str(device["id"]),
                "name": device["name"],
                "dev_type": device["device_type"],
                "vendor": device["vendor"],
            }

            optional_fields = {
                "c_ip": device["c_ip"],
                "c_user": device["c_user"],
                "c_pass": device["c_pass"],
                "h_type": device["h_type"],
                "h_ip": device["h_ip"],
                "h_user": device["h_user"],
                "h_pass": device["h_pass"],
                "ip": device["ip"],
                "user": device["user"],
                "password": device["password"],
                "pid": device["pid"]
            }

            for key, value in optional_fields.items():
                if key in device and device[key] != "":
                    device_dict[key] = value

            result.append(device_dict)

        return result
