from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from config import Const
from sg import sg

servers = Blueprint("servers", __name__)


@servers.route(Const.API_ROOT2 + "/servers", methods=['GET', 'POST', 'PUT', 'DELETE'])
@cross_origin()
def server_handler():
    if request.method == 'POST':
        j, rc = sg.create(request.json)
    elif request.method == 'PUT':
        j, rc = sg.update(request.json)
    elif request.method == 'DELETE':
        j, rc = sg.delete(request.json)
    else:
        j, rc = sg.list()
    return jsonify(j), rc
