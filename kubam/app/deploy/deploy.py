from flask import Blueprint, jsonify
from flask_cors import cross_origin
from ucs import UCSUtil
from config import Const

deploy = Blueprint("deploy", __name__)
ucs_util = UCSUtil()


# The grand daddy of them all, it is what deploys everything
@deploy.route(Const.API_ROOT + "/deploy", methods=['POST'])
@cross_origin()
def deploy_server():
    err, msg = ucs_util.make_ucs()
    if err != 0:
        return jsonify({'error': msg}), 400

    # now call the deployment!
    return jsonify({"status": "ok"}), 201


# Dangerous command, it will undo everything
@deploy.route(Const.API_ROOT + "/deploy", methods=['DELETE'])
@cross_origin()
def destroy_server():
    # deploy.logger.info("Deleting deployment")
    err, msg = ucs_util.destroy_ucs()
    if err != 0:
        return jsonify({'error:': msg}), 400
    elif msg == "ok":
        return jsonify({'status': "ok"}), 201
    else:
        return jsonify({'status': msg}), 200
