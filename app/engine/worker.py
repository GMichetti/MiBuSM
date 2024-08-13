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
from common_libs import *
from config_loader import Config_Loader
from internal_db import Internal_DB
from action_status import Action_Status

config_loader = Config_Loader()
logger = Logger()


BATTERY_LOWER_THRESHOLD = config_loader.config["battery_lower_threshold"]
DB = config_loader.config["internal_db"]
HISTORY_MAX_SIZE = config_loader.config["history_max_size"]
DEV_INFO_COLLECTION = config_loader.config["internal_db_devs_info"]
ACTION_STATUS_LIST_COLLECTION = config_loader.config["internal_db_action_status_list"]


class Worker():

    @staticmethod
    def dispatcher(device, device_id, action, params, extra):
        """
        It forwards the action to the correct method between:
            - perform_action_on_device
            - check_power_continuity

        Args:
            device (dict): an object representing the device
            device_id (string): device id
            action (string): action to perform
            params (list): list of params if the action needed them
            extra (dict): power continuity data
        """

        if (extra["power_continuity"] and
            extra["power_continuity"].get("power_continuity_subject_id", None) == device_id and
                action["action"] == "get_info"):
            Worker.check_power_continuity(
                device, device_id, action, extra)
        else:
            Worker.perform_action_on_device(device, device_id, action, params)

    @staticmethod
    def perform_action_on_device(device, device_id, action, params):
        """
        It performs the action against regular device

        Args:
            device (dict): an object representing the device
            device_id (string): device id
            action (string): action to perform
            params (list): list of params if the action needed them

        Raises:
            Exception: if something went wrong
        """

        try:
            logger.info(
                f"performing the action {action['action']} against device {device_id}")
            action_status_db = Internal_DB(DB, ACTION_STATUS_LIST_COLLECTION)
            action_status_db.update_one(
                {"action_id": action['action_id']}, "action_status", Action_Status.DISPATCHED.value)

            dev_info_db = Internal_DB(DB, DEV_INFO_COLLECTION)
            result = {"result": getattr(device, action["action"])() if not bool(params) else getattr(device, action["action"])(*params),
                      "req_timestamp": action["action_time_req"],
                      "res_timestamp": time.time(),
                      "delta_t": time.time() - action["action_time_req"],
                      "action_id": action["action_id"]
                      }
            criteria = {"_id": device_id}
            dev_info_db.push_one(
                criteria, action["action"], result, HISTORY_MAX_SIZE)
            action_status_db.update_one(
                {"action_id": action['action_id']}, "action_status", Action_Status.COMPLETED.value)
        except Exception as err:
            action_status_db.update_one(
                {"action_id": action['action_id']}, "action_status", Action_Status.ERROR.value)
            logger.error(
                f"Error while action {action['action']} against device {device_id}: {err}")
            raise
        finally:
            dev_info_db.close_conn()
            

    @staticmethod
    def check_power_continuity(device, device_id, action, extra):
        """
        It performs a check against the power continuity device

        Args:
            device (dict): an object representing the device
            device_id (string): device id
            action (string): action to perform
            extra (dict): power continuity data

        Raises:
            Exception: if something went wrong
        """

        try:
            logger.info(
                f"performing the check power continuity action against device {device_id}")
            action_status_db = Internal_DB(DB, ACTION_STATUS_LIST_COLLECTION)
            action_status_db.update_one(
                {"action_id": action['action_id']}, "action_status", Action_Status.DISPATCHED.value)

            result = {"result": getattr(device, action["action"])(),
                      "req_timestamp": action["action_time_req"],
                      "res_timestamp": time.time(),
                      "delta_t": time.time() - action["action_time_req"],
                      "action_id": action["action_id"]
                      }
            dev_info_db = Internal_DB(DB, DEV_INFO_COLLECTION)
            ps = result.get("result", {}).get("result", None)
            if ps.get("ac", None) and (ps.get("battery", None) <= BATTERY_LOWER_THRESHOLD):
                extra["power_continuity"]["power_continuity_status"].subject_notify()

            criteria = {"_id": device_id}
            dev_info_db.push_one(
                criteria, action["action"], result, HISTORY_MAX_SIZE)
            action_status_db.update_one(
                {"action_id": action['action_id']}, "action_status", Action_Status.COMPLETED.value)
        except Exception as err:
            action_status_db.update_one(
                {"action_id": action['action_id']}, "action_status", Action_Status.ERROR.value)
            logger.error(
                f"Error while action {action['action']} against device {device_id}: {err}")
            raise
        finally:
            dev_info_db.close_conn()
            
