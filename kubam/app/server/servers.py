from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
from ucs import UCSServer, UCSTemplate, UCSUtil
from db import YamlDB
from config import Const
from helper import KubamError


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
            return {"error": msg}, Const.HTTP_SERVER_ERROR
        return {"servers": sg}, Const.HTTP_OK

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
            return {"error": msg}, Const.HTTP_UNAUTHORIZED
        db = YamlDB()
        err, msg = db.new_server_group(Const.KUBAM_CFG, req)
        if err == 1:
            return {"error": msg}, Const.HTTP_BAD_REQUEST
        return {"status": "new server group {0} created!".format(req['name'])}, Const.HTTP_CREATED

    @staticmethod
    def update_servers(req):
        """
        Update a server group
        """
        err, msg = UCSUtil.check_ucs_login(req)
        if err == 1:
            return {"error:": msg}, Const.HTTP_BAD_REQUEST
        db = YamlDB()
        err, msg = db.update_server_group(Const.KUBAM_CFG, req)
        if err == 1:
            return {"error": msg}, Const.HTTP_BAD_REQUEST
        return {"status": "server group {0} updated!".format(req['name'])}, Const.HTTP_CREATED

    @staticmethod
    def delete_servers(req):
        """
        Delete the UCS server group or CIMC from the config.
        """
        print req
        if not isinstance(req, dict):
            return {"error": "invalid parameters: {0}".format(req)}, Const.HTTP_BAD_REQUEST
        uuid = req['id']
        db = YamlDB()
        err, msg = db.delete_server_group(Const.KUBAM_CFG, uuid)
        if err == 1:
            return {"error": msg}, Const.HTTP_BAD_REQUEST
        else:
            return {"status": "Server group deleted"}, Const.HTTP_NO_CONTENT


class Templates(object):
    @staticmethod
    def list_templates(server_group):
        """
        Get the service profile templates in the server group.
        """
        db = YamlDB()
        err, msg, sg = db.get_server_group(Const.KUBAM_CFG, server_group)
        err, msg, handle = UCSUtil.ucs_login(sg)
        if err != 0:
            msg = UCSUtil.not_logged_in(msg)
            current_app.logger.warning(msg)
            return jsonify({"error": msg}), Const.HTTP_UNAUTHORIZED

        ucs_templates = UCSTemplate.list_templates(handle)
        UCSUtil.ucs_logout(handle)
        return jsonify({"templates": ucs_templates}), Const.HTTP_OK

    @staticmethod
    def update_template(server_group, req):
        db = YamlDB()
        msg = db.assign_template(Const.KUBAM_CFG, req, server_group)
        return jsonify({"status": msg}), Const.HTTP_CREATED

    @staticmethod
    def delete_template(server_group, req):
        db = YamlDB()
        msg = db.delete_template(Const.KUBAM_CFG, req, server_group)
        return jsonify({"status": msg}), Const.HTTP_NO_CONTENT


@servers.route(Const.API_ROOT2 + "/servers", methods=["GET", "POST", "PUT", "DELETE"])
@cross_origin()
def server_handler():
    if request.method == "GET":
        j, rc = Servers.list_servers()
    elif request.method == "POST":
        j, rc = Servers.create_servers(request.json)
    elif request.method == "PUT":
        j, rc = Servers.update_servers(request.json)
    elif request.method == "DELETE":
        j, rc = Servers.delete_servers(request.json)
    else:
        j = {"error": "Unknown HTTP method, aborting."}
        rc = Const.HTTP_NOT_ALLOWED
        current_app.log.error(j)
    return jsonify(j), rc


@servers.route(Const.API_ROOT2 + "/servers/<server_group>/templates", methods=["GET", "POST", "PUT", "DELETE"])
@cross_origin()
def template_handler(server_group):
    try:
        if request.method == "GET":
            j, rc = Templates.list_templates(server_group)
        elif request.method == "POST" or request.method == "PUT":
            j, rc = Templates.update_template(server_group, request.json)
        elif request.method == "DELETE":
            j, rc = Templates.delete_template(server_group, request.json)
        else:
            j = "Unknown HTTP method, aborting."
            rc = Const.HTTP_NOT_ALLOWED
            current_app.log.error(j)
    except KubamError as e:
        current_app.log.error(e)
        j = str(e)
        rc = Const.HTTP_SERVER_ERROR
    return j, rc


@servers.route(Const.API_ROOT2 + "/servers/<server_group>/servers", methods=["GET"])
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
        return jsonify({"error": msg}), Const.HTTP_UNAUTHORIZED
    ucs_servers = UCSServer.list_servers(handle)
    UCSUtil.ucs_logout(handle)

    # Gets a hash of severs of form:
    # {blades: ["1/1", "1/2",..], rack: ["6", "7"]}
    db = YamlDB()
    err, msg, db_servers = db.get_ucs_servers(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    ucs_servers = UCSUtil.servers_to_api(ucs_servers, db_servers)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    return jsonify({"servers": ucs_servers}), Const.HTTP_OK

@servers.route(Const.API_ROOT2 + "/servers/<server_group>/servers", methods=['GET'])
@cross_origin()
def deploy_servers(server_group):
    """
    Given a server group, deploy the resources in this form: 
    1. If a service profile template is defined, create a sp from the template and associate
    2. If no service profile is defined, create all resources (like we did before)
    """

    db = YamlDB()
    err, msg, sg = db.get_server_group(Const.KUBAM_CFG, server_group)
    err, msg, handle = UCSUtil.ucs_login(sg)

    UCSUtil.ucs_logout(handle)

    # It may also be that they pass parameters of which hosts in the server group, so we need to 
    # check that these are in the server group as well.  

