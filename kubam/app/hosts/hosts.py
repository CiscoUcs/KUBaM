from flask import jsonify, request, Blueprint
from flask_cors import cross_origin
from db import YamlDB
from config import Const

hosts = Blueprint("hosts", __name__)


class Hosts(object):
    # list the server group information
    @staticmethod
    def list_hosts():
        """
        / basic test to see if site is up.
        should return { 'status' : 'ok'}
        """
        err, msg, host_list = YamlDB.list_hosts(Const.KUBAM_CFG)
        if err == 1:
            return {'error': msg}, 500
        return {"hosts": host_list}, 200

    # create a new server group
    @staticmethod
    def create_hosts(req):
        """
        Create a new host entry
        Format of request should be JSON that looks like:
        {"name", "aci01", "credentials" : {"user": "admin", "password" : "secret-password", "ip" : "172.28.225.163" }, ...}
        """
        err, msg = YamlDB.new_hosts(Const.KUBAM_CFG, req)
        if err == 1:
            return {'error': msg}, 400
        return {'status': "Hosts %s created!" % req["name"]}, 201

    @staticmethod
    def update_hosts(req):
        # TODO Complete me!
        return {"status": "ok"}, 200

    @staticmethod
    def delete_hosts(req):
        """
        Delete the ACI group from the config.
        """
        uuid = req['id']
        err, msg = YamlDB.delete_hosts(Const.KUBAM_CFG, uuid)
        if err == 1:
            return {'error': msg}, 400
        else:
            return {'status': "Hosts deleted"}, 201


@hosts.route(Const.API_ROOT2 + "/hosts", methods=['GET', 'POST', 'PUT', 'DELETE'])
@cross_origin()
def host_handler():
    if request.method == 'POST':
        j, rc = Hosts.create_hosts(request.json)
    elif request.method == 'PUT':
        j, rc = Hosts.update_hosts(request.json)
    elif request.method == 'DELETE':
        j, rc = Hosts.delete_hosts(request.json)
    else:
        j, rc = Hosts.list_hosts()
    return jsonify(j), rc
