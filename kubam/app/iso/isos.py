from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from db import YamlDB
from config import Const
from autoinstall import Builder, IsoMaker

isos = Blueprint("isos", __name__)


# List ISO images
@isos.route(Const.API_ROOT + "/isos", methods=['GET'])
@cross_origin()
def get_isos():
    err, iso_images = IsoMaker.list_isos("/kubam")
    if err != 0:
        return jsonify({'error': iso_images})
    return jsonify({'isos': iso_images}), 200



#TODO: Remove this method as this is the old one. 
# Make the boot ISO image of an ISO
@isos.route(Const.API_ROOT + "/isos/boot", methods=['POST'])
@cross_origin()
def mkboot_iso():
    # Get the ISO map
    db = YamlDB()
    err, msg, iso_images = db.get_iso_map(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({"error": msg}), 400
    if len(iso_images) == 0:
        return jsonify({"error": "No ISOS have been mapped.  Please map an ISO image with an OS"}), 400
    iso_maker = IsoMaker()
    err, msg = iso_maker.mkboot_iso(isos)
    if err != 0:
        return jsonify({"error": msg}), 400

    builder = Builder()
    err, msg = builder.deploy_server_images(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({"error": msg}), 400
    return jsonify({"status": "ok"}), 201


# Map the ISO images to OS versions
@isos.route(Const.API_ROOT + "/isos/map", methods=['GET'])
@cross_origin()
def get_iso_map():
    db = YamlDB()
    err, msg, iso_images = db.get_iso_map(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'iso_map': iso_images}), 200


# update iso to os map
@isos.route(Const.API_ROOT + "/isos/map", methods=['POST'])
@cross_origin()
def update_iso_map():
    if not request.json:
        return jsonify({'error': 'expected request with iso_map '}), 400
    if "iso_map" not in request.json:
        return jsonify({'error': 'expected request with iso_map '}), 400

    iso_images = request.json['iso_map']
    db = YamlDB()
    err, msg = db.update_iso_map(Const.KUBAM_CFG, iso_images)
    if err != 0:
        return jsonify({'error': msg}), 400
    return get_iso_map()
