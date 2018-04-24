from session import UCSSession
from db import YamlDB

KUBAM_CFG="/kubam/kubam.yaml"

# list the server group information
def list():
    """
    / basic test to see if site is up.
    should return { 'status' : 'ok'}
    """
    err, msg, hosts = YamlDB.list_hosts(KUBAM_CFG)
    if err == 1:
        return ({'error': msg}, 500)
    return (hosts, 200)


# create a new server group
def create(request):
    """
    Create a new host entry
    Format of request should be JSON that looks like:
    {"name", "aci01", "credentials" : {"user": "admin", "password" : "secret-password", "ip" : "172.28.225.163" }, ...}
    """
    err, msg = YamlDB.new_hosts(KUBAM_CFG, request)
    if err == 1:
        return {'error': msg}, 400
    return {'status': "Hosts %s created!" % request["name"]}, 201
      
def delete(request):
    """
    Delete the ACI group from the config.
    """
    uuid = request['id']
    err, msg = YamlDB.delete_hosts(KUBAM_CFG, uuid)
    if err == 1:
        return {'error': msg}, 400
    else:
        return {'status': "Hosts deleted"}, 201
    
