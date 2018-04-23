from session import UCSSession
from db import YamlDB

KUBAM_CFG="/kubam/kubam.yaml"

# list the server group information
def list():
    """
    / basic test to see if site is up.
    should return { 'status' : 'ok'}
    """
    err, msg, sg = YamlDB.list_server_group(KUBAM_CFG)
    if err == 1:
        return ({'error': msg}, 500)
    return (sg, 200)

def check_login(request):
    if not isinstance(request, dict):
        return {'error' : "improper request sent"}, 401
    if not 'credentials' in request:
        return {'error' : "no credentials found in request"}, 401
    for v in ['user', 'password', 'ip']:
        if not v in request['credentials']:
            return {'error' : "credentials should include %s" % v}, 401
    user = request['credentials']['user']
    pw = request['credentials']['password']
    ip = request['credentials']['ip']
    if ip == "":
        return {'error': "Please enter a valid UCSM IP address."}, 401
    h, err = UCSSession.login(user, pw, ip)
    if h == "":
        return {'error': err}, 401
    UCSSession.logout(h)
    return "", 200
    
# create a new server group
def create(request):
    """
    Create a new UCS Domain
    Format of request should be JSON that looks like:
    {"name", "ucs01", "type" : "ucsm", "credentials" : {"user": "admin", "password" : "secret-password", "ip" : "172.28.225.163" }}
    """
    # make sure we can log in first. 
  
    msg, code = check_login(request)
    if code == 401:
        return msg, code
    err, msg = YamlDB.new_server_group(KUBAM_CFG, request)
    if err == 1:
        return {'error': msg}, 401
    return {'status': "new server group %s created!" % request["name"]}, 201

def update(request):
    """
    Update a server group
    """
    msg, code = check_login(request)
    if code == 401:
        return msg, code
    err, msg = YamlDB.update_server_group(KUBAM_CFG, request)
    if err == 1:
        return {'error': msg}, 401
    return {'status': "server group %s updated!" % request["name"]}, 201
      
def delete(request):
    """
    Delete the UCS server group or CIMC from the config.
    """
    uuid = request['id']
    err, msg = YamlDB.delete_server_group(KUBAM_CFG, uuid)
    if err == 1:
        return {'error': msg}, 401
    else:
        return {'status': "server group deleted"}, 201
    
