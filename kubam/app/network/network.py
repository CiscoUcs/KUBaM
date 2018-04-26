from flask import jsonify, request, Blueprint
from flask_cors import cross_origin
from db import YamlDB
from config import Const
from ucs import UCSUtil, UCSNet

networks = Blueprint("networks", __name__)


class Network(object):
    # list the server group information
    @staticmethod
    def list_network():
        """
        Lists all the network groups
        """
        err, msg, net_list = YamlDB.list_network_group(Const.KUBAM_CFG)
        if err == 1:
            return {'error': msg}, 500
        return {"networks": net_list}, 200

    # create a new server group
    @staticmethod
    def create_network(req):
        """
        Create a new network group
        """
        err, msg = YamlDB.new_network_group(Const.KUBAM_CFG, req)
        if err == 1:
            return {'error': msg}, 400
        return {'status': "Network %s created!" % req["name"]}, 201

    @staticmethod
    def update_network(req):
        """
        Update Netowork settings of one of the network groups.
        """
        err, msg = YamlDB.update_network_group(Const.KUBAM_CFG, req)
        if err == 1:
            return {'error': msg}, 400
        return {"status": "ok"}, 200

    @staticmethod
    def delete_network(req):
        """
        Delete the network group from the config.
        """
        uuid = req['id']
        err, msg = YamlDB.delete_network_group(Const.KUBAM_CFG, uuid)
        if err == 1:
            return {'error': msg}, 400
        else:
            return {'status': "Network deleted"}, 201


@networks.route(Const.API_ROOT2 + "/networks", methods=['GET', 'POST', 'PUT', 'DELETE'])
@cross_origin()
def network_handler():
    if request.method == 'POST':
        j, rc = Network.create_network(request.json)
    elif request.method == 'PUT':
        j, rc = Network.update_network(request.json)
    elif request.method == 'DELETE':
        j, rc = Network.delete_network(request.json)
    else:
        j, rc = Network.list_network()
    return jsonify(j), rc


# et the networks in the UCS.
@networks.route(Const.API_ROOT + "/networks", methods=['GET'])
@cross_origin()
def get_networks():
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        return UCSUtil.not_logged_in(msg)
    vlans = UCSNet.list_vlans(handle)
    UCSUtil.ucs_logout(handle)
    err, msg, net_hash = YamlDB.get_network(Const.KUBAM_CFG)
    err, msg, net_settings = YamlDB.get_ucs_network(Const.KUBAM_CFG)
    selected_vlan = ""
    if "vlan" in net_settings:
        selected_vlan = net_settings["vlan"]

    return jsonify(
        {'vlans': [{"name": vlan.name, "id": vlan.id, "selected": (vlan.name == selected_vlan)} for vlan in vlans],
         'network': net_hash}), 200


@networks.route(Const.API_ROOT + "/networks/vlan", methods=['POST'])
@cross_origin()
def select_vlan():
    if not request.json:
        return jsonify({'error': 'expected hash of VLANs'}), 400
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        return UCSUtil.not_logged_in(msg)
    # app.logger.info("Request is: ")
    # app.logger.info(request)
    vlan = request.json['vlan']
    err, msg = YamlDB.update_ucs_network(Const.KUBAM_CFG, {"vlan": vlan})
    if err != 0:
        return jsonify({'error': msg}), 500
    # return the existing networks now with the new one chosen.
    return get_networks()


@networks.route(Const.API_ROOT + "/networks", methods=['POST'])
@cross_origin()
def update_networks():
    if not request.json:
        return jsonify({'error': 'expected hash of network settings'}), 400
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        return UCSUtil.not_logged_in(msg)
    # app.logger.info("request is")
    # app.logger.info(request.json)
    vlan = request.json['vlan']
    err, msg = YamlDB.update_ucs_network(Const.KUBAM_CFG, {"vlan": vlan})
    if err != 0:
        return jsonify({'error': msg}), 400
    network = request.json['network']
    err, msg = YamlDB.update_network(Const.KUBAM_CFG, network)
    if err != 0:
        return jsonify({'error': msg}), 400
    return get_networks()