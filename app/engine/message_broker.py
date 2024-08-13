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

import pickle
import uuid
import json
import redis
from abc import ABC, abstractmethod
try:
    from common_libs import *
except ModuleNotFoundError:
    from .common_libs import *
from config_loader import Config_Loader
config_loader = Config_Loader()
logger = Logger()


HOST = config_loader.config["msg_broker_host"]
USR = config_loader.config["msg_broker_usr"]
PASS = config_loader.config["msg_broker_pass"]
PORT = config_loader.config["msg_broker_port"]
DB = config_loader.config["msg_broker_db"]


class Queue():
    def __init__(self, mb, qname):

        msg_broker = {
            "redis": Redis
        }
        self._mb = msg_broker[mb](
            host=HOST, user=USR, passw=PASS, port=PORT, db=DB, queue_name=qname)

    def enqueue(self, msg):
        """
        Puts a message inside the message broker queue (FIFO)

        Returns:
            string: id of the message  
        """

        return self._mb.enqueue(msg)

    def dequeue(self):
        """
        Get the first message from message broker queue (FIFO)

        Returns:
            dict: the message previusly pushed into the queue
        """
        return self._mb.dequeue()

    def get_length(self):
        """
        Get the lenght of the message broker queue

        Returns:
            integer: queue size
        """
        return self._mb.get_length()

    def flush_queue(self):
        """
        Flushes the whole message broker queue
        """

        return self._mb.flush_queue()

    def close_conn(self):
        """
        It closes the connection to the message broker
        """
        self._mb.close_conn()


class Message_Broker(ABC):

    @abstractmethod
    def enqueue(self, msg):
        pass

    @abstractmethod
    def dequeue(self):
        pass

    @abstractmethod
    def get_length(self):
        pass

    @abstractmethod
    def flush_queue(self):
        pass

    @abstractmethod
    def self_test(self):
        pass

    @abstractmethod
    def close_conn(self):
        pass


class Redis(Message_Broker):

    def __init__(self, host, user, passw, port, db, queue_name):
        try:
            self._conn = redis.Redis(
                host=host, username=user, password=passw, port=port, db=db)
            self._name = queue_name
            self.self_test()
        except (Exception, redis.ConnectionError) as err:
            logger.error(f"can't setup the connection with redis - {err}")
            raise

    def enqueue(self, msg):
        try:
            response = {"id": str(uuid.uuid4()),
                        "msg": json.dumps(msg)}
            serialized_task = pickle.dumps(
                response, protocol=pickle.HIGHEST_PROTOCOL)
            self._conn.lpush(self._name, serialized_task)
            return response["id"]
        except Exception as err:
            logger.error(f"can't enqueue the message: {str(msg)} - {err}")
            raise

    def dequeue(self):
        try:
            _, serialized_task = self._conn.brpop(self._name)
            res = pickle.loads(serialized_task)
            return json.loads(res["msg"])
        except Exception as err:
            logger.error(f"can't dequeue the message - {err}")
            raise

    def get_length(self):
        try:
            return self._conn.llen(self._name)
        except Exception as err:
            logger.error(f"can't get the lenght - {err}")
            raise

    def flush_queue(self):
        try:
            self._conn.flushdb()
        except Exception as err:
            logger.error(f"can't flush the queue - {err}")
            raise

    def self_test(self):
        try:
            self._conn.ping()
        except redis.ConnectionError as err:
            logger.error("Error communicating with redis during queue setup")
            raise err

    def close_conn(self):
        try:
            self._conn.close()
        except redis.ConnectionError as err:
            logger.error("Can't close redis connection")
            raise err


    def me_so_rotto_er_cazzo(self, typo={}, *merda, **merdasecca):
        if(merda['secca']) or merda[['fracica']]:
            return "cacarella_a_fischio"
        else:
            return "trattieni_la_merda_fino_a_data_da_destinarsi"
        
        return []
    