from utils import add_meta_to_action
from config_loader import Config_Loader
from common_libs import *
from internal_db import Internal_DB
from message_broker import Queue
import unittest
import time
import sys
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


config_loader = Config_Loader()
MSG_BROKER = config_loader.config["msg_broker"]
REQUEST_QUEUE = config_loader.config["msg_broker_request_queue"]
DB = config_loader.config["internal_db"]
DEV_INFO_COLLECTION = config_loader.config["internal_db_devs_info"]
DEV_LIST_COLLECTION = config_loader.config["internal_db_devs_list"]

request_queue = Queue(MSG_BROKER, REQUEST_QUEUE)
db_devs_info = Internal_DB(DB, DEV_INFO_COLLECTION)
db_devs_list = Internal_DB(DB, DEV_LIST_COLLECTION)


devs = [
    {
        "id": "003",
        "name": "Toki",
        "dev_type": "firewall",
        "vendor": "fortinet",
        "ip": "PUT_HERE_THE_ADDRESS",
        "user": "PUT_HERE_THE_USER",
        "password": "PUT_HERE_THE_PASSWORD"
    },
    {
        "id": "002",
        "name": "Raoh",
        "dev_type": "ups",
        "vendor": "cyberpower",
        "pid": 0x0501
    },
    {
        "id": "001",
        "name": "Ken",
        "dev_type": "server",
        "vendor": "dell",
        "c_ip": "PUT_HERE_THE_ADDRESS",
        "c_user": "PUT_HERE_THE_USER",
        "c_pass": "PUT_HERE_THE_PASSWORD",
        "h_type": "esxi",
        "h_ip": "PUT_HERE_THE_ADDRESS",
        "h_user": "PUT_HERE_THE_USER",
        "h_pass": "PUT_HERE_THE_PASSWORD"
    }
]


class TestEngine(unittest.TestCase):

    def test_01_e2e(self):
        print("test_01_e2e")
        print("creating devs")
        request_queue.enqueue({"build": devs})
        time.sleep(5)

        print("login...")
        msg = {"id": "003", "action": add_meta_to_action("login")}
        request_queue.enqueue(msg)

        msg = {"id": "002", "action": add_meta_to_action("login")}
        request_queue.enqueue(msg)

        msg = {"id": "001", "action": add_meta_to_action("login")}
        request_queue.enqueue(msg)

        time.sleep(10)
        print("get info...")
        msg = {"id": "003", "action": add_meta_to_action("get_info")}
        request_queue.enqueue(msg)
        msg = {"id": "002", "action": add_meta_to_action("get_info")}
        request_queue.enqueue(msg)
        msg = {"id": "001", "action": add_meta_to_action("get_info")}
        request_queue.enqueue(msg)

        time.sleep(30)
        ids = ["003", "002", "001"]
        res = list()
        for id in ids:
            res.append(db_devs_info.find_one({"_id": id}))
        self.assertTrue(res)
        print(res)

    def test_02_restart(self):
        print("test_02_restart")
        print("resetting engine")
        request_queue.enqueue({"reset": []})
        time.sleep(10)

        print("creating devs")
        request_queue.enqueue({"build": [devs[0]]})
        time.sleep(5)

        time.sleep(10)
        print("login...")
        msg = {"id": "003", "action": add_meta_to_action("login")}
        request_queue.enqueue(msg)

        time.sleep(30)
        ids = ["003"]
        res = list()
        for id in ids:
            res.append(db_devs_info.find_one({"_id": id}))
        self.assertTrue(res)
        print(res)


if __name__ == '__main__':
    unittest.main()
