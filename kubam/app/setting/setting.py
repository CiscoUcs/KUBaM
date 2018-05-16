from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from config import Const
from db import YamlDB

setting = Blueprint("setting", __name__)
db = YamlDB()


# Get the capabilities of Kubam
@setting.route(Const.API_ROOT + "/catalog", methods=["GET"])
@cross_origin()
def get_catalog():
    catalog = Const.CATALOG
    return jsonify(catalog), Const.HTTP_OK


# Get the Kubam IP address
@setting.route(Const.API_ROOT + "/ip", methods=["GET"])
@cross_origin()
def get_kubam_ip():
    err, msg, kubam_ip = db.get_kubam_ip(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    return jsonify({"kubam_ip": kubam_ip}), Const.HTTP_OK


# Update the Kubam IP address
@setting.route(Const.API_ROOT + "/ip", methods=["POST"])
@cross_origin()
def update_kubam_ip():
    if not request.json:
        return jsonify({"error": "expected request with kubam_ip "}), Const.HTTP_BAD_REQUEST
    if "kubam_ip" not in request.json:
        return jsonify({"error": "expected request with kubam_ip "}), Const.HTTP_BAD_REQUEST

    kubam_ip = request.json['kubam_ip']
    err, msg = db.update_kubam_ip(Const.KUBAM_CFG, kubam_ip)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    return jsonify({"kubam_ip": kubam_ip}), Const.HTTP_CREATED


# Get the public keys
@setting.route(Const.API_ROOT + "/keys", methods=["GET"])
@cross_origin()
def get_public_keys():
    err, msg, keys = db.get_public_keys(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    return jsonify({"keys": keys}), Const.HTTP_OK


# Update the public keys
@setting.route(Const.API_ROOT + "/keys", methods=["POST"])
@cross_origin()
def update_public_keys():
    if not request.json:
        return jsonify({"error": "expected request with keys"}), Const.HTTP_BAD_REQUEST
    if "keys" not in request.json:
        return jsonify({"error": "expected request with keys"}), Const.HTTP_BAD_REQUEST

    keys = request.json['keys']
    err, msg = db.update_public_keys(Const.KUBAM_CFG, keys)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    return jsonify({"keys": keys}), Const.HTTP_CREATED


# Get the proxy setting
@setting.route(Const.API_ROOT + "/proxy", methods=["GET"])
@cross_origin()
def get_proxy():
    err, msg, keys = db.get_proxy(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    return jsonify({"proxy": keys}), Const.HTTP_OK


# Update the proxy setting
@setting.route(Const.API_ROOT + "/proxy", methods=["POST"])
@cross_origin()
def update_proxy():
    if not request.json:
        return jsonify({"error": "expected request with proxy"}), Const.HTTP_BAD_REQUEST
    if "proxy" not in request.json:
        return jsonify({"error": "expected request with proxy"}), Const.HTTP_BAD_REQUEST

    proxy = request.json["proxy"]
    err, msg = db.update_proxy(Const.KUBAM_CFG, proxy)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    return jsonify({"proxy": proxy}), Const.HTTP_CREATED


# Get the organisation from the UCSM
@setting.route(Const.API_ROOT + "/org", methods=["GET"])
@cross_origin()
def get_org():
    err, msg, org = db.get_org(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    return jsonify({"org": org}), Const.HTTP_OK


# Update the organisation in the UCSM
@setting.route(Const.API_ROOT + "/org", methods=["POST"])
@cross_origin()
def update_ucs_org():
    if not request.json:
        return jsonify({"error": "expected request with org"}), Const.HTTP_BAD_REQUEST
    if "org" not in request.json:
        return jsonify({"error": "expected request with org"}), Const.HTTP_BAD_REQUEST

    org = request.json["org"]
    err, msg = db.update_org(Const.KUBAM_CFG, org)
    if err != 0:
        return jsonify({"error": msg}), Const.HTTP_BAD_REQUEST
    return jsonify({"org": org}), Const.HTTP_CREATED
