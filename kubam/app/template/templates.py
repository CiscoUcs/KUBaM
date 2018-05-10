from flask import Blueprint, jsonify, current_app
from flask_cors import cross_origin
from ucs import UCSTemplate, UCSUtil
from config import Const
from util import KubamError

templates = Blueprint("templates", __name__)


@templates.route(Const.API_ROOT2 + "/templates", methods=['GET'])
@cross_origin()
def get_templates():
    err, msg, handle = UCSUtil.ucs_login()
    if err != 0:
        msg = UCSUtil.not_logged_in(msg)
        current_app.logger.warning(msg)
        return jsonify({'error': msg}), Const.HTTP_UNAUTHORIZED
    try:
        ucs_templates = UCSTemplate.list_templates(handle)
        UCSUtil.ucs_logout(handle)
        return jsonify({'templates': ucs_templates}), Const.HTTP_OK
    except KubamError as e:
        return jsonify({'error': e}), Const.HTTP_SERVER_ERROR
