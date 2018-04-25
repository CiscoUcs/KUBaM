from UCSMonitor import UCSMonitor
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from ucs import UCSUtil
from config import Const

monitor = Blueprint("monitor", __name__)


# Get the server name from the URL parameters
def get_server_name():
    server_type = request.args.get('type')
    chassis_id = request.args.get('chassis_id')
    slot = request.args.get('slot')
    rack_id = request.args.get('rack_id')
    server_name = None
    if server_type == "blade":
        server_name = "sys/chassis-{0}/blade-{1}".format(chassis_id, slot)
    elif server_type == "rack":
        server_name = "sys/rack-unit-{0}".format(rack_id)

    return server_name


# Get the overall status of the server from UCSM FSM
@monitor.route(Const.API_ROOT2 + "/status", methods=['GET'])
@cross_origin()
def get_server_status():
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        return UCSUtil.not_logged_in(msg)
    status = UCSMonitor.get_status(handle, get_server_name())
    UCSUtil.ucs_logout(handle)
    if not status:
        return jsonify({"error": "Bad blade or rack server specified"}), 404
    else:
        return jsonify(status), 200


# Get the detailed status of the server stages from UCSM FSM
@monitor.route(Const.API_ROOT2 + "/fsm", methods=['GET'])
@cross_origin()
def get_server_fsm():
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        return UCSUtil.not_logged_in(msg)
    fsm = UCSMonitor.get_fsm(handle, get_server_name())
    UCSUtil.ucs_logout(handle)

    if not fsm:
        return jsonify({"error": "Bad blade or rack server specified"}), 404
    else:
        return jsonify(fsm), 200
