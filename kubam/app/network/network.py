from flask import jsonify, request, current_app, Blueprint
from flask_cors import cross_origin
from db import YamlDB
from config import Const
from helper import KubamError

networks = Blueprint("networks", __name__)


class Network(object):
    # list the server group information
    @staticmethod
    def list_network():
        """
        Lists all the network groups
        """
        db = YamlDB()
        err, msg, net_list = db.list_network_group(Const.KUBAM_CFG)
        if err == 1:
            return {"error": msg}, Const.HTTP_SERVER_ERROR
        return {"networks": net_list}, Const.HTTP_OK

    # create a new server group
    @staticmethod
    def create_network(req):
        """
        Create a new network group
        """
        db = YamlDB()
        err, msg = db.new_network_group(Const.KUBAM_CFG, req)
        if err == 1:
            return {"error": msg}, Const.HTTP_BAD_REQUEST
        return {"status": "Network {0} created!".format(req['name'])}, Const.HTTP_CREATED

    @staticmethod
    def update_network(req):
        """
        Update network settings of one of the network groups.
        """
        db = YamlDB()
        err, msg = db.update_network_group(Const.KUBAM_CFG, req)
        if err == 1:
            return {"error": msg}, Const.HTTP_BAD_REQUEST
        return {"status": "ok"}, Const.HTTP_CREATED

    @staticmethod
    def delete_network(req):
        """
        Delete the network group from the config.
        """
        uuid = req['id']
        db = YamlDB()
        err, msg = db.delete_network_group(Const.KUBAM_CFG, uuid)
        if err == 1:
            return {"error": msg}, Const.HTTP_BAD_REQUEST
        else:
            return {"status": "Network deleted"}, Const.HTTP_CREATED


@networks.route(Const.API_ROOT2 + "/networks", methods=["GET", "POST", "PUT", "DELETE"])
@cross_origin()
def network_handler():
    try:
        if request.method == "GET":
            j, rc = Network.list_network()
        elif request.method == "POST":
            j, rc = Network.create_network(request.json)
        elif request.method == "PUT":
            j, rc = Network.update_network(request.json)
        elif request.method == "DELETE":
            j, rc = Network.delete_network(request.json)
        else:
            j = "Unknown HTTP method, aborting."
            rc = Const.HTTP_NOT_ALLOWED
            current_app.logger.error(j)
    except KubamError as e:
        current_app.log.error(e)
        j = {"error": str(e)}
        rc = Const.HTTP_SERVER_ERROR
    return jsonify(j), rc
