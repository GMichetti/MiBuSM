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

import uuid
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .server import db
from enum import Enum
from sqlalchemy import Column, String
from ipaddress import ip_address



class UserRoleEnum(Enum):
    ADMIN = "admin"
    GUEST = "guest"


class DeviceType(Enum):
    SERVER = "server"
    SECURITY_APPLIANCE = "firewall"
    POWER_CONTINUITY_APPLIANCE = "ups"
    L3_APPLIANCE = "l3"
    L2_APPLIANCE = "l2"


class User(db.Model, UserMixin):
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=True)
    role = db.Column(db.Enum(UserRoleEnum), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self) -> str:
        return f"id: {self.id}, user: {self.user}, role: {self.role}"


class Devices(db.Model):
    # id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_type = db.Column(db.Enum(DeviceType), nullable=False)
    name = db.Column(db.String(200), default="")
    vendor = db.Column(db.String(200), nullable=False)
    controller_ip = db.Column(db.String(200), default="")
    controller_user = db.Column(db.String(200), default="")
    controller_password = db.Column(db.String(200), default="")
    hypervisor_type = db.Column(db.String(200), default="")
    hypervisor_ip = db.Column(db.String(200), default="")
    hypervisor_user = db.Column(db.String(200), default="")
    hypervisor_password = db.Column(db.String(200), default="")
    host_ip = db.Column(db.String(200), default="")
    host_user = db.Column(db.String(200), default="")
    host_password = db.Column(db.String(200), default="")
    pid = db.Column(db.String(200), default="")

    def __repr__(self) -> str:
        return f"id: {self.id} device_type: {self.device_type}, vendor: {self.vendor} , type:{self.device_type}"

    def to_dict(self):
        device_dict = {
            "id": self.id,
            "device_type": self.device_type.value,
            "name": self.name,
            "vendor": self.vendor,
            "c_ip": self.controller_ip,
            "c_user": self.controller_user,
            "c_pass": self.controller_password,
            "h_type": self.hypervisor_type,
            "h_ip": self.hypervisor_ip,
            "h_user": self.hypervisor_user,
            "h_pass": self.hypervisor_password,
            "ip": self.host_ip,
            "user": self.host_user,
            "password": self.host_password,
            "pid": self.pid
        }
        return device_dict