from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
from ucs import UCSProfile
from config import Const

deploy = Blueprint("deploy", __name__)


class Deployments(object):
    # List the server group information
    @staticmethod
    def list_images():
        """
        / list the deployments that are ready to go
        """
        return {"deployments": ""}, 200

    @staticmethod
    def create_images(req):
        """
        Create a new deployment
        ["host01", "host02", ... ]
        """
    # Get the ISO map
    #db = YamlDB()
    #err, msg, iso_images = db.get_iso_map(Const.KUBAM_CFG)
    #if err != 0:
    #    return jsonify({"error": msg}), 400
    #if len(iso_images) == 0:
    #    return jsonify({"error": "No ISOS have been mapped.  Please map an ISO image with an OS"}), 400
    #iso_maker = IsoMaker()
    #err, msg = iso_maker.mkboot_iso(isos)
    #if err != 0:
    #    return jsonify({"error": msg}), 400
#
#    builder = Builder()
#    err, msg = builder.deploy_server_images(Const.KUBAM_CFG)
#    if err != 0:
#        return jsonify({"error": msg}), 400
#    return jsonify({"status": "ok"}), 201
        return {'status': "server images created!"}, 201


@deploy.route(Const.API_ROOT2 + "/deploy/images", methods=['POST', 'GET', 'DELETE'])
@cross_origin()
def deploy_image_handler():
    if request.method == 'POST':
        j, rc = Deployments.create_images(request.json)
    else:
        j, rc = Deployments.list_images()
    return jsonify(j), rc


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
