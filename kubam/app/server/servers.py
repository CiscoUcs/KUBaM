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
        try:
            UCSUtil.check_ucs_login(req)
        except KubamError as e:
            return {"error": str(e)}, Const.HTTP_UNAUTHORIZED
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
        try:
            UCSUtil.check_ucs_login(req)
        except KubamError as e:
            return {"error": str(e)}, Const.HTTP_UNAUTHORIZED
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
    def get_templates(server_group):
        db = YamlDB()
        sg = db.get_server_group(Const.KUBAM_CFG, server_group)
        handle = UCSUtil.ucs_login(sg)
        ucs_templates = UCSTemplate.list_templates(handle)
        UCSUtil.ucs_logout(handle)
        return ucs_templates

    def list_templates(self, server_group):
        """
        Get the service profile templates in the server group.
        """
        ucs_templates = self.get_templates(server_group)
        return {"templates": ucs_templates}, Const.HTTP_OK

    def update_templates(self, server_group, req):
        ucs_templates = self.get_templates(server_group)
        db = YamlDB()
        msg = db.assign_template(Const.KUBAM_CFG, req, server_group, ucs_templates)
        return {"status": msg}, Const.HTTP_CREATED

    def delete_templates(self, server_group, req):
        ucs_templates = self.get_templates(server_group)
        db = YamlDB()
        msg = db.delete_template(Const.KUBAM_CFG, req, server_group, ucs_templates)
        return {"status": msg}, Const.HTTP_NO_CONTENT


@servers.route(Const.API_ROOT2 + "/servers", methods=["GET", "POST", "PUT", "DELETE"])
@cross_origin()
def server_handler():
    try:
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
            current_app.logger.error(j)
    except KubamError as e:
        current_app.logger.error(e)
        j = {"error": str(e)}
        rc = Const.HTTP_BAD_REQUEST
    return jsonify(j), rc


@servers.route(Const.API_ROOT2 + "/servers/<server_group>/templates", methods=["GET", "POST", "PUT", "DELETE"])
@cross_origin()
def template_handler(server_group):
    try:
        t = Templates()
        if request.method == "GET":
            j, rc = t.list_templates(server_group)
        elif request.method == "POST" or request.method == "PUT":
            j, rc = t.update_templates(server_group, request.json)
        elif request.method == "DELETE":
            j, rc = t.delete_templates(server_group, request.json)
        else:
            j = "Unknown HTTP method, aborting."
            rc = Const.HTTP_NOT_ALLOWED
            current_app.logger.error(j)
    except KubamError as e:
        current_app.logger.error(e)
        j = {"error": str(e)}
        rc = Const.HTTP_BAD_REQUEST
    return jsonify(j), rc


@servers.route(Const.API_ROOT2 + "/servers/<server_group>/servers", methods=["GET"])
@cross_origin()
def get_servers(server_group):
    """
    List all the servers in the server group
    or in this case the domain. 
    1. Make call to UCS to grab the servers. 
    2. Make call to database to see which ones are selected.
    3. Call servers_to_api which merges the two adding 'selected: true' to the servers that are selected.
    """
    db = YamlDB()
    try:
        sg = db.get_server_group(Const.KUBAM_CFG, server_group)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    try:
        handle = UCSUtil.ucs_login(sg)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_UNAUTHORIZED
    ucs_servers = UCSServer.list_servers(handle)
    UCSUtil.ucs_logout(handle)

    # Gets a hash of severs of form:
    # {blades: ["1/1", "1/2",..], rack: ["6", "7"]}
    err, msg, db_servers = db.get_ucs_servers(Const.KUBAM_CFG, server_group)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    ucs_servers = UCSUtil.servers_to_api(ucs_servers, db_servers)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    return jsonify({"servers": ucs_servers}), Const.HTTP_OK


@servers.route(Const.API_ROOT2 + "/servers/<server_group>/servers", methods=['POST'])
@cross_origin()
def select_servers(server_group):
    """
    Given a server group, select the servers from the server group (if this is UCS) that should be 
    selected to be deployed and placed in a kubam group
    """
    # make sure we got some data.
    if not request.json:
        return jsonify({"error": "expected hash of servers"}), Const.HTTP_BAD_REQUEST
    if "servers" not in request.json:
        return jsonify({"error": "expected 'servers' with hash of servers in request"}), Const.HTTP_BAD_REQUEST
    # we expect servers to be a hash of like:
    # {blades: ["1/1", "1/2",..], rack: ["6", "7"]}
    ucs_servers = request.json['servers']
    # translate to db
    usc_servers = UCSUtil.servers_to_db(ucs_servers)
    if usc_servers:
        db = YamlDB()
        err, msg = db.update_ucs_servers(Const.KUBAM_CFG, usc_servers, server_group)
        if err != 0:
            return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST

    return jsonify({"status": "ok"}), Const.HTTP_CREATED


@servers.route(Const.API_ROOT2 + "/servers/<server_group>/deploy", methods=['POST'])
@cross_origin()
def deploy_servers(server_group):
    """
    Given a server group, deploy the resources in this form: 
    1. If a service profile template is defined, create a sp from the template and associate
    2. If no service profile is defined, create all resources (like we did before)
    """

    db = YamlDB()
    try:
        sg = db.get_server_group(Const.KUBAM_CFG, server_group)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST
    org = "org-root"
    if "org" in sg:
        org = sg["org"]

    err, msg, hosts = db.get_hosts_in_server_group(Const.KUBAM_CFG, server_group)
    
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    if len(hosts) < 1:
        return jsonify({"error": "No hosts defined in the server group"}), Const.HTTP_BAD_REQUEST

    try:
        handle = UCSUtil.ucs_login(sg)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    for h in hosts:
        if "service_profile_template" in h:
            err, msg = UCSServer.make_profile_from_template(handle, org, h)
            if err != 0:
                UCSUtil.ucs_logout(handle)
                return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
        else:
            print "This part is not implemented yet"

    UCSUtil.ucs_logout(handle)
    return jsonify({"status": hosts}), Const.HTTP_CREATED


@servers.route(Const.API_ROOT2 + "/servers/<server_group>/clone", methods=['POST'])
@cross_origin()
def clone_template(server_group):
    """
    Given a server group and selected service profile template, deploy the resources in this form:
    1. Clone an existing service profile template
    2. Create and assign vMedia policy and change the boot order to boot the vMedia policy
    """
    # TODO Create me
    pass
