from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from config import Const
from db import YamlDB

util = Blueprint("util", __name__)
db = YamlDB()


# Get the capabilities of Kubam
@util.route(Const.API_ROOT + "/catalog", methods=['GET'])
@cross_origin()
def get_catalog():
    catalog = Const.CATALOG
    return jsonify(catalog), 200


# Get the Kubam IP address
@util.route(Const.API_ROOT + "/ip", methods=['GET'])
@cross_origin()
def get_kubam_ip():
    err, msg, kubam_ip = db.get_kubam_ip(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'kubam_ip': kubam_ip}), 200


# Update the Kubam IP address
@util.route(Const.API_ROOT + "/ip", methods=['POST'])
@cross_origin()
def update_kubam_ip():
    if not request.json:
        return jsonify({'error': 'expected request with kubam_ip '}), 400
    if "kubam_ip" not in request.json:
        return jsonify({'error': 'expected request with kubam_ip '}), 400

    kubam_ip = request.json['kubam_ip']
    err, msg = db.update_kubam_ip(Const.KUBAM_CFG, kubam_ip)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'kubam_ip': kubam_ip}), 201


# Get the public keys
@util.route(Const.API_ROOT + "/keys", methods=['GET'])
@cross_origin()
def get_public_keys():
    err, msg, keys = db.get_public_keys(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'keys': keys}), 200


# Update the public keys
@util.route(Const.API_ROOT + "/keys", methods=['POST'])
@cross_origin()
def update_public_keys():
    if not request.json:
        return jsonify({'error': "expected request with keys "}), 400
    if "keys" not in request.json:
        return jsonify({'error': "expected request with keys "}), 400

    keys = request.json['keys']
    err, msg = db.update_public_keys(Const.KUBAM_CFG, keys)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'keys': keys}), 201


# Get the proxy settings
@util.route(Const.API_ROOT + "/proxy", methods=['GET'])
@cross_origin()
def get_proxy():
    err, msg, keys = db.get_proxy(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'proxy': keys}), 200


# Update the proxy settings
@util.route(Const.API_ROOT + "/proxy", methods=['POST'])
@cross_origin()
def update_proxy():
    if not request.json:
        return jsonify({'error': 'expected request with proxy '}), 400
    if "proxy" not in request.json:
        return jsonify({'error': 'expected request with proxy'}), 400

    proxy = request.json['proxy']
    err, msg = db.update_proxy(Const.KUBAM_CFG, proxy)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'proxy': proxy}), 201


# Get the organisation from the UCSM
@util.route(Const.API_ROOT + "/org", methods=['GET'])
@cross_origin()
def get_org():
    err, msg, org = db.get_org(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'org': org}), 200


# Update the organisation in the UCSM
@util.route(Const.API_ROOT + "/org", methods=['POST'])
@cross_origin()
def update_ucs_org():
    if not request.json:
        return jsonify({'error': "expected request with org"}), 400
    if "org" not in request.json:
        return jsonify({'error': "expected request with org"}), 400

    org = request.json['org']
    err, msg = db.update_org(Const.KUBAM_CFG, org)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'org': org}), 201


@util.route(Const.API_ROOT + "/settings", methods=['POST'])
@cross_origin()
def update_settings():
    if not request.json:
        return jsonify({'error': "expected kubam_ip and keys in json request"}), 400
    if "kubam_ip" not in request.json:
        return jsonify({'error': "Please enter the IP address of the kubam server"}), 400
    if "keys" not in request.json:
        return jsonify({
            'error': "Please specify keys. See documentation for how this should look: "
                     "https://ciscoucs.github.io/kubam/docs/settings."
        }), 400

    # Proxy and org fields are not mandatory
    if "proxy" in request.json:
        proxy = request.json['proxy']
        err, msg = db.update_proxy(Const.KUBAM_CFG, proxy)
        if err != 0:
            return jsonify({'error': msg}), 400

    if "org" in request.json:
        org = request.json['org']
        err, msg = db.update_org(Const.KUBAM_CFG, org)
        if err != 0:
            return jsonify({'error': msg}), 400

    # Update the Kubam IP if it is changed
    ip = request.json['kubam_ip']
    err, msg = db.update_kubam_ip(Const.KUBAM_CFG, ip)
    if err != 0:
        return jsonify({'error': msg}), 400

    # Update the keys if changed
    keys = request.json['keys']
    err, msg = db.update_public_keys(Const.KUBAM_CFG, keys)
    if err != 0:
        return jsonify({'error': msg}), 400

    return jsonify({"status": "ok"}), 201
