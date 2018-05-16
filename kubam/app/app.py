from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
from aci import aci
from deploy import deploy
from host import hosts
from iso import isos
from monitor import monitor
from network import networks
from server import servers
from setting import setting

app = Flask(__name__)
app.register_blueprint(aci)
app.register_blueprint(deploy)
app.register_blueprint(hosts)
app.register_blueprint(isos)
app.register_blueprint(monitor)
app.register_blueprint(networks)
app.register_blueprint(servers)
app.register_blueprint(setting)
CORS(app)


@app.route('/')
@cross_origin()
def index():
    """
    Basic test to see if site is up.
    Should return { 'status' : 'ok'}
    """
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True)
