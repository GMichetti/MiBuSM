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
import jinja2
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

try:
    from config_loader import Config_Loader
except ModuleNotFoundError:
    from ..config_loader import Config_Loader
config_loader = Config_Loader()


try:
    from log import Logger
except ModuleNotFoundError:
    from ..log import Logger

logger = Logger()

SECRET_KEY = config_loader.config["flask_secret_key"]
DB_NAME = config_loader.config["flask_db_name"]
DEFAULT_USER_PASSWORD = config_loader.config["default_user_password"]
RATE_LIMITER_STORAGE_URI = config_loader.config["internal_db_host"]

# Linking to SQLAlchemy
db = SQLAlchemy()
app = Flask(__name__, instance_relative_config=True)

# Rate Limiter for API
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=RATE_LIMITER_STORAGE_URI,
)

# Needed for Prometheus
metrics = GunicornPrometheusMetrics(app)

basedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, DB_NAME)
app.config['SECRET_KEY'] = SECRET_KEY


def hide_password(password):
    if password and isinstance(password, str):
        if password != "-":
            return '*' * len(password)
        else:
            return "-"
    else:
        return "-"


def apply_dash(data):
    if not data:
        return '-'
    else:
        return data


def uppercase(st):
    return st.upper()


jinja2.filters.FILTERS['hide_password'] = hide_password
jinja2.filters.FILTERS['apply_dash'] = apply_dash
jinja2.filters.FILTERS['uppercase'] = uppercase

try:
    os.makedirs(app.instance_path)
except OSError:
    pass

db.init_app(app)

from .models import User, Devices
from . import controller

with app.app_context():
    db.create_all()
    default_user = User.query.filter_by(user='JackBurton').first()
    if not default_user:
        default_user = User(user='JackBurton', role="ADMIN")
        default_user.set_password(password=DEFAULT_USER_PASSWORD)
        db.session.add(default_user)
        db.session.commit()

