from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from ucs import UCSUtil, UCSServer
from ucsc import UCSCUtil, UCSCServer
from db import YamlDB
from config import Const
from helper import KubamError

disks = Blueprint("disks", __name__)

class Disks(object):
    @staticmethod
    def list_ucsm(handle, wanted):
        """
        Get all the drives of the servers listed and print them out. 
            and stuff.
        """
        try:
            all_servers = UCSServer.list_servers(handle)
            ucs_servers = UCSUtil.servers_to_objects(all_servers, wanted)
        except KubamError as e:
            UCSUtil.ucs_logout(handle)
            return {"error": str(e)}, Const.HTTP_BAD_REQUEST
        disks = {} 
        from ucsmsdk.mometa.storage.StorageLocalDisk import StorageLocalDisk
        for i in ucs_servers:
            try:
                server_disks = UCSServer.list_disks(handle, i)
                disks[i['dn']] = []
                for d in server_disks:
                    # d.__dict__ flattens the object to a dictionary. 
                    kv = d.__dict__
                    kv = dict((key, value) for key, value in kv.iteritems() if not key.startswith('_') )
                    disks[i['dn']].append( kv)
            except KubamError as e:
                UCSUtil.ucs_logout(handle)
                return {"error": str(e)}, Const.HTTP_BAD_REQUEST
        
        out = UCSUtil.dn_hash_to_out(disks)
        UCSUtil.ucs_logout(handle)
        return out, Const.HTTP_OK
             
            
    @staticmethod
    def list_ucsc(handle, wanted):
        """
        Get all the drives of the servers listed and print them out. 
        """
        try:
            all_servers = UCSCServer.list_servers(handle)
            ucs_servers = UCSCUtil.servers_to_objects(all_servers, wanted)
        except KubamError as e:
            UCSCUtil.ucsc_logout(handle)
            return {"error": str(e)}, Const.HTTP_BAD_REQUEST
        disks = {} 
        from ucscsdk.mometa.storage.StorageLocalDisk import StorageLocalDisk
        for i in ucs_servers:
            try:
                server_disks = UCSCServer.list_disks(handle, i)
                disks[i['dn']] = []
                for d in server_disks:
                    # d.__dict__ flattens the object to a dictionary. 
                    kv = d.__dict__
                    kv = dict((key, value) for key, value in kv.iteritems() if not key.startswith('_') )
                    disks[i['dn']].append( kv)
            except KubamError as e:
                UCSUtil.ucs_logout(handle)
                return {"error": str(e)}, Const.HTTP_BAD_REQUEST
        
        out = UCSCUtil.dn_hash_to_out(disks)
        UCSCUtil.ucsc_logout(handle)
        return out, Const.HTTP_OK
        
    @staticmethod
    def delete_ucsm(handle, wanted):
        try:
            all_servers = UCSServer.list_servers(handle)
            ucs_servers = UCSUtil.servers_to_objects(all_servers, wanted)
        except KubamError as e:
            UCSUtil.ucs_logout(handle)
            return {"error": str(e)}, Const.HTTP_BAD_REQUEST
        return {"status":"ok"}, 201
        from ucsmsdk.mometa.storage.StorageLocalDisk import StorageLocalDisk
        for i in ucs_servers:
            try:
                UCSServer.reset_disks(handle, i)
            except KubamError as e: 
                UCSUtil.ucs_logout(handle)
                return {"error": str(e)}, Cont.HTTP_BAD_REQUEST
        return {"status" : "ok"}, 201
        

    @staticmethod
    def delete_ucsc(handle, wanted):
        """
        sets the JBOD disks to unconfigured good.
        """
        try:
            all_servers = UCSCServer.list_servers(handle)
            ucs_servers = UCSCUtil.servers_to_objects(all_servers, wanted)
        except KubamError as e:
            UCSCUtil.ucsc_logout(handle)
            return {"error": str(e)}, Const.HTTP_BAD_REQUEST
        from ucscsdk.mometa.storage.StorageLocalDisk import StorageLocalDisk
        for i in ucs_servers:
            try:
                UCSCServer.reset_disks(handle, i)
            except KubamError as e: 
                UCSCUtil.ucsc_logout(handle)
                return {"error": str(e)}, Cont.HTTP_BAD_REQUEST
        return {"status" : "ok"}, 201
        

@disks.route(Const.API_ROOT2 + "/servers/<server_group>/disks", methods=["GET", "DELETE"])
@cross_origin()
def disk_operation(server_group):
    """
    Figure out the operation and do it. 
    """
    wanted = "all"
    try: 
        db = YamlDB()
        sg = db.get_server_group(Const.KUBAM_CFG, server_group)
    except KubamError as e:
        return jsonify({"error": str(e)}), Const.HTTP_BAD_REQUEST


    if request.json and "servers" in request.json:
        wanted = request.json["servers"]

    ## login to UCS Manager and do the action. 
    if sg["type"] == "ucsm":
        try:
            handle = UCSUtil.ucs_login(sg)
        except KubamError as e:
            return jsonify({"error": str(e)}), Const.HTTP_UNAUTHORIZED

        if request.method == "DELETE":
            js, rc = Disks.delete_ucsm(handle,  wanted)
        js, rc = Disks.list_ucsm(handle, wanted)
        
        return jsonify(js), rc

    ## login to UCS Central and do the action
    elif sg["type"] == "ucsc":
        try:
            handle = UCSCUtil.ucsc_login(sg)
        except KubamError as e:
            return jsonify({"error": str(e)}), Const.HTTP_UNAUTHORIZED

        if request.method == "DELETE":
            js, rc = Disks.delete_ucsc(handle, wanted)
        js, rc =  Disks.list_ucsc(handle, wanted)
        return jsonify(js), rc

