from flask import jsonify, request, Blueprint
from flask_cors import cross_origin
from db import YamlDB
from config import Const
from ucs import UCSSession

session = Blueprint("session", __name__)


# Determine if we have credentials stored or not
@session.route(Const.API_ROOT + "/session", methods=['GET'])
@cross_origin()
def get_credentials():
    credentials = {}
    err, msg, config = YamlDB.open_config(Const.KUBAM_CFG)
    if err == 0:
        if "ucsm" in config and "credentials" in config["ucsm"]:
            credentials = config["ucsm"]["credentials"]
            if "user" in credentials and "password" in credentials and "ip" in credentials:
                credentials["password"] = "REDACTED"
                # session.logger.info(credentials)
    return jsonify({'credentials': credentials}), 200


# Every call logs in and logs out
@session.route(Const.API_ROOT + "/session", methods=['POST'])
@cross_origin()
def create_credentials():
    if not request.json:
        return jsonify({'error': 'expected credentials hash'}), 400

    credentials = dict()
    credentials['user'] = request.json['credentials']['user']
    credentials['password'] = request.json['credentials']['password']
    credentials['ip'] = request.json['credentials']['server']
    if credentials['ip'] == "":
        return jsonify({'error': "Please enter a valid UCSM IP address."}), 401
    # session.logger.info("starting login attempt to UCS.")
    ucs_session = UCSSession()
    h, err = ucs_session.login(credentials['user'], credentials['password'], credentials['ip'])
    if not h:
        return jsonify({'error': err}), 401
    # Write datafile
    YamlDB.update_ucs_creds(Const.KUBAM_CFG, credentials)
    UCSSession.logout(h)
    return jsonify({'login': "success"}), 201


@session.route(Const.API_ROOT + "/session", methods=['DELETE'])
@cross_origin()
def delete_session():
    YamlDB.update_ucs_creds(Const.KUBAM_CFG, "")
    return jsonify({'logout': "success"})
