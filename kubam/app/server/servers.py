from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
from ucs import UCSUtil, UCSServer, UCSTemplate, UCSUtil
from autoinstall import Builder
from config import Const
from db import YamlDB
from config import Const
from util import KubamError


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
        print req
        if not isinstance(req, dict):
            return {'error' : "invalid parameters: %s" % req}, 400
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
        print request.json

        j, rc = Servers.delete_servers(request.json)
    else:
        j, rc = Servers.list_servers()
    return jsonify(j), rc


@servers.route(Const.API_ROOT2 + "/servers/<server_group>/templates", methods=['GET'])
@cross_origin()
def get_templates(server_group):
    """
    Get the service profile templates in the server group. 
    """
    db = YamlDB()
    err, msg, sg = db.get_server_group(Const.KUBAM_CFG, server_group)
    err, msg, handle = UCSUtil.ucs_login(sg)
    if err != 0:
        msg = UCSUtil.not_logged_in(msg)
        current_app.logger.warning(msg)
        return jsonify({'error': msg}), Const.HTTP_UNAUTHORIZED
    try:
        ucs_templates = UCSTemplate.list_templates(handle)
        UCSUtil.ucs_logout(handle)
        return jsonify({'templates': ucs_templates}), Const.HTTP_OK
    except KubamError as e:
        return jsonify({'error': e}), Const.HTTP_SERVER_ERROR


@servers.route(Const.API_ROOT2 + "/servers/<server_group>/servers", methods=['GET'])
@cross_origin()
def get_servers(server_group):
    """
    List all the servers in the server group
    or in this case the domain. 
    """
    db = YamlDB()
    err, msg, sg = db.get_server_group(Const.KUBAM_CFG, server_group)
    err, msg, handle = UCSUtil.ucs_login(sg)
     
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
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'servers': ucs_servers}), 200

