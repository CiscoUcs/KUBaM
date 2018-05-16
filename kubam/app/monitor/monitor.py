from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from ucs import UCSUtil, UCSMonitor
from db import YamlDB
from config import Const
from helper import KubamError

monitor = Blueprint("monitor", __name__)


# Get the overall status of the server from UCSM FSM
@monitor.route(Const.API_ROOT2 + "/<server_group>/status", methods=["GET"])
@cross_origin()
def get_server_status(server_group):
    try:
        db = YamlDB()
        sg = db.get_server_group(Const.KUBAM_CFG, server_group)
        handle = UCSUtil.ucs_login(sg)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST
    status = UCSMonitor.get_status(handle, UCSMonitor.get_server_name(request.args))
    UCSUtil.ucs_logout(handle)
    if not status:
        return jsonify({"error": "Bad blade or rack server specified"}), Const.HTTP_NOT_FOUND
    else:
        return jsonify(status), Const.HTTP_OK


# Get the detailed status of the server stages from UCSM FSM
@monitor.route(Const.API_ROOT2 + "/<server_group>/fsm", methods=["GET"])
@cross_origin()
def get_server_fsm(server_group):
    try:
        db = YamlDB()
        sg = db.get_server_group(Const.KUBAM_CFG, server_group)
        handle = UCSUtil.ucs_login(sg)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST
    fsm = UCSMonitor.get_fsm(handle, UCSMonitor.get_server_name(request.args))
    UCSUtil.ucs_logout(handle)

    if not fsm:
        return jsonify({"error": "Bad blade or rack server specified"}), Const.HTTP_NOT_FOUND
    else:
        return jsonify(fsm), Const.HTTP_OK
