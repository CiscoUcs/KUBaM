from flask import Flask, jsonify, request, abort
from network import UCSNet
from server import UCSServer
from session import UCSSession
from util import UCSUtil

app = Flask(__name__)


API_ROOT="/api/v1"

handle = ""

credentials = {
    'user': "",
    'password': "",
    'server': ""
}

@app.route('/')
def index():
    return jsonify({'status': 'ok'})


@app.route(API_ROOT + "/session", methods=['GET'])
def get_creds():
    c = credentials
    c["password"] = "REDACTED"
    return jsonify({'credentials': c})


# test with: curl -H "Content-Type: application/json" -X POST -d '{"credentials": {"user" : "admin", "password" : "cisco123", "server" : "172.28.225.163"}}' localhost:5000/api/v1/credentials}}

@app.route(API_ROOT + "/session", methods=['POST'])
def create_creds():
    global handle
    if not request.json:
        return jsonify({'error': 'expected credentials hash'}), 400
   
    print request.json['credentials'] 
    credentials['user'] = request.json['credentials']['user']
    credentials['password'] = request.json['credentials']['password']
    credentials['server'] = request.json['credentials']['server']
    h, err = UCSSession.login(credentials['user'], 
                              credentials['password'],
                              credentials['server'])
    print h
    if h == "":
        return jsonify({'error': err}), 401
    handle = h
    return jsonify({'login': "success"}), 201

@app.route(API_ROOT + "/session", methods=['DELETE'])
def delete_session():
    if handle != "":
        UCSSession.logout(handle)
    return jsonify({'logout': "success"})

def not_logged_in():
    return jsonify({'error': 'not logged in to UCS'}), 401
    
# get the networks in the UCS. 
@app.route(API_ROOT + "/networks", methods=['GET'])
def get_networks():
    global handle
    if handle == "":
        return not_logged_in() 
    vlans = UCSNet.listVLANs(handle) 
    return jsonify({'vlans': [{"name": vlan.name, "vlan-id": vlan.id}  for vlan in vlans]}), 200
    

@app.route(API_ROOT + "/servers", methods=['GET'])
def get_servers():
    global handle
    if handle == "":
        return not_logged_in() 
    servers = UCSServer.list_servers(handle) 
    return jsonify({'servers': servers}), 200

# deploy the UCS
@app.route(API_ROOT + "/deploy", methods=['POST'])
def deploy_ucs():
    return "ucs"    


if __name__ == '__main__':
    app.run(debug=True)


