# This file is a part of Mibu.
#
# Copyright (C) 2024 Giuseppe Michetti <gius.michetti@gmail.com>
#
# Mibu is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# Mibu is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

try:
    from engine import service
except ModuleNotFoundError:
    from ..engine import service
    
from flask import render_template, request, redirect, session, url_for
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from .server import app
from flask_restx import Resource, Api, Namespace, fields
from .server import db
from .server import logger
from .models import User, Devices


#################################################################################
#                                                                               #
#                             INITIALIZE COMPONENTS                             #
#                                                                               #
#################################################################################

api = Api(app, version='1.0',
          title='Mibu',
          description='Mibu Server Manager API rest',
          doc='/docs/',
          prefix="/api/")

login_manager = LoginManager(app)
login_manager.login_view = 'login'

engine_service = service.Service()
engine_service.initialize()


@login_manager.user_loader
def load_user(user):
    return User.query.get(str(user))


#################################################################################
#                                                                               #
#                                     ROUTES                                    #
#                                                                               #
#################################################################################

@app.route('/')
@login_required
def index():
    app.logger.info('Access to route /')
    return render_template('dashboard.html', current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page
    """

    if request.method == 'POST':
        username = request.form['username']
        password = password = request.form['password']
        user = User.query.filter_by(user=username).first()
        if user and user.check_password(password=password):
            login_user(user)
            return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/delete_user/<string:id>')
@login_required
def delete_user(id):
    """
    It managed the deletion of a single user from the related DB
    """

    if current_user.role.value == "admin":
        user = User.query.filter_by(id=id).first()
        db.session.delete(user)
        db.session.commit()
    return redirect("/users")


@app.route('/delete_device/<string:id>')
@login_required
def delete_device(id):
    """
    It manages the deletion of a single device from the related DB
    """
    if current_user.role.value == "admin":
        user = Devices.query.filter_by(id=id).first()
        db.session.delete(user)
        db.session.commit()
        devices = Devices.query.all()
        devices_list = [device.to_dict() for device in devices]
        try:
            devs = engine_service.get_data_from_device_model(devices_list)
            if engine_service.reset_engine():
                if engine_service.register_devices(devs):
                    logger.info("devices registered successfully")
                else:
                    logger.error("can't register devices")
            else:
                logger.error("can't reset the engine")

        except Exception as err:
            logger.error(f"can't reset the engine: {err}")

        return redirect("/devices")


@app.route('/logout')
@login_required
def logout():
    """
    Logout page
    """
    logout_user()
    return render_template('login.html')


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    """
    Shows data relating to the users DB.
    Adds a new user if required
    """

    if request.method == 'POST':
        username = request.form["username"]
        role = request.form["role_radios"]
        new_user = User(user=username, role=role)
        new_user.set_password(password=request.form["password"])
        db.session.add(new_user)
        db.session.commit()

    users = User.query.all()
    return render_template('users.html', users=users, current_user=current_user)


@app.route('/devices', methods=['GET', 'POST'])
@login_required
def devices():
    """
    Shows data relating to the devices DB.
    Adds a new device if required
    """

    if request.method == 'POST' and current_user.role.value == "admin":
        try:
            device_type = request.form["device_type_radios"]
            if device_type == "SERVER":
                name = request.form.get("name", "")
                vendor = request.form.get("vendor", "").lower()
                controller_ip = request.form.get("controller_ip", "")
                controller_user = request.form.get("controller_user", "")
                controller_password = request.form.get(
                    "controller_password", "")
                hypervisor_type = request.form.get(
                    "hypervisor_type", "").lower()
                hypervisor_ip = request.form.get("hypervisor_ip", "")
                hypervisor_user = request.form.get("hypervisor_user", "")
                hypervisor_password = request.form.get(
                    "hypervisor_password", "")
                new_device = Devices(device_type=device_type,
                                     name=name,
                                     vendor=vendor,
                                     controller_ip=controller_ip,
                                     controller_user=controller_user,
                                     controller_password=controller_password,
                                     hypervisor_type=hypervisor_type,
                                     hypervisor_ip=hypervisor_ip,
                                     hypervisor_user=hypervisor_user,
                                     hypervisor_password=hypervisor_password)
            elif device_type == "POWER_CONTINUITY_APPLIANCE":
                name = request.form.get("name", "")
                vendor = request.form.get("vendor", "").lower()
                pid = request.form.get("pid", "").lower()
                new_device = Devices(device_type=device_type,
                                     name=name,
                                     vendor=vendor,
                                     pid=pid)
            else:
                name = request.form.get("name", "")
                vendor = request.form.get("vendor", "").lower()
                ip_address = request.form.get("ip_address", "")
                user = request.form.get("user", "")
                password = request.form.get("password", "")
                new_device = Devices(device_type=device_type,
                                     name=name,
                                     vendor=vendor,
                                     host_ip=ip_address,
                                     host_user=user,
                                     host_password=password)
            db.session.add(new_device)
            db.session.commit()
            devices = Devices.query.all()
            devices_list = [device.to_dict() for device in devices]
            devs = engine_service.get_data_from_device_model(devices_list)

            if engine_service.reset_engine():
                if engine_service.register_devices(devs):
                    logger.info("devices registered successfully")
                else:
                    logger.error("can't register devices")
            else:
                logger.error("can't reset the engine")

        except Exception as err:
            logger.error(err)

    devices = Devices.query.all()
    return render_template('devices.html', devices=devices)


@app.route('/reload_devices', methods=['GET', 'POST'])
@login_required
def reloald_devices():
    """
    Reload the devices inside the engine without adding/removing
    """

    if request.method == 'POST' and current_user.role.value == "admin":
        devices = Devices.query.all()
        devices_list = [device.to_dict() for device in devices]
        devs = engine_service.get_data_from_device_model(devices_list)
        if engine_service.reset_engine():
            if engine_service.register_devices(devs):
                logger.info("devices registered successfully")
            else:
                logger.error("can't register devices")
        else:
            logger.error("can't reset the engine")
    devices = Devices.query.all()
    return render_template('devices.html', devices=devices)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """
    Shows the main page relating to device statistics
    """
    reg_devs = engine_service.get_registered_devices()
    return render_template('dashboard.html', current_user=current_user, reg_devs=reg_devs)


@app.route('/perf_n_logs', methods=['GET'])
@login_required
def perf_n_logs():
    """
    Shows the MiBu performance and logs page. Adds software observability
    """
    return render_template('perf_n_logs.html', current_user=current_user)


#################################################################################
#                                                                               #
#                                EXPOSED REST API v1                            #
#                                                                               #
#################################################################################

rest_api_v1 = Namespace(name="Mibu", description="API REST v1")
app.config.SWAGGER_SUPPORTED_SUBMIT_METHODS = []


class Auth_Login(Resource):

    @rest_api_v1.doc(params={'username': '', 'password': ''})
    @rest_api_v1.doc(responses={200: 'User Authorized'})
    @rest_api_v1.doc(responses={401: 'User Unauthorized'})
    def post(self):
        """
        It allows login into Mibu
        """

        username = request.get_json()['username']
        password = request.get_json()['password']
        user = User.query.filter_by(user=username).first()
        if user and user.check_password(password=password):
            login_user(user)
            session['user_id'] = user.id
            return {'logged in': 'User Authorized'}, 200
        else:
            return {'error': 'User Unauthorized'}, 401


class Devices_Info(Resource):

    @rest_api_v1.doc(responses={200: "data"})
    @rest_api_v1.doc(responses={400: 'no data found'})
    @rest_api_v1.doc(responses={404: 'no registered devices'})
    @rest_api_v1.doc(responses={500: 'internal error'})
    @login_required
    def get(self):
        """
        It obtains statistical data from registered devices
        """
        try:
            dev_list = engine_service.get_registered_devices()
            if dev_list:
                data = engine_service.get_data_from_devices(dev_list)
                if data:
                    return data, 200
                else:
                    return {"error": "no data found"}, 400
            else:
                return {"error:": "no registered devices"}, 404
        except Exception as err:
            logger.error(f"internal error: {err}")
            return {}, 500


class Set_State(Resource):

    @rest_api_v1.doc(params={
        'action': {
            'description': 'action performed against a list of device to set the device status',
            'required': True,
            'example': {'power_on': ["id1", "id2"],
                        'shutdown': ["id3", "id4"],
                        'reboot': ["id5", "id6"]}
        }
    })
    @rest_api_v1.doc(responses={400: 'something went wrong trying to set the state'})
    @rest_api_v1.doc(responses={404: 'missing ids or device not registered'})
    @rest_api_v1.doc(responses={500: 'internal error'})
    @login_required
    def post(self):
        """
        Set whether to turn on, off or reboot a device)
        """
        data = request.get_json()
        action = list(data.keys())[0]
        if action in ["power_on", "shutdown", "reboot"]:
            dev_ids = data[action]

            if dev_ids and any(obj['id'] in dev_ids for obj in engine_service.get_registered_devices(only_ids=True)):
                res = engine_service.send_to_devices(
                    list(map(lambda id: {"id": id, "action": action}, dev_ids)))
                if res:
                    return {f"{action}": dev_ids}, 200

                else:
                    {'error': f'something went wrong trying to {action} devices: {dev_ids}'}, 400
            else:
                {'error': 'missing ids or device not registered'}, 404
        else:
            return {'error': 'internal error'}, 500


class Get_Perf_n_Logs(Resource):

    @rest_api_v1.doc(responses={200: "data"})
    @rest_api_v1.doc(responses={500: 'internal error'})
    @login_required
    def get(self):
        """
        It obtains MiBu performance and log data
        """
        try:
            dev_list = engine_service.get_registered_devices()
            msg_broker_queue = engine_service.get_msg_bkr_queue()
            throughput = engine_service.get_throughput(dev_list)
            logs = engine_service.read_log_files()
            return {"msg_broker_queue": msg_broker_queue,
                    "throughput": throughput,
                    "logs": logs}, 200
        except Exception as err:
            logger.error(f"error getting performance and log data: {err}")
            return {"msg_broker_queue": 0,
                    "throughput": [],
                    "logs": ""}, 500


class Send_Command(Resource):
    
    @rest_api_v1.doc(params={
        'action': {
            'description': 'action performed against a list of device to interact with thee OS',
            'required': True,
            'example': {'power_on_vms': ["id1", "id2"],
                        'get_vms_on': ["id3", "id4"],
                        'send_command': ["id5", "id6"]}
        }
    })
    @rest_api_v1.doc(responses={200: "data"})
    @rest_api_v1.doc(responses={400: 'command not recognized for the device type'})
    @rest_api_v1.doc(responses={404: 'missing ids or device not registered'})
    @rest_api_v1.doc(responses={500: 'internal error'})
    @login_required
    def post(self):
        """
        Forward a general command to any registered device
        """

        SERVER_AVAILABLE_ACTIONS = [
            "power_on_vms", "power_off_vms", "get_vms_on"]
        FIREWALL_AVAILABLE_ACTIONS = ["send_command"]

        data = request.get_json()
        action = list(data.keys())[0]
        dev_ids = data[action]
        registered_devs = engine_service.get_registered_devices()
        if dev_ids and any(obj['id'] == dev_ids for obj in registered_devs):
            dev_type = engine_service.get_registered_device_by_id(dev_ids)[
                "dev_type"]
            if (dev_type == "server" and action in SERVER_AVAILABLE_ACTIONS) or \
                    (dev_type == "firewall" and action in FIREWALL_AVAILABLE_ACTIONS):

                res = engine_service.send_to_devices(
                    list(map(lambda id: {"id": id, "action": action}, dev_ids)))
                if res:
                    return {f"{action}": dev_ids}, 200
                else:
                    {'error': f'internal error trying to {action} devices: {dev_ids}'}, 500
            else:
                {'error': 'command not recognized for the device type'}, 400
        else:
            {'error': 'missing ids or device not registered'}, 404


class Get_Command_Result(Resource):

    @rest_api_v1.doc(params={
        'action_ids': {
            'description': 'List of action IDs',
            'type': 'array',
            'items': {
                'type': 'string'
            },
            'required': True,
            'example': ["id1", "id2"]
        }
    })
    @rest_api_v1.doc(responses={200: "data"})
    @rest_api_v1.doc(responses={404: 'no actions found'})
    @login_required
    def post(self):
        """
        Get results from a performed list of actions
        """
        action_ids = request.get_json()["action_ids"]
        if action_ids:
            status_list = engine_service.get_action_status(action_ids)

            result = []
            for status in status_list:
                result.append(status)
            return {"result": result}, 200
        else:
            {'error': 'no actions found'}, 404


rest_api_v1.add_resource(Auth_Login, '/auth/login')
rest_api_v1.add_resource(Devices_Info, '/devices_info')
rest_api_v1.add_resource(Set_State, '/set_state')
rest_api_v1.add_resource(Get_Perf_n_Logs, '/get_perf_n_logs')
rest_api_v1.add_resource(Send_Command, '/send_command')
rest_api_v1.add_resource(Get_Command_Result, '/get_command_result')
api.add_namespace(rest_api_v1, path='/v1')
