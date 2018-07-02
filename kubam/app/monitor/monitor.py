from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from ucs import UCSUtil, UCSMonitor, UCSServer
from ucsc import UCSCUtil, UCSCMonitor, UCSCServer
from db import YamlDB
from config import Const
from helper import KubamError

monitor = Blueprint("monitor", __name__)


# Get the overall status of the server from UCSM FSM
@monitor.route(Const.API_ROOT2 + "/servers/<server_group>/status", methods=["GET"])
@cross_origin()
def get_server_status(server_group):
    """
    Get the FSM or status of the server... what its doing now. 
    Expects { servers: { blade: [ 1/1, 1/2, ...], rack_server: [ 1, 2, 3] }}
    (with quotes of course for proper json)
    if nothing is passed, returns everything. 
    """
    wanted = "all"
    try:
        db = YamlDB()
        sg = db.get_server_group(Const.KUBAM_CFG, server_group)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST
    
    if request.json and "servers" in request.json:
        wanted = request.json["servers"]

    if sg["type"] == "ucsm":
        return get_server_status_ucsm(sg, wanted)
    elif sg["type"] == "ucsc":
        return get_server_status_ucsc(sg, wanted)

    return jsonify({"error": "server group {0} is not a supported type".format(sg["type"])}), Const.HTTP_BAD_REQUEST
    

def get_server_status_ucsm(sg, wanted):
    """
    Get the UCS Manager Server status 
    """
    try:
        handle = UCSUtil.ucs_login(sg)
    except KubamError as e:
        UCSUtil.ucs_logout(handle)
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    try:
        all_servers = UCSServer.list_servers(handle)
        if not wanted == "all":
            all_servers = UCSUtil.servers_to_objects(all_servers, wanted)
    except KubamError as e:
        UCSUtil.ucs_logout(handle)
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST
    
    try: 
        status = UCSMonitor.get_status(handle, all_servers)
        out = UCSUtil.dn_hash_to_out(status)
    except KubamError as e:
        UCSUtil.ucs_logout(handle)
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    UCSUtil.ucs_logout(handle)
    return jsonify({"servers" : out }), Const.HTTP_OK

def get_server_status_ucsc(sg, wanted):
    try:
        handle = UCSCUtil.ucsc_login(sg)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    try:
        all_servers = UCSCServer.list_servers(handle)
        if not wanted == "all":
            all_servers = UCSCUtil.servers_to_objects(all_servers, wanted)
    except KubamError as e:
        UCSCUtil.ucsc_logout(handle)
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST
    
    #try: 
    #    status = UCSCMonitor.get_status(handle, all_servers)
    #    out = UCSCUtil.dn_hash_to_out(status)
    #except KubamError as e:
    #    UCSUtil.ucsc_logout(handle)
    #    return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    UCSCUtil.ucsc_logout(handle)
    return jsonify({"servers" : all_servers }), Const.HTTP_OK





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
