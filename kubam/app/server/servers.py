from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
from ucs import UCSServer, UCSTemplate, UCSUtil
from ucsc import UCSCServer, UCSCTemplate, UCSCUtil
from imc import IMCServer, IMCUtil
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
        err, msg = YamlDB.check_valid_server_group(req)
        if err != 0:
            return {"error": msg}, Const.HTTP_BAD_REQUEST
        # Make sure we can log in first.
        if not 'type' in req:
            return {"error": "No server type sent as part of request"}, Const.HTTP_UNAUTHORIZED
        if req['type'] == "ucsm":
            try:
                UCSUtil.check_ucs_login(req)
            except KubamError as e:
                return {"error": str(e)}, Const.HTTP_UNAUTHORIZED
        elif req["type"] == "ucsc":
            try:
                UCSCUtil.check_ucsc_login(req)
            except KubamError as e: 
                return {"error":str(e)}, Const.HTTP_UNAUTHORIZED
        elif req["type"] == "imc":
            try: 
                IMCUtil.check_imc_login(req)
            except KubamError as e: 
                return {"error":str(e)}, Const.HTTP_UNAUTHORIZED
        else:
            return {"error": "type: {0} is not recognized".format(req["type"])}, Const.HTTP_UNAUTHORIZED

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
        if not isinstance(req, dict):
            return {"error": "invalid parameters: {0}".format(req)}, Const.HTTP_BAD_REQUEST
        if not "name" in req:
            return {"error": "please give the server group name you wish to delete"}, Const.HTTP_BAD_REQUEST
        name = req['name']
        db = YamlDB()
        err, msg = db.delete_server_group(Const.KUBAM_CFG, name)
        if err == 1:
            return {"error": msg}, Const.HTTP_BAD_REQUEST
        else:
            return {"status": "Server group deleted"}, Const.HTTP_NO_CONTENT


class Templates(object):
    @staticmethod
    def get_templates(server_group):
        db = YamlDB()
        sg = db.get_server_group(Const.KUBAM_CFG, server_group)
        ucs_templates = []
        if sg['type'] == "ucsc":
            handle = UCSCUtil.ucsc_login(sg)
            ucs_templates = UCSCTemplate.list_templates(handle)
            UCSCUtil.ucsc_logout(handle)
        elif sg['type'] == "ucs":
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

    if sg['type'] == "ucsm":
        try:
            handle = UCSUtil.ucs_login(sg)
        except KubamError as e:
            return jsonify({"error": str(e)}), Const.HTTP_UNAUTHORIZED
        ucs_servers = UCSServer.list_servers(handle)
        UCSUtil.ucs_logout(handle)
    elif sg['type'] == 'ucsc':
        try:
            handle = UCSCUtil.ucsc_login(sg)
        except KubamError as e:
            return jsonify({"error": str(e)}), Const.HTTP_UNAUTHORIZED
        ucs_servers = UCSCServer.list_servers(handle)
        UCSCUtil.ucsc_logout(handle)

    # Gets a hash of severs of form:
    # {blades: ["1/1", "1/2",..], rack: ["6", "7"]}
    err, msg, db_servers = db.get_ucs_servers(Const.KUBAM_CFG, server_group)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    if db_servers is None:
        return jsonify({"servers": ucs_servers})

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
    # {servers: {blades: ["1/1", "1/2",..], rack: ["6", "7"]}}
    ucs_servers = request.json['servers']
    if ucs_servers:
        db = YamlDB()
        err, msg = db.update_ucs_servers(Const.KUBAM_CFG, ucs_servers, server_group)
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
    #TODO: deploy only hosts that are given as parameters. 
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

    if sg['type'] == 'ucsc':
        return deploy_ucsc(sg, hosts, org) 
    elif sg['type'] == 'ucsm':
        return deploy_ucs(sg, hosts, org)

    return jsonify({"error": "server group type is not supported.".format(sg['type'])}), Const.HTTP_BAD_REQUEST
  
def deploy_ucs(sg, hosts, org):
    """
    Deploy UCS hosts
    """
    try:
        handle = UCSUtil.ucs_login(sg)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST
    for h in hosts:
        if "service_profile_template" in h:
            err = 0
            msg = ""
            err, msg = UCSServer.make_profile_from_template(handle, org, h)
            if err != 0:
                UCSUtil.ucs_logout(handle)
                return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
            if "server" in h:
                err, msg = UCSServer.associate_server(handle,org,h)
        else:
            # TODO: Create this part. 
            print "This part is not implemented yet"
    UCSUtil.ucs_logout(handle)
    return jsonify({"status": hosts}), Const.HTTP_CREATED


def deploy_ucsc(sg, hosts, org):  
    """
    Deploy UCSC resources
    """
    try:
        handle = UCSCUtil.ucsc_login(sg)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    for h in hosts:
        if "service_profile_template" in h:
            err = 0
            msg = ""
            err, msg = UCSCServer.make_profile_from_template(handle, org, h)
            if err != 0:
                UCSCUtil.ucsc_logout(handle)
                return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
            # associate the server if it is called out. 
            if "server" in h:
                err, msg = UCSCServer.associate_server(handle,org,h)
        else:
            # TODO: Create this part. 
            print "This part is not implemented yet"

    UCSCUtil.ucsc_logout(handle)
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


@servers.route(Const.API_ROOT2 + "/servers/<server_group>/vmedia", methods=['POST'])
@cross_origin()
def create_vmedia(server_group):
    """
    Create the Vmedia policy for a server group
    """
    db = YamlDB()
    # get server group. 
    try:
        sg = db.get_server_group(Const.KUBAM_CFG, server_group)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    org = "org-root"
    if "org" in sg:
        org = sg["org"]
    # go through all hosts associated with this server group
    err, msg, hosts = db.list_hosts(Const.KUBAM_CFG)
    if err == 1:
        return jsonify({'error': msg}), Const.HTTP_BAD_REQUEST
    hosts = [x for x in hosts if 'server_group' in x and x['server_group'] == server_group]
    if len(hosts) < 1:
        return jsonify({'error': 'no hosts associated with server group'}), Const.HTTP_OK
    # get the os image they use
    oses = list(set([ x["os"] for x in hosts]))
    # create those vmedia policies
    err = 0
    msg = ""
    err, msg, kubam_ip = db.get_kubam_ip(Const.KUBAM_CFG)
    if kubam_ip is None:
        return jsonify({'error': 'Please define the  KUBAM IP first.'} ), Const.HTTP_OK
    handle = ""
    if sg['type'] == 'ucsm':
        try:
            handle = UCSUtil.ucs_login(sg)
        except KubamError as e:
            return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

        err, msg = UCSServer.make_vmedias(handle, org, kubam_ip, oses)
        UCSUtil.ucs_logout(handle)

    elif sg['type'] == 'ucsc':
        try:
            handle = UCSCUtil.ucsc_login(sg)
        except KubamError as e:
            return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

        err, msg = UCSCServer.make_vmedias(handle, org, kubam_ip, oses)
        UCSCUtil.ucsc_logout(handle)
    elif sg['type'] == 'imc':
         
        try:
            handle = IMCUtil.imc_login(sg)
        except KubamError as e:
            return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

        try:
            IMCServer.mount_media(handle, kubam_ip, hosts[0]['name'], oses[0])
        except KubamError as e:
            IMCUtil.imc_logout(handle)
            return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST
        IMCUtil.imc_logout(handle)
            
    if err != 0:
        return jsonify({'error': msg}), Const.HTTP_BAD_REQUEST
   
    return jsonify({"status": oses}), Const.HTTP_CREATED

def servers_to_objects(handle, servers):
    """
    Get the servers from the API and turn them into the UCS objects
    So we can do operations on them. 
    """
    ucs_servers = UCSServer.list_servers(handle)
    return UCSUtil.servers_to_objects(ucs_servers, servers)
    
    
def ucsc_servers_to_objects(handle, servers):
    """
    Get the servers from the API and turn them into the UCS objects
    So we can do operations on them. 
    """
    ucs_servers = UCSCServer.list_servers(handle)
    return UCSCUtil.servers_to_objects(ucs_servers, servers)
    


def power_server(server_group, req_json, action):
    """
    Power actions for a server: off, on, hardreset, softreset
    """
    db = YamlDB()
    # get server group. 
    servers = ""
    try:
        sg = db.get_server_group(Const.KUBAM_CFG, server_group)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    try:
        servers = req_json['servers']
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST
    
    # find out if server is ucsc or ucs
    err = 0
    msg = ""
    powerstat = ""
    
    if sg['type'] == "ucsm":
        return power_server_ucsm(sg, servers, action)
    elif sg['type'] == "ucsc":
        return power_server_ucsc(sg, servers, action)
   


def power_server_ucsm(sg, servers, action): 
    """
    perform power operations (hardreset, off, on..) for UCS Manager. 
    """
    # we expect servers to be a hash of like:
    # {blades: ["1/1", "1/2",..], rack: ["6", "7"]}
    try:
        handle = UCSUtil.ucs_login(sg)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_UNAUTHORIZED
    try: 
        ucs_servers = servers_to_objects(handle, servers) 
    except KubamError as e:
        UCSUtil.ucs_logout(handle)
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    for i in ucs_servers:
        try: 
            UCSServer.power_server(handle, i, action)
        except KubamError as e:
            UCSUtil.ucs_logout(handle)
            return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST
    UCSUtil.ucs_logout(handle)
    powerstat = UCSUtil.objects_to_servers(ucs_servers, ["oper_power"])
    return jsonify({"status": powerstat}), Const.HTTP_CREATED

def power_server_ucsc(sg, servers, action):
    """
    perform power operations (hardreset, off, on..) for UCS Central
    """
    try:
        handle = UCSCUtil.ucsc_login(sg)
    except Exception as e:
        return jsonify({"error": str(e)}), Const.HTTP_UNAUTHORIZED
    try:
        ucsc_servers = ucsc_servers_to_objects(handle, servers)
    except KubamError as e:
        UCSCUtil.ucsc_logout(handle)
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    for i in ucsc_servers:
        try:
            UCSCServer.power_server(handle, i, action)
        except KubamError as e:
            UCSUtil.ucs_logout(handle)
            return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST

    UCSUtil.ucs_logout(handle)
    powerstat = UCSCUtil.objects_to_servers(ucsc_servers, ["oper_power"])
    return jsonify({"status": powerstat}), Const.HTTP_CREATED
    




@servers.route(Const.API_ROOT2 + "/servers/<server_group>/power/<method>", methods=['PUT'])
@cross_origin()
def power_operation(server_group, method):
    if not request.json:
        return jsonify({"error": "no json data was passed in. example might be: ['1/1', '1/2']"}), Const.HTTP_BAD_REQUEST
    if method in ['hardreset', 'softreset', 'on', 'off']:
        return power_server(server_group, request.json, method)
    else:
        return jsonify({"error": "power method {0} is not supported. Use: on, off, hardreset, softreset".format(method)}), Const.HTTP_BAD_REQUEST

@servers.route(Const.API_ROOT2 + "/servers/<server_group>/powerstat", methods=['GET'])
@cross_origin()
def powerstat(server_group):
    """
    Get the power stat for the servers. 
    """
    powerstat = ""
    wanted_servers = "all"
    db = YamlDB()
    try:
        sg = db.get_server_group(Const.KUBAM_CFG, server_group)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST
   
    if request.json and "servers" in request.json:
        wanted_servers = request.json["servers"]
    current_app.logger.info(wanted_servers) 
    if sg['type'] == "ucsm":
        powerstat = powerstat_ucsm(sg, wanted_servers)
    elif sg['type'] == "ucsc":
        powerstat = powerstat_ucsc(sg, wanted_servers)
    else:
        return jsonify({"error": "powerstat not supported on this type of server"}), Const.HTTP_BAD_REQUEST

    return jsonify({"status" : powerstat }), Const.HTTP_OK

def powerstat_ucsm(sg, wanted_servers):
    """
    Get the power stat of the UCS Manager servers.
    """
    try:
        handle = UCSUtil.ucs_login(sg)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_UNAUTHORIZED
    try: 
        powerstat = UCSServer.list_servers(handle)
        if not wanted_servers == "all":
            powerstat = UCSUtil.servers_to_objects(powerstat, wanted_servers)
        powerstat = UCSUtil.objects_to_servers(powerstat, ["oper_power"])
    except KubamError as e:
        UCSUtil.ucs_logout(handle)
        return jsonify({"error": str(e)}), Const.HTTP_UNAUTHORIZED
    UCSUtil.ucs_logout(handle)
    return powerstat

def powerstat_ucsc(sg, wanted_servers):
    """
    Get the power status of the UCS Central servers.
    """
    try:
        handle = UCSCUtil.ucsc_login(sg)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_UNAUTHORIZED
    try: 
        powerstat = UCSCServer.list_servers(handle)
        if not wanted_servers == "all":
            powerstat = UCSCUtil.servers_to_objects(powerstat, wanted_servers)
        powerstat = UCSCUtil.objects_to_servers(powerstat, ["oper_power"])
    except KubamError as e:
        UCSCUtil.ucsc_logout(handle)
    
    UCSCUtil.ucsc_logout(handle)     
    return powerstat
