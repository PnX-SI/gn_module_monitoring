from werkzeug.exceptions import Forbidden

from flask import request, g, current_app, Blueprint
from sqlalchemy import update
from utils_flask_sqla.response import json_resp

from geonature.core.gn_permissions import decorators as permissions
from geonature.core.gn_permissions.decorators import check_cruved_scope
from geonature.core.imports.models import Destination
from geonature.utils.env import DB

from gn_module_monitoring.monitoring.definitions import monitoring_definitions
from gn_module_monitoring.modules.repositories import get_module
from gn_module_monitoring.utils.utils import to_int
from gn_module_monitoring.config.repositories import get_config_old

blueprint_legacy = Blueprint(
    "legacy", __name__, template_folder=current_app.config["MEDIA_FOLDER"] + "/monitorings"
)


def get_serialized_object(module_code, object_type, id):
    """
    renvoie un object, à partir de type de l'object et de son id

    :param module_code: reference le module concerne
    :param object_type: le type d'object (site, visit, obervation)
    :param id : l'identifiant de l'object (de id_base_site pour site)
    :type module_code: str
    :type object_type: str
    :type id: int

    :return: renvoie l'object requis
    :rtype: dict
    """

    # field_name = param.get('field_name')
    # value = module_code if object_type == 'module'
    config = get_config_old(module_code, force=True)

    depth = to_int(request.args.get("depth", 1))

    return (
        monitoring_definitions.monitoring_object_instance(
            module_code, object_type, config=config, id=id
        ).get(depth=depth)
        # .get(value=value, field_name = field_name)
        .serialize(depth)
    )


@blueprint_legacy.after_request
def legacy_warning(response):
    message = f"[MONITORING] Legacy route used : {request.endpoint}. Please update your code to use the new routes."
    current_app.logger.warning(message)
    response.headers["Deprecation"] = True
    return response


@blueprint_legacy.route(
    "/object/<string:module_code>/<string:object_type>/<int:id>", methods=["GET"]
)
@blueprint_legacy.route("/object/<string:module_code>/<string:object_type>", methods=["GET"])
@blueprint_legacy.route(
    "/object/module",
    methods=["GET"],
)
@check_cruved_scope("R")
@json_resp
@permissions.check_cruved_scope("R", get_scope=True)
def get_monitoring_object_api(scope, module_code=None, object_type="module", id=None):
    """
    renvoie un object, à partir de type de l'object et de son id

    :param module_code: reference le module concerne
    :param object_type: le type d'object (site, visit, obervation)
    :param id : l'identifiant de l'object (de id_base_site pour site)
    :type module_code: str
    :type object_type: str
    :type id: int

    :return: renvoie l'object requis
    :rtype: dict
    """

    # field_name = param.get('field_name')
    # value = module_code if object_type == 'module'

    depth = to_int(request.args.get("depth", 1))

    config = get_config_old(module_code, force=True)

    monitoring_obj = monitoring_definitions.monitoring_object_instance(
        module_code, object_type, config=config, id=id
    )
    if id != None:
        object = monitoring_obj.get(depth=depth)
        if not object._model.has_instance_permission(scope=scope):
            raise Forbidden(f"User {g.current_user} cannot read {object_type} {object._id}")

    return (
        monitoring_obj.get(depth=depth)
        # .get(value=value, field_name = field_name)
        .serialize(depth)
    )


def create_or_update_object_api(module_code, object_type, id=None):
    """
    route pour la création ou la modification d'un objet
    si id est renseigné, c'est une création (PATCH)
    sinon c'est une modification (POST)

    :param module_code: reference le module concerne
    :param object_type: le type d'object (site, visit, obervation)
    :param id : l'identifiant de l'object (de id_base_site pour site)
    :type module_code: str
    :type object_type: str
    :type id: int
    :return: renvoie l'object crée ou modifié
    :rtype: dict
    """
    depth = to_int(request.args.get("depth", 1))

    # recupération des données post
    post_data = dict(request.get_json())

    # on rajoute id_module s'il n'est pas renseigné par défaut
    post_data["properties"].setdefault("id_module", None)
    if not post_data["properties"]["id_module"]:
        if module_code != "generic":
            post_data["properties"]["id_module"] = get_module("module_code", module_code).id_module
        else:
            post_data["properties"]["id_module"] = "generic"
    if object_type == "module":
        query = update(Destination).where(Destination.code == module_code).values(active=True)
        DB.session.execute(query)

    config = get_config_old(module_code, force=True)
    return (
        monitoring_definitions.monitoring_object_instance(
            module_code, object_type, config=config, id=id
        )
        .create_or_update(post_data)
        .serialize(depth)
    )


# update object
@blueprint_legacy.route("/object/<string:module_code>/<object_type>/<int:id>", methods=["PATCH"])
@blueprint_legacy.route(
    "/object/<string:module_code>/module",
    defaults={"id": None, "object_type": "module"},
    methods=["PATCH"],
)
@check_cruved_scope("U")
@json_resp
@permissions.check_cruved_scope("U", get_scope=True)
def update_object_api(scope, module_code, object_type, id):
    depth = to_int(request.args.get("depth", 1))
    if id != None:

        config = get_config_old(module_code, force=True)
        object = monitoring_definitions.monitoring_object_instance(
            module_code, object_type, config=config, id=id
        ).get(depth=depth)
        if not object._model.has_instance_permission(scope=scope):
            raise Forbidden(f"User {g.current_user} cannot update {object_type} {object._id}")

    post_data = dict(request.get_json())
    return create_or_update_object_api(module_code, object_type, id)


# create object
@blueprint_legacy.route(
    "/object/<string:module_code>/<object_type>", defaults={"id": None}, methods=["POST"]
)
@blueprint_legacy.route(
    "/object/module",
    defaults={"module_code": None, "object_type": "module", "id": None},
    methods=["POST"],
)
@check_cruved_scope("C")
@json_resp
def create_object_api(module_code, object_type, id):
    post_data = dict(request.get_json())
    # get_config(module_code, force=True)
    return create_or_update_object_api(module_code, object_type, id)


# delete
@blueprint_legacy.route("/object/<string:module_code>/<object_type>/<int:id>", methods=["DELETE"])
@blueprint_legacy.route(
    "/object/<string:module_code>/module",
    defaults={"id": None, "object_type": "module"},
    methods=["DELETE"],
)
@check_cruved_scope("D")
@json_resp
@permissions.check_cruved_scope("D", get_scope=True)
def delete_object_api(scope, module_code, object_type, id):
    depth = to_int(request.args.get("depth", 1))

    # ??? PLUS VALABLE
    # NOTE: normalement on ne peut plus supprimer les groupes de site / sites par l'entrée protocoles
    # if object_type in ("site", "sites_group"):
    #     raise Exception(
    #         f"No right to delete {object_type} from protocol. The {object_type} with id: {id} could be linked with others protocols"
    #     )

    config = get_config_old(module_code=module_code, force=True)
    monitoring_obj = monitoring_definitions.monitoring_object_instance(
        module_code, object_type, config=config, id=id
    )
    if id != None:
        object = monitoring_obj.get(depth=depth)
        if not object._model.has_instance_permission(scope=scope):
            raise Forbidden(f"User {g.current_user} cannot delete {object_type} {object._id}")

    return monitoring_obj.delete()


@blueprint_legacy.route("/sites/config", methods=["GET"])
def get_config_sites(id=None, module_code="generic", object_type="site"):
    obj = get_serialized_object(module_code, object_type, id)
    return obj["properties"]


@blueprint_legacy.route("/sites_groups/config", methods=["GET"])
def get_config_sites_groups(id=None, module_code="generic", object_type="sites_group"):
    obj = get_serialized_object(module_code, object_type, id)
    return obj["properties"]
