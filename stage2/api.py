from flask import Flask, jsonify, request, abort
from network import UCSNet
from server import UCSServer
from session import UCSSession
from util import UCSUtil

app = Flask(__name__)


API_ROOT="/api/v1"

credentials = {
    'user': "",
    'password': "",
    'server': ""
}

@app.route('/')
def index():
    return '<h1>KUBaM is Up!</h1>'


@app.route(API_ROOT + "/credentials", methods=['GET'])
def get_creds():
    c = credentials
    c["password"] = "REDACTED"
    return jsonify({'credentials': c})


# test with: curl -H "Content-Type: application/json" -X POST -d '{"credentials": {"user" : "admin", "password" : "cisco123", "server" : "172.28.225.163"}}' localhost:5000/api/v1/credentials}}

@app.route(API_ROOT + "/credentials", methods=['POST'])
def create_creds():
    if not request.json:
        return jsonify({'error': 'expected credentials hash'}), 400
    
    credentials['user'] = request.json['credentials']['user']
    credentials['password'] = request.json['credentials']['password']
    credentials['server'] = request.json['credentials']['server']
    return jsonify({'credentials': credentials}), 201
    
# get the networks in the UCS. 
@app.route(API_ROOT + "/networks", methods=['GET'])
def get_networks():
    handle = UCSSession.login(credentials['user'], 
                              credentials['password'],
                              credentials['server'])
    if handle == "":
        return jsonify({'error': "Error with UCS connection."})
    vlans = UCSNet.listVLANs(handle) 
    UCSSession.logout(handle)
    print vlans
    return "vlans", 200
    

@app.route(API_ROOT + "/servers", methods=['GET'])
def get_servers():
    return "ucs"    

# deploy the UCS
@app.route(API_ROOT + "/deploy", methods=['POST'])
def deploy_ucs():
    return "ucs"    


if __name__ == '__main__':
    app.run(debug=True)


