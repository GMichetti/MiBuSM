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

from pydantic import BaseModel, validator, IPvAnyAddress, SecretStr, PositiveInt, NonNegativeInt, ValidationError
import yaml
import os
import logging


class ConfigModel(BaseModel):
    flask_db_name: str = "db.sqlite"
    flask_secret_key: str = "5UP3R_5eCRe7"
    msg_broker: str = "redis"
    msg_broker_usr: str = ""
    msg_broker_pass: SecretStr = ""
    msg_broker_host: str | IPvAnyAddress = "redis"
    msg_broker_port: PositiveInt = 6379
    msg_broker_db: NonNegativeInt = 0
    msg_broker_request_queue: str = "request_queue"
    internal_db: str = "mongodb"
    internal_db_usr: str = ""
    internal_db_pass: str = ""
    internal_db_host: str | IPvAnyAddress = "mongodb"
    internal_db_port: PositiveInt = 27017
    internal_db_database: str = "mibu_db"
    internal_db_devs_info: str = "mibu_devs_info"
    internal_db_devs_list: str = "mibu_devs_list"
    internal_db_action_status_list: str = "mibu_action_status_list"
    internal_db_msg_bkr_stats: str = "mibu_msg_bkr_stats"
    action_status_sb_pruning_time: PositiveInt = 60     # [minutes]
    log_file_path: str = os.path.join("/var", "log","mibu", "mibu.log") if os.name == 'posix' else os.path.join("C:\\", "var", "log", "mibu","mibu.log")
    log_lock_file: str = os.path.join("/var", "log", "mibu", "mibu.lock") if os.name == 'posix' else os.path.join("C:\\", "var", "log","mibu","mibu.lock")
    log_max_bytes: PositiveInt = 1024 * 512             # [Kbytes]
    max_workers: PositiveInt = 4
    polling_cycle_heartbeat: PositiveInt = 5
    waiting_time: PositiveInt = 5
    battery_lower_threshold: PositiveInt = 20
    history_max_size: PositiveInt = 10
    msg_bkr_history_max_size: PositiveInt = 20
    auto_feeder_polling_time: PositiveInt = 20
    auto_max_time_delta: PositiveInt = 70
    action_retry_delay: PositiveInt = 1
    action_retry_tries: PositiveInt = 2
    worker_timeout: PositiveInt = 30
    default_user_password: str = "Ch@ngeMe!"


    @validator("auto_max_time_delta", pre=True, always=True, check_fields=True)
    def validate_max_time_delta(cls, value, values):
        auto_feeder_polling_time = values.get("auto_feeder_polling_time", 20)
        return (auto_feeder_polling_time * 3) + 10


class Config_Loader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config_Loader, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        """
        Load the configuration from the config.yaml file.
        If it does not exist, use default values
        """
        
        config_defaults = ConfigModel().model_dump()

        try:
            with open('config.yaml', 'r') as file:
                config_data = yaml.safe_load(file)

        except FileNotFoundError:
            config_data = config_defaults

        except yaml.YAMLError:
            config_data = config_defaults

        config_data = {**config_defaults, **config_data}

        try:
            self.config_data = ConfigModel(**config_data)
        except ValidationError as ve:
            logging.error(f"{ve}, using default config values")
            self.config_data = config_defaults

    @property
    def config(self):
        return self.config_data.model_dump()
