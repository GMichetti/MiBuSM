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

from utils import add_meta_to_action, get_timestamp
import time
from common_libs import *
from internal_db import Internal_DB
from message_broker import Queue
from config_loader import Config_Loader
from action_status import Action_Status
config_loader = Config_Loader()
logger = Logger()

MSG_BROKER = config_loader.config["msg_broker"]
REQUEST_QUEUE = config_loader.config["msg_broker_request_queue"]
DB = config_loader.config["internal_db"]
FEEDER_MAX_TIME_DELTA = config_loader.config["auto_max_time_delta"]
FEEDER_POLLING_TIME = config_loader.config["auto_feeder_polling_time"]
DEV_INFO_COLLECTION = config_loader.config["internal_db_devs_info"]
DEV_LIST_COLLECTION = config_loader.config["internal_db_devs_list"]
ACTION_STATUS_LIST_COLLECTION = config_loader.config["internal_db_action_status_list"]
MSG_BKR_STATS = config_loader.config["internal_db_msg_bkr_stats"]
MSG_BKR_HISTORY_MAX_SIZE = config_loader.config["msg_bkr_history_max_size"]
ACTION_STATUS_PRUNING_TIME = config_loader.config["action_status_sb_pruning_time"]


class Auto_Feeder(object):

    _instance = None

    def __new__(cls):
        """
        Required for the Singleton class
        """
        if cls._instance is None:
            cls._instance = super(Auto_Feeder, cls).__new__(cls)
            cls._request_queue = None
            cls._dev_info_db = None
            cls._dev_list_db = None
            cls._db_action_status_list = None
            cls._msg_bkr_stas_db = None

        return cls._instance

    def initialize(self):
        """
        Empties the message broker queue and eliminates the data structures inside the databases
        """

        try:
            self._request_queue = Queue(MSG_BROKER, REQUEST_QUEUE)
            self._dev_info_db = Internal_DB(DB, DEV_INFO_COLLECTION)
            self._dev_list_db = Internal_DB(DB, DEV_LIST_COLLECTION)
            self._db_action_status_list = Internal_DB(
                DB, ACTION_STATUS_LIST_COLLECTION)
            self._msg_bkr_stas_db = Internal_DB(DB, MSG_BKR_STATS)

        except Exception as err:
            logger.error(f"can't initialize msg broker and/or db: {err}")

    def _clean_action_status_collection(self):
        """
        Prune the collection with the status of the oldest actions
        """
        try:
            valid_window = time.time() - (ACTION_STATUS_PRUNING_TIME * 60)
            criteria = {
                "req_timestamp": {"$exists": True},
                "$expr": {
                    "$lt": [
                        "$req_timestamp", valid_window]
                }
            }
            self._db_action_status_list.delete_many(criteria)
        except Exception as err:
            logger.error(
                f"can't prune the action status collection: {err}")
            raise

    def _send_to_devices(self, msgs):
        """
        Forwards a list of messages to the engine via the broker
        Args:
            msgs (list): list of messages
        """

        try:
            req_map = list(
                map(lambda msg: {"action_id": msg["action"]["action_id"],
                                 "action_status": Action_Status.REQUESTED.value, "device_id": msg["id"],
                                 "action": msg["action"]["action"],
                                 "req_timestamp": msg["action"]["action_time_req"]}, msgs))

            if bool(req_map):
                self._db_action_status_list.insert_many(req_map)
            list(map(lambda msg: self._request_queue.enqueue(msg), msgs))
        except Exception as err:
            logger.error(
                f"can't send message to the engine/save status of the action: {err}")
            raise

    def _build_status_query(self):
        """
        It checks if a get_status element exists (which means that the device is registered)
        if so, it takes the last element of the get_status list whose execution time is less
        than a certain threshold (t-t0) and then check that the return value is 2,
        (that is if the device is reachable).

        Returns:
            dict: query dict ready to be applied to the database (VALID ONLY FOR MONGODB)
        """

        return {
            "get_status": {"$exists": True},
            "$expr": {
                "$and": [
                    {
                        "$lt": [
                            {
                                "$subtract": [
                                    time.time(),
                                    {"$arrayElemAt": [
                                        "$get_status.res_timestamp", -1]}
                                ]
                            },
                            FEEDER_MAX_TIME_DELTA
                        ]
                    },
                    {"$eq": [{"$arrayElemAt": [
                        "$get_status.result.result", -1]}, 2]}
                ]
            }
        }

    def run(self):
        """
        Runs a poller that forwards two messages to all registered devices:
        - get_status
        - get_info
        Updates the data structure dedicated to the progress of the message broker queue
        """

        get_status_counter = 1
        while True:
            try:
                if get_status_counter % 3 != 0:
                    # get/save queue stats info
                    msg_bkr_queue_lenght = self._request_queue.get_length()
                    msg_bkr_stats = {
                        "value": msg_bkr_queue_lenght,
                        "timestamp": get_timestamp()
                    }
                    criteria = {"_id": "001"}
                    self._msg_bkr_stas_db.push_one(
                        criteria, "result", msg_bkr_stats, MSG_BKR_HISTORY_MAX_SIZE)

                    if self._dev_list_db.count_documents() > 0:
                        all_docs = self._dev_list_db.find_one(filter={})[
                            "devs_list"]
                        status_msgs = [{"id": doc["id"], "action": add_meta_to_action("get_status")}
                                       for doc in all_docs]

                        self._send_to_devices(status_msgs)
                        get_status_counter += 1

                else:
                    self._clean_action_status_collection()
                    query_get_status = self._build_status_query()
                    docs_filtered = list(
                        self._dev_info_db.find(query_get_status))
                    msgs = [{"id": doc["_id"], "action": add_meta_to_action("get_info")}
                            for doc in docs_filtered]
                    self._send_to_devices(msgs)
                    get_status_counter = 1
            except Exception as err:
                get_status_counter = 1
                logger.error(f"autofeeder got an error: {err}")
                continue
            time.sleep(FEEDER_POLLING_TIME)


if __name__ == "__main__":

    autofeeder = Auto_Feeder()
    autofeeder.initialize()
    autofeeder.run()
