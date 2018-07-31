from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
from ucs import UCSProfile
from autoinstall import Builder, IsoMaker
from db import YamlDB
from config import Const

deploy = Blueprint("deploy", __name__)


class Deployments(object):

    @staticmethod
    def get_valid_hosts(host_list):
        valid_hosts = []
        db = YamlDB()
        err, msg, hosts = db.list_hosts(Const.KUBAM_CFG)
        if err != 0:
            return err, msg, hosts
        if isinstance(host_list, list):
            for i in host_list:
                valid_host = [x for x in hosts if x["name"] == i]
                if len(valid_host) == 0:
                    return 1, "{0} is not a valid host".format(i), ""
                valid_hosts.append(valid_host[0])
        else: 
            valid_hosts = hosts
        return 0, None, valid_hosts

    @staticmethod
    def get_valid_isos(os_list):
        valid_os = []
        db = YamlDB()
        err, msg, iso_map = db.get_iso_map(Const.KUBAM_CFG)
        if err != 0:
            return 1, msg, None
        if iso_map == None:
            return 1, "Please upload ISO Images first", None
        for i in os_list:
            valid_iso = [x for x in iso_map if x["os"] == i]
            if not i in [x["os"] for x in iso_map]:
                return 1, "Please map {0} to an iso image".format(i), None
            valid_os.append(valid_iso[0])
        return 0, None, valid_os
        
        

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
        ["host01", "host02", ... ] or no arguments.  
        """
        err, msg, hosts = Deployments.get_valid_hosts(req)
        if err != 0:
            return {'error': msg}, 400
       
        # get all the oses that need to be installed. 
        oses = list(set([x["os"] for x in hosts]))
        # check that we have ISO mapped images for each one
        err, msg, isos = Deployments.get_valid_isos(oses)
        if err != 0:
            return {'error': msg}, 400
        # if the iso image isn't already exploded, extract it. 
        err, msg = IsoMaker.extract_isos(isos)
        if err != 0:
            return {'error': msg}, 400
        # if the boot image isn't already created, create it. 
        err, msg = IsoMaker.mkboot_isos(isos) 
        if err != 0:
            return {'error': msg}, 400
        # always go through and create the auto installation media for each server. 
        err, msg = Builder.make_images(hosts)
        if err != 0:
            return {'error': msg}, 400
        return {'status': "server images created!"}, 201


@deploy.route(Const.API_ROOT2 + "/deploy/images", methods=['POST', 'GET', 'DELETE'])
@cross_origin()
def deploy_image_handler():
    if request.method == 'POST':
        j, rc = Deployments.create_images(request.json)
    else:
        j, rc = Deployments.list_images()
    return jsonify(j), rc
