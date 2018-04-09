from session import UCSSession
from db import YamlDB

KUBAM_CFG="/kubam/kubam.yaml"

# list the server group information
def list():
    """
    / basic test to see if site is up.
    should return { 'status' : 'ok'}
    """
    return ({'status': 'ok'}, 200)

# create a new server group
def create(request):
    """
    Create a new UCS Domain
    Format of request should be JSON that looks like:
    {"name", "ucs01", "type" : "ucsm", "credentials" : {"user": "admin", "password" : "secret-password", "ip" : "172.28.225.163" }}
    """
    # make sure we can log in first. 
    credentials = {}
    credentials['user'] = request['credentials']['user']
    credentials['password'] = request['credentials']['password']
    credentials['ip'] = request['credentials']['ip']
    if credentials['ip'] == "":
        return {'error': "Please enter a valid UCSM IP address."}, 401
    h, err = UCSSession.login(credentials['user'],
                              credentials['password'],
                              credentials['ip'])
    if h == "":
        return {'error': err}, 401
    UCSSession.logout(h)

    # test that the name doesn't already exist (has to be unique names)
     
    # make sure type is specified. 
    
    # write datafile.
    err, msg = YamlDB.new_server_group(KUBAM_CFG, credentials)
    if err != "":
        return {'error': msg}, 401
    
    return {'status': "new server group created!"}, 201
