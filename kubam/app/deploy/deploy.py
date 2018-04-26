from flask import Blueprint, jsonify, current_app
from flask_cors import cross_origin
from ucs import UCSProfile
from config import Const

deploy = Blueprint("deploy", __name__)


# The grand daddy of them all, it is what deploys everything
@deploy.route(Const.API_ROOT + "/deploy", methods=['POST'])
@cross_origin()
def deploy_server():
    err, msg = UCSProfile.make_ucs()
    if err != 0:
        return jsonify({'error': msg}), 400

    # now call the deployment!
    return jsonify({"status": "ok"}), 201


# Dangerous command, it will undo everything
@deploy.route(Const.API_ROOT + "/deploy", methods=['DELETE'])
@cross_origin()
def destroy_server():
    current_app.logger.info("Deleting deployment")
    err, msg = UCSProfile.destroy_ucs()
    if err != 0:
        return jsonify({'error:': msg}), 400
    elif msg == "ok":
        return jsonify({'status': "ok"}), 201
    else:
        return jsonify({'status': msg}), 200
