from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from ucs import UCSUtil, UCSServer
from autoinstall import Builder
from config import Const
from db import YamlDB

servers = Blueprint("servers", __name__)


class Servers(object):
    # List the server group information
    @staticmethod
    def list_servers():
        """
        / basic test to see if site is up.
        should return { 'status' : 'ok'}
        """
        db = YamlDB()
        err, msg, sg = db.list_server_group(Const.KUBAM_CFG)
        if err == 1:
            return {'error': msg}, 500
        return {"servers": sg}, 200

    # Create a new server group
    @staticmethod
    def create_servers(req):
        """
        Create a new UCS Domain
        Format of request should be JSON that looks like:
        {"name", "ucs01", "type" : "ucsm", "credentials":
            {"user": "admin", "password": "secret-password", "ip" : "172.28.225.163" }}
        """
        # Make sure we can log in first.

        err, msg = UCSUtil.check_ucs_login(req)
        if err == 1:
            return {'error:': msg}, 400
        db = YamlDB()
        err, msg = db.new_server_group(Const.KUBAM_CFG, req)
        if err == 1:
            return {'error': msg}, 400
        return {'status': "new server group {0} created!".format(req["name"])}, 201

    @staticmethod
    def update_servers(req):
        """
        Update a server group
        """
        err, msg = UCSUtil.check_ucs_login(req)
        if err == 1:
            return {'error:': msg}, 400
        db = YamlDB()
        err, msg = db.update_server_group(Const.KUBAM_CFG, req)
        if err == 1:
            return {'error': msg}, 400
        return {'status': "server group %s updated!" % req["name"]}, 201

    @staticmethod
    def delete_servers(req):
        """
        Delete the UCS server group or CIMC from the config.
        """
        uuid = req['id']
        db = YamlDB()
        err, msg = db.delete_server_group(Const.KUBAM_CFG, uuid)
        if err == 1:
            return {'error': msg}, 400
        else:
            return {'status': "server group deleted"}, 201


@servers.route(Const.API_ROOT2 + "/servers", methods=['GET', 'POST', 'PUT', 'DELETE'])
@cross_origin()
def server_handler():
    if request.method == 'POST':
        j, rc = Servers.create_servers(request.json)
    elif request.method == 'PUT':
        j, rc = Servers.update_servers(request.json)
    elif request.method == 'DELETE':
        j, rc = Servers.delete_servers(request.json)
    else:
        j, rc = Servers.list_servers()
    return jsonify(j), rc


@servers.route(Const.API_ROOT + "/servers", methods=['GET'])
@cross_origin()
def get_servers():
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        msg = UCSUtil.not_logged_in(msg)
        return jsonify({'error': msg}), 401
    ucs_servers = UCSServer.list_servers(handle)
    UCSUtil.ucs_logout(handle)

    # Gets a hash of severs of form:
    # {blades: ["1/1", "1/2",..], rack: ["6", "7"]}
    db = YamlDB()
    err, msg, db_servers = db.get_ucs_servers(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    ucs_servers = UCSUtil.servers_to_api(ucs_servers, db_servers)
    err, msg, hosts = db.get_hosts(Const.KUBAM_CFG)
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
        msg = UCSUtil.not_logged_in(msg)
        return jsonify({'error': msg}), 401
    ucs_servers = request.json['servers']
    # Gets a hash of severs of form:
    # {blades: ["1/1", "1/2",..], rack: ["6", "7"]}
    ucs_servers = UCSUtil.servers_to_db(ucs_servers)
    db = YamlDB()
    if ucs_servers:
        err, msg = db.update_ucs_servers(Const.KUBAM_CFG, ucs_servers)
        if err != 0:
            return jsonify({'error': msg}), 400
    if "hosts" not in request.json:
        return get_servers()

    hosts = request.json['hosts']
    err, msg = db.update_hosts(Const.KUBAM_CFG, hosts)
    if err != 0:
        return jsonify({'error': msg}), 400

    # Return the existing networks now with the new one chosen.
    return get_servers()


# Make the server images
@servers.route(Const.API_ROOT + "/servers/images", methods=['POST'])
@cross_origin()
def deploy_server_autoinstall_images():
    builder = Builder()
    err, msg = builder.deploy_server_images(Const.KUBAM_CFG)
    if not err == 0:
        return jsonify({"error": msg})
    return jsonify({"status": "ok"}), 201
