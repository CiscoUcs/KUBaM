from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from ucs import UCSUtil, UCSServer
from autoinstall import Builder
from config import Const
from db import YamlDB
from sg import sg

servers = Blueprint("servers", __name__)


@servers.route(Const.API_ROOT2 + "/servers", methods=['GET', 'POST', 'PUT', 'DELETE'])
@cross_origin()
def server_handler():
    if request.method == 'POST':
        j, rc = sg.create(request.json)
    elif request.method == 'PUT':
        j, rc = sg.update(request.json)
    elif request.method == 'DELETE':
        j, rc = sg.delete(request.json)
    else:
        j, rc = sg.list()
    return jsonify(j), rc


@servers.route(Const.API_ROOT + "/servers", methods=['GET'])
@cross_origin()
def get_servers():
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        return UCSUtil.not_logged_in(msg)
    ucs_servers = UCSServer.list_servers(handle)
    UCSUtil.ucs_logout(handle)

    # Gets a hash of severs of form:
    # {blades: ["1/1", "1/2",..], rack: ["6", "7"]}
    err, msg, db_servers = YamlDB.get_ucs_servers(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    ucs_servers = UCSUtil.servers_to_api(ucs_servers, db_servers)
    err, msg, hosts = YamlDB.get_hosts(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'servers': ucs_servers, 'hosts': hosts}), 200


@servers.route(Const.API_ROOT + "/servers", methods=['POST'])
@cross_origin()
def select_servers():
    if not request.json:
        return jsonify({'error': 'expected hash of servers'}), 400
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        return UCSUtil.not_logged_in(msg)
    ucs_servers = request.json['servers']
    # Gets a hash of severs of form:
    # {blades: ["1/1", "1/2",..], rack: ["6", "7"]}
    ucs_servers = UCSUtil.servers_to_db(ucs_servers)
    if ucs_servers:
        err, msg = YamlDB.update_ucs_servers(Const.KUBAM_CFG, ucs_servers)
        if err != 0:
            return jsonify({'error': msg}), 400
    if "hosts" not in request.json:
        return get_servers()

    hosts = request.json['hosts']
    err, msg = YamlDB.update_hosts(Const.KUBAM_CFG, hosts)
    if err != 0:
        return jsonify({'error': msg}), 400

    # Return the existing networks now with the new one chosen.
    return get_servers()


# Make the server images
@servers.route(Const.API_ROOT + "/servers/images", methods=['POST'])
@cross_origin()
def deploy_server_autoinstall_images():
    err, msg = Builder.deploy_server_images(Const.KUBAM_CFG)
    if not err == 0:
        return jsonify({"error": msg})
    return jsonify({"status": "ok"}), 201
