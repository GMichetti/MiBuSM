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

from pymongo import MongoClient, errors as pyErr
from abc import ABC, abstractmethod
try:
    from common_libs import *
except ModuleNotFoundError:
    from .common_libs import *
from config_loader import Config_Loader
config_loader = Config_Loader()
logger = Logger()


HOST = config_loader.config["internal_db_host"]
USR = config_loader.config["internal_db_usr"]
PASS = config_loader.config["internal_db_pass"]
PORT = config_loader.config["internal_db_port"]
DB = config_loader.config["internal_db_database"]


class Internal_DB():
    def __init__(self, db, collection):
        internal_db = {
            "mongodb": MongoDB
        }
        self._db = internal_db[db](
            host=HOST, user=USR, passw=PASS, port=PORT, db=DB, collection=collection)

    def insert(self, obj):
        """
        Insert an element inside a collection

        Args:
            obj (dict): object that needs to be inserted in the collection
        """

        self._db.insert(obj)

    def insert_many(self, objs):
        """
        Insert a list of elements inside a collection

        Args:
            objs (list): object that needs to be inserted in the collection
        """

        self._db.insert_many(objs)

    def find_one(self, filter):
        """
        It returns only the first element found via the given filter

        Args:
            filter (dict): filter applied to the request to find the doc
        Returns:
            dict: Returns an object 
        """

        return self._db.find_one(filter)

    def find(self, filter):
        """
        It returns all the elements found via the given filter

        Args:
            filter (dict): filter applied to the request to find the doc
        Returns:
            dict: Returns a list objects 
        """

        return self._db.find(filter)

    def update_one(self, filter, k, v):
        """
        Updates one single document

        Args:
            filter (dict): filter applied to the request to find the doc
            k (string): key on which to update the doc
            v (dict): value of the updated doc
        Returns:
            dict: Returns the document updated 
        """

        return self._db.update_one(filter, k, v)

    def push_one(self, filter, k, v, slice):
        """
        Update the first element that matches the given filter.
        If there is no ducument retrieved, no change is applied

        Args:
            filter (dict): filter applied to the request to find the doc
            k (string): array key on which to add the new doc
            v (dict): value of the new document
            slice (integer): cuts the array of inserted docs by a predefined quantity

        Returns:
            dict: Returns the document updated 
        """

        return self._db.push_one(filter, k, v, slice)

    def delete_many(self, filter):
        """
        Delete one or more document matching the filter provided
        
        
        Args:
            filter (dict): filter applied to the request to find the doc
        Returns:
            integer: number of elements deleted
        
        """
        
        return self._db.delete_many(filter)

    def count_documents(self, filter={}):
        """
        It counts all the documents stored in the collection
        
        Args:
            filter (dict): filter applied to the request to find the doc
        Returns:
            integer: number of documents found
        """

        return self._db.count_documents(filter)

    def clean_collection(self):
        """
        It drops the whole collection
        """

        return self._db.clean_collection()

    def close_conn(self):
        """
        It closes the connection to the DB
        """

        self._db.close_conn()


class Database(ABC):

    @abstractmethod
    def insert(self):
        pass

    @abstractmethod
    def insert_many(self):
        pass

    @abstractmethod
    def find_one(self):
        pass

    @abstractmethod
    def find(self):
        pass

    @abstractmethod
    def update_one(self):
        pass

    @abstractmethod
    def push_one(self):
        pass
    
    @abstractmethod
    def delete_many(self):
        pass

    @abstractmethod
    def count_documents(self):
        pass

    @abstractmethod
    def clean_collection(self):
        pass

    @abstractmethod
    def self_test(self):
        pass

    @abstractmethod
    def close_conn(self):
        pass


class MongoDB(Database):

    def __init__(self, host, user, passw, port, db, collection):
        try:
            self._client = MongoClient(
                host=host, username=user, password=passw, port=port)
            self._db = self._client[db]
            self._collection = self._db[collection]
            self.self_test()
        except (Exception, pyErr) as err:
            logger.error(f"can't setup the connection with mongodb - {err}")
            raise

    def insert(self, obj):
        try:
            self._collection.insert_one(obj)
        except Exception as err:
            logger.error(f"can't insert given dict into mongodb: {err}")
            raise err

    def insert_many(self, objs):
        try:
            self._collection.insert_many(objs)
        except Exception as err:
            logger.error(f"can't insert documents in the collection: {err}")
            raise err

    def find_one(self, filter):
        try:
            return self._collection.find_one(filter)
        except Exception as err:
            logger.error(f"can't find any any dict with given filter: {err}")
            raise err

    def find(self, filter):
        try:
            return self._collection.find(filter)
        except Exception as err:
            logger.error(f"can't find any any dict with given filter: {err}")
            raise err

    def update_one(self, filter, k, v):
        try:
            self._collection.update_one(
                filter,
                {
                    '$set': {k: v}
                }
            )
        except Exception as err:
            logger.error(f"can't update the element: {err}")

    def push_one(self, filter, k, v, slice):
        try:
            self._collection.update_one(
                filter,
                {
                    '$push': {
                        k: {
                            '$each': [v],
                            '$slice': - slice
                        }
                    }
                },
                upsert=True
            )
        except Exception as err:
            logger.error(f"can't update the element: {err}")
            
            
    def delete_many(self, filter):
        try:
            return self._collection.delete_many(filter)
        except Exception as err:
            logger.error(f"can't delete any any dict with given filter: {err}")
            raise err
       
       
    def count_documents(self, filter):
        try:
            return self._collection.count_documents(filter)
        except Exception as err:
            logger.error(f"can't count documents in the collection: {err}")
            raise err

    def clean_collection(self):
        try:
            return self._collection.delete_many({})
        except Exception as err:
            logger.error(f"can't delete all items in the collection: {err}")
            raise err

    def self_test(self):
        try:
            self._client.server_info()
        except Exception as err:
            logger.error(f"Error communicating with MongoDB: {err}")
            raise err

    def close_conn(self):
        try:
            self._client.close()
        except Exception as err:
            logger.error(f"Can't close connection to MongoDB: {err}")
            raise err


