from session import UCSSession
from db import YamlDB

KUBAM_CFG="/kubam/kubam.yaml"

# list the server group information
def list():
    """
    / basic test to see if site is up.
    should return { 'status' : 'ok'}
    """
    err, msg, sg = YamlDB.list_aci(KUBAM_CFG)
    if err == 1:
        return ({'error': msg}, 500)
    return { "aci" : sg} , 200

def check_login(request):
    if not 'credentials' in request:
        return {'error' : "no credentials found in request"}, 400
    for v in ['user', 'password', 'ip']:
        if not v in request['credentials']:
            return {'error' : "credentials should include %s" % v}, 400 
    user = request['credentials']['user']
    pw = request['credentials']['password']
    ip = request['credentials']['ip']
    if ip == "":
        return {'error': "Please enter a valid ACI IP address."}, 400
    # TODO: implement ACI apis to log in and configure
    #h, err = UCSSession.login(user, pw, ip)
    #if h == "":
    #    return {'error': err}, 400
    #UCSSession.logout(h)
    return "", 200
    
# create a new server group
def create(request):
    """
    Create a new ACI entry
    Format of request should be JSON that looks like:
    {"name", "aci01", "credentials" : {"user": "admin", "password" : "secret-password", "ip" : "172.28.225.163" }, ...}
    """
    # make sure we can log in first. 
    msg, code = check_login(request)
    if code == 400:
        return msg, code
    err, msg = YamlDB.new_aci(KUBAM_CFG, request)
    if err == 1:
        return {'error': msg}, 400
    return {'status': "new ACI group %s created!" % request["name"]}, 201

def update(request):
    """
    Update an ACI group
    """
    msg, code = check_login(request)
    if code == 400:
        return msg, code
    err, msg = YamlDB.update_aci(KUBAM_CFG, request)
    if err == 1:
        return {'error': msg}, 400
    return {'status': "ACI group %s updated!" % request["name"]}, 201
      
def delete(request):
    """
    Delete the ACI group from the config.
    """
    uuid = request['id']
    err, msg = YamlDB.delete_aci(KUBAM_CFG, uuid)
    if err == 1:
        return {'error': msg}, 400
    else:
        return {'status': "ACI group deleted"}, 201
    
