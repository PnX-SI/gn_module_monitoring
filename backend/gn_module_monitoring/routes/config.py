from flask import request

from utils_flask_sqla.response import json_resp

from ..blueprint import blueprint
from ..config.repositories import (
    get_config,
    get_config_frontend
)
# from ..decorators import check_cruved_scope_monitoring


@blueprint.route('/config/<string:module_code>', methods=['GET'])
@blueprint.route('/config', defaults={'module_code': None}, methods=['GET'])
# @check_cruved_scop e_monitoring('R', 1)
@json_resp
def get_config_api(module_code):
    """
        route qui renvoie la config pour un module donné
    """

    return get_config_frontend(module_code, force=True)


