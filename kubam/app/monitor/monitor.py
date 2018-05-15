from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from ucs import UCSUtil, UCSMonitor
from config import Const

monitor = Blueprint("monitor", __name__)


# Get the overall status of the server from UCSM FSM
@monitor.route(Const.API_ROOT2 + "/status", methods=["GET"])
@cross_origin()
def get_server_status():
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        msg = UCSUtil.not_logged_in(msg)
        return jsonify({"error": msg}), Const.HTTP_UNAUTHORIZED
    status = UCSMonitor.get_status(handle, UCSMonitor.get_server_name(request.args))
    UCSUtil.ucs_logout(handle)
    if not status:
        return jsonify({"error": "Bad blade or rack server specified"}), Const.HTTP_NOT_FOUND
    else:
        return jsonify(status), Const.HTTP_OK


# Get the detailed status of the server stages from UCSM FSM
@monitor.route(Const.API_ROOT2 + "/fsm", methods=["GET"])
@cross_origin()
def get_server_fsm():
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        msg = UCSUtil.not_logged_in(msg)
        return jsonify({"error": msg}), Const.HTTP_UNAUTHORIZED
    fsm = UCSMonitor.get_fsm(handle, UCSMonitor.get_server_name(request.args))
    UCSUtil.ucs_logout(handle)

    if not fsm:
        return jsonify({"error": "Bad blade or rack server specified"}), Const.HTTP_NOT_FOUND
    else:
        return jsonify(fsm), Const.HTTP_OK
