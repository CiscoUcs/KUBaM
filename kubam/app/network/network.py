from flask import jsonify, request, Blueprint
from flask_cors import cross_origin
from db import YamlDB
from config import Const

network = Blueprint("network", __name__)


class Network(object):
    # list the server group information
    @staticmethod
    def list():
        """
        Lists all the network groups
        """
        err, msg, net_list = YamlDB.list_network_group(Const.KUBAM_CFG)
        if err == 1:
            return {'error': msg}, 500
        return {"networks": net_list}, 200

    # create a new server group
    @staticmethod
    def create(req):
        """
        Create a new network group
        """
        err, msg = YamlDB.new_network_group(Const.KUBAM_CFG, req)
        if err == 1:
            return {'error': msg}, 400
        return {'status': "Network %s created!" % req["name"]}, 201

    @staticmethod
    def update(req):
        """
        Update Netowork settings of one of the network groups.
        """
        err, msg = YamlDB.update_network_group(Const.KUBAM_CFG, req)
        if err == 1:
            return {'error': msg}, 400
        return {"status": "ok"}, 200

    @staticmethod
    def delete(req):
        """
        Delete the network group from the config.
        """
        uuid = req['id']
        err, msg = YamlDB.delete_network(Const.KUBAM_CFG, uuid)
        if err == 1:
            return {'error': msg}, 400
        else:
            return {'status': "Network deleted"}, 201


@network.route(Const.API_ROOT2 + "/networks", methods=['GET', 'POST', 'PUT', 'DELETE'])
@cross_origin()
def network_handler():
    if request.method == 'POST':
        j, rc = Network.create(request.json)
    elif request.method == 'PUT':
        j, rc = Network.update(request.json)
    elif request.method == 'DELETE':
        j, rc = Network.delete(request.json)
    else:
        j, rc = Network.list()
    return jsonify(j), rc
