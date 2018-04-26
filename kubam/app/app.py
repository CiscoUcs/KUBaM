from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from deploy import deploy
from hosts import hosts
from monitor import monitor
from network import networks
from server import servers
from session import session
from config import Const
from ucs import UCSServer, UCSUtil
from iso import IsoMaker
from db import YamlDB
from autoinstall import Builder
from aci import aci

app = Flask(__name__)
app.register_blueprint(deploy)
app.register_blueprint(hosts)
app.register_blueprint(monitor)
app.register_blueprint(networks)
app.register_blueprint(servers)
app.register_blueprint(session)
CORS(app)

ucs_util = UCSUtil()


@app.route('/')
@cross_origin()
def index():
    """
    / basic test to see if site is up.
    should return { 'status' : 'ok'}
    """
    return jsonify({'status': 'ok'})


@app.route(Const.API_ROOT2 + "/aci", methods=['GET', 'POST', 'PUT', 'DELETE'])
@cross_origin()
def aci_handler():
    if request.method == 'POST':
        j, rc = aci.create(request.json)
    elif request.method == 'PUT':
        j, rc = aci.update(request.json)
    elif request.method == 'DELETE':
        j, rc = aci.delete(request.json)
    else:
        j, rc = aci.list()
    return jsonify(j), rc


# get the kubam ip address
@app.route(Const.API_ROOT + "/ip", methods=['GET'])
@cross_origin()
def get_kubam_ip():
    err, msg, ip = YamlDB.get_kubam_ip(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'kubam_ip': ip}), 200


# update the kubam IP address
@app.route(Const.API_ROOT + "/ip", methods=['POST'])
@cross_origin()
def update_kubam_ip():
    if not request.json:
        return jsonify({'error': 'expected request with kubam_ip '}), 400
    if "kubam_ip" not in request.json:
        return jsonify({'error': 'expected request with kubam_ip '}), 400

    ip = request.json['kubam_ip']
    err, msg = YamlDB.update_kubam_ip(Const.KUBAM_CFG, ip)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'kubam_ip': ip}), 201


# get the org
@app.route(Const.API_ROOT + "/org", methods=['GET'])
@cross_origin()
def get_org():
    err, msg, org = YamlDB.get_org(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'org': org}), 200


# update the org
@app.route(Const.API_ROOT + "/org", methods=['POST'])
@cross_origin()
def update_ucs_org():
    if not request.json:
        return jsonify({'error': 'expected request with org'}), 400
    if "org" not in request.json:
        return jsonify({'error': 'expected request with org'}), 400

    org = request.json['org']
    err, msg = YamlDB.update_org(Const.KUBAM_CFG, org)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'org': org}), 201


# get the proxy
@app.route(Const.API_ROOT + "/proxy", methods=['GET'])
@cross_origin()
def get_proxy():
    err, msg, keys = YamlDB.get_proxy(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'proxy': keys}), 200


# update proxy
@app.route(Const.API_ROOT + "/proxy", methods=['POST'])
@cross_origin()
def update_proxy():
    if not request.json:
        return jsonify({'error': 'expected request with proxy '}), 400
    if "proxy" not in request.json:
        return jsonify({'error': 'expected request with proxy'}), 400

    proxy = request.json['proxy']
    err, msg = YamlDB.update_proxy(Const.KUBAM_CFG, proxy)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'proxy': proxy}), 201


# get the public keys
@app.route(Const.API_ROOT + "/keys", methods=['GET'])
@cross_origin()
def get_public_keys():
    err, msg, keys = YamlDB.get_public_keys(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'keys': keys}), 200


# update public keys
@app.route(Const.API_ROOT + "/keys", methods=['POST'])
@cross_origin()
def update_public_keys():
    if not request.json:
        return jsonify({'error': 'expected request with keys '}), 400
    if "keys" not in request.json:
        return jsonify({'error': 'expected request with keys '}), 400

    keys = request.json['keys']
    err, msg = YamlDB.update_public_keys(Const.KUBAM_CFG, keys)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'keys': keys}), 201


# see if there are any selected servers in the database
def servers_to_api(ucs_servers, dbServers):
    for i, real_server in enumerate(ucs_servers):
        if real_server["type"] == "blade":
            if "blades" in dbServers:
                for b in dbServers["blades"]:
                    b_parts = b.split("/")
                    if (len(b_parts) == 2 and
                            real_server["chassis_id"] == b_parts[0] and
                            real_server["slot"] == b_parts[1]):
                        real_server["selected"] = True
                        ucs_servers[i] = real_server
        elif real_server["type"] == "rack":
            if "rack_servers" in dbServers:
                for s in dbServers["rack_servers"]:
                    if real_server["rack_id"] == s:
                        real_server["selected"] = True
                        ucs_servers[i] = real_server
    return ucs_servers


@app.route(Const.API_ROOT + "/servers", methods=['GET'])
@cross_origin()
def get_servers():
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        return UCSUtil.not_logged_in(msg)
    servers = UCSServer.list_servers(handle)
    UCSUtil.ucs_logout(handle)

    # gets a hash of severs of form:
    # {blades: ["1/1", "1/2",..], rack: ["6", "7"]}
    err, msg, dbServers = YamlDB.get_ucs_servers(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    servers = servers_to_api(servers, dbServers)
    # app.logger.info("returninng servers...")
    # app.logger.info(servers)
    err, msg, hosts = YamlDB.get_hosts(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'servers': servers, 'hosts': hosts}), 200


# translates the json we get from the web interface to what we expect to put in
# the database.
def servers_to_db(servers):
    # gets a server array list and gets the selected servers and
    # puts them in the database form
    server_pool = {}
    # app.logger.info(servers)
    for s in servers:
        if "selected" in s and s["selected"] == True:
            if s["type"] == "blade":
                if not "blades" in server_pool:
                    server_pool["blades"] = []
                b = "%s/%s" % (s["chassis_id"], s["slot"])
                server_pool["blades"].append(b)
            elif s["type"] == "rack":
                if not "rack_servers" in server_pool:
                    server_pool["rack_servers"] = []
                server_pool["rack_servers"].append(s["rack_id"])
    return server_pool


@app.route(Const.API_ROOT + "/servers", methods=['POST'])
@cross_origin()
def select_servers():
    # make sure we got some data.
    if not request.json:
        return jsonify({'error': 'expected hash of servers'}), 400
    # make sure we can login
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        return UCSUtil.not_logged_in(msg)
    servers = request.json['servers']
    # we expect servers to be a hash of like:
    # {blades: ["1/1", "1/2",..], rack: ["6", "7"]}
    servers = servers_to_db(servers)
    if servers:
        err, msg = YamlDB.update_ucs_servers(Const.KUBAM_CFG, servers)
        if err != 0:
            return jsonify({'error': msg}), 400
    if "hosts" not in request.json:
        return get_servers()

    hosts = request.json['hosts']
    err, msg = YamlDB.update_hosts(Const.KUBAM_CFG, hosts)
    if err != 0:
        return jsonify({'error': msg}), 400

    # return the existing networks now with the new one chosen.
    return get_servers()


# list ISO images.
@app.route(Const.API_ROOT + "/isos", methods=['GET'])
@cross_origin()
def get_isos():
    err, isos = IsoMaker.list_isos("/kubam")
    if err != 0:
        return jsonify({'error': isos})
    return jsonify({'isos': isos}), 200


# make the boot ISO image of an ISO
# curl -H "Content-Type: application/json" -X POST -d '{"iso" : "Vmware-ESXi-6.5.0-4564106-Custom-Cisco-6.5.0.2.iso" }' http://localhost/api/v1/isos/boot
# curl -H "Content-Type: application/json" -X POST -d '{"iso" : "CentOS-7-x86_64-Minimal-1611.iso" }' http://localhost/api/v1/isos/boot
@app.route(Const.API_ROOT + "/isos/boot", methods=['POST'])
@cross_origin()
def mkboot_iso():
    # get the iso map
    err, msg, isos = YamlDB.get_iso_map(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({"error": msg}), 400
    if len(isos) == 0:
        return jsonify({"error": "No ISOS have been mapped.  Please map an ISO image with an OS"}), 400
    err, msg = IsoMaker.mkboot_iso(isos)
    if err != 0:
        return jsonify({"error": msg}), 400

    err, msg = Builder.deploy_server_images(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({"error": msg}), 400
    return jsonify({"status": "ok"}), 201


# get the capabilities of KUBAM
@app.route(Const.API_ROOT + "/catalog", methods=['GET'])
@cross_origin()
def get_catalog():
    catalog = Builder.catalog
    app.logger.info(catalog)
    return jsonify(catalog), 200


# map the iso images to os versions.
@app.route(Const.API_ROOT + "/isos/map", methods=['GET'])
@cross_origin()
def get_iso_map():
    err, msg, isos = YamlDB.get_iso_map(Const.KUBAM_CFG)
    if err != 0:
        return jsonify({'error': msg}), 400
    return jsonify({'iso_map': isos}), 200


# update iso to os map
@app.route(Const.API_ROOT + "/isos/map", methods=['POST'])
@cross_origin()
def update_iso_map():
    app.logger.info("request.json")
    app.logger.info(request.json)
    if not request.json:
        return jsonify({'error': 'expected request with iso_map '}), 400
    if "iso_map" not in request.json:
        return jsonify({'error': 'expected request with iso_map '}), 400

    isos = request.json['iso_map']
    err, msg = YamlDB.update_iso_map(Const.KUBAM_CFG, isos)
    if err != 0:
        return jsonify({'error': msg}), 400
    return get_iso_map()


# Make the server images
@app.route(Const.API_ROOT + "/servers/images", methods=['POST'])
@cross_origin()
def deploy_server_autoinstall_images():
    err, msg = Builder.deploy_server_images(Const.KUBAM_CFG)
    if not err == 0:
        return jsonify({"error": msg})
    return jsonify({"status": "ok"}), 201


@app.route(Const.API_ROOT + "/settings", methods=['POST'])
@cross_origin()
def update_settings():
    app.logger.info(request.json)
    if not request.json:
        return jsonify({'error': 'expected kubam_ip and keys in json request'}), 400
    if not "kubam_ip" in request.json:
        return jsonify({'error': 'Please enter the IP address of the kubam server'}), 400
    if not "keys" in request.json:
        return jsonify({
                           'error': 'Please specify keys.  See documentation for how this should look: https://ciscoucs.github.io/kubam/docs/settings.'}), 400
    # proxy and org are not manditory.

    if "proxy" in request.json:
        proxy = request.json['proxy']
        err, msg = YamlDB.update_proxy(Const.KUBAM_CFG, proxy)
        if err != 0:
            return jsonify({'error': msg}), 400

    if "org" in request.json:
        org = request.json['org']
        err, msg = YamlDB.update_org(Const.KUBAM_CFG, org)
        if err != 0:
            return jsonify({'error': msg}), 400

    # update the kubam_IP if it is changed.
    ip = request.json['kubam_ip']
    err, msg = YamlDB.update_kubam_ip(Const.KUBAM_CFG, ip)
    if err != 0:
        return jsonify({'error': msg}), 400

    # update the keys if changed.
    keys = request.json['keys']
    app.logger.info(keys)
    err, msg = YamlDB.update_public_keys(Const.KUBAM_CFG, keys)
    if err != 0:
        return jsonify({'error': msg}), 400

    return jsonify({"status": "ok"}), 201


if __name__ == '__main__':
    app.run(debug=True)

