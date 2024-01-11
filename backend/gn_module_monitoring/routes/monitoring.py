"""
    module definissant les routes d'accès de modification des objects
        site, visit, observation, ...
"""


from pathlib import Path
from werkzeug.exceptions import NotFound, Forbidden
from flask import request, send_from_directory, url_for, g, current_app
import datetime as dt

from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import select

from utils_flask_sqla.response import json_resp, json_resp_accept_empty_list
from utils_flask_sqla.response import to_csv_resp, to_json_resp
from utils_flask_sqla_geo.generic import GenericTableGeo
from utils_flask_sqla.generic import serializeQuery


from ..blueprint import blueprint
from geonature.core.gn_permissions import decorators as permissions
from geonature.core.gn_permissions.decorators import check_cruved_scope
from geonature.core.gn_commons.models.base import TModules
from geonature.core.gn_permissions.models import TObjects, Permission

from geonature.utils.env import DB, ROOT_DIR
import geonature.utils.filemanager as fm

from gn_module_monitoring import MODULE_CODE
from ..monitoring.definitions import monitoring_definitions
from ..modules.repositories import get_module
from ..utils.utils import to_int
from ..config.repositories import get_config, get_config_with_specific
from gn_module_monitoring.utils.routes import (
    query_all_types_site_from_site_id,
)


@blueprint.url_value_preprocessor
def set_current_module(endpoint, values):
    # recherche du sous-module courrant
    requested_module_code = values.get("module_code") or MODULE_CODE
    current_module = DB.first_or_404(
        statement=select(TModules)
        .options(joinedload(TModules.objects))
        .where(TModules.module_code == requested_module_code),
        description=f"No module with code {requested_module_code} {endpoint}",
    )
    g.current_module = current_module

    # recherche de l'object de permission courrant
    object_type = values.get("object_type")

    if object_type:
        permission_level = current_app.config["MONITORINGS"].get("PERMISSION_LEVEL", {})
        requested_permission_object_code = permission_level.get(object_type)

        if requested_permission_object_code is None:
            # error ?
            return

        # Test si l'object de permission existe
        requested_permission_object = DB.first_or_404(
            statement=select(TObjects).where(
                TObjects.code_object == requested_permission_object_code
            ),
            description=f"No permission object with code {requested_permission_object_code} {endpoint}",
        )

        # si l'object de permission est associé au module => il devient l'objet courant
        # - sinon se sera 'ALL' par defaut
        for module_perm_object in current_module.objects:
            if module_perm_object == requested_permission_object:
                g.current_object = requested_permission_object
                return


@blueprint.route("/object/<string:module_code>/<string:object_type>/<int:id>", methods=["GET"])
@blueprint.route("/object/<string:module_code>/<string:object_type>", methods=["GET"])
@blueprint.route(
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
    if id != None:
        object = monitoring_definitions.monitoring_object_instance(
            module_code, object_type, id
        ).get(depth=depth)
        if not object._model.has_instance_permission(scope=scope):
            raise Forbidden(f"User {g.current_user} cannot read {object_type} {object._id}")

    if id != None and object_type == "site":
        types_site_obj = query_all_types_site_from_site_id(id)
        list_types_sites_dict = [
            values
            for res in types_site_obj
            for (key_type_site, values) in res.as_dict().items()
            if key_type_site == "config"
        ]
        customConfig = {"specific": {}}
        for specific_config in list_types_sites_dict:
            customConfig["specific"].update((specific_config or {}).get("specific", {}))

        get_config(module_code, force=True, customSpecConfig=customConfig)
    else:
        get_config(module_code, force=True)

    return (
        monitoring_definitions.monitoring_object_instance(module_code, object_type, id).get(
            depth=depth
        )
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

    if module_code != "generic":
        module = get_module("module_code", module_code)
    else:
        module = {"id_module": "generic"}

    # on rajoute id_module s'il n'est pas renseigné par défaut ??
    if "id_module" not in post_data["properties"]:
        post_data["properties"]["id_module"] = "generic"
    else:
        post_data["properties"]["id_module"] = module.id_module

    return (
        monitoring_definitions.monitoring_object_instance(module_code, object_type, id)
        .create_or_update(post_data)
        .serialize(depth)
    )


def get_config_object(module_code, object_type, id):
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
    get_config(module_code, force=True)

    depth = to_int(request.args.get("depth", 1))

    return (
        monitoring_definitions.monitoring_object_instance(module_code, object_type, id).get(
            depth=depth
        )
        # .get(value=value, field_name = field_name)
        .serialize(depth)
    )


# update object
@blueprint.route("object/<string:module_code>/<object_type>/<int:id>", methods=["PATCH"])
@blueprint.route(
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
        object = monitoring_definitions.monitoring_object_instance(
            module_code, object_type, id
        ).get(depth=depth)
        if not object._model.has_instance_permission(scope=scope):
            raise Forbidden(f"User {g.current_user} cannot update {object_type} {object._id}")

    post_data = dict(request.get_json())
    if "dataComplement" in post_data:
        get_config_with_specific(module_code, force=True, complements=post_data["dataComplement"])
    else:
        get_config(module_code, force=True)
    return create_or_update_object_api(module_code, object_type, id)


# create object
@blueprint.route(
    "object/<string:module_code>/<object_type>", defaults={"id": None}, methods=["POST"]
)
@blueprint.route(
    "/object/module",
    defaults={"module_code": None, "object_type": "module", "id": None},
    methods=["POST"],
)
@check_cruved_scope("C")
@json_resp
def create_object_api(module_code, object_type, id):
    post_data = dict(request.get_json())
    if "dataComplement" in post_data:
        get_config_with_specific(module_code, force=True, complements=post_data["dataComplement"])
    else:
        get_config(module_code, force=True)
    return create_or_update_object_api(module_code, object_type, id)


# delete
@blueprint.route("object/<string:module_code>/<object_type>/<int:id>", methods=["DELETE"])
@blueprint.route(
    "/object/<string:module_code>/module",
    defaults={"id": None, "object_type": "module"},
    methods=["DELETE"],
)
@check_cruved_scope("D")
@json_resp
@permissions.check_cruved_scope("D", get_scope=True)
def delete_object_api(scope, module_code, object_type, id):
    depth = to_int(request.args.get("depth", 1))
    if id != None:
        object = monitoring_definitions.monitoring_object_instance(
            module_code, object_type, id
        ).get(depth=depth)
        if not object._model.has_instance_permission(scope=scope):
            raise Forbidden(f"User {g.current_user} cannot delete {object_type} {object._id}")

    if object_type in ("site", "sites_group"):
        raise Exception(
            f"No right to delete {object_type} from protocol. The {object_type} with id: {id} could be linked with others protocols"
        )
    get_config(module_code, force=True)
    # NOTE: normalement on ne peut plus supprimer les groupes de site / sites par l'entrée protocoles
    return monitoring_definitions.monitoring_object_instance(module_code, object_type, id).delete()


# breadcrumbs
@blueprint.route("breadcrumbs/<string:module_code>/<object_type>/<int:id>", methods=["GET"])
@blueprint.route(
    "breadcrumbs/<string:module_code>/<object_type>", defaults={"id": None}, methods=["GET"]
)
@blueprint.route(
    "/breadcrumbs/<string:module_code>/module",
    defaults={"id": None, "object_type": "module"},
    methods=["GET"],
)
@check_cruved_scope("R")
@json_resp
def breadcrumbs_object_api(module_code, object_type, id):
    get_config(module_code, force=True)
    query_params = dict(**request.args)
    query_params["parents_path"] = request.args.getlist("parents_path")
    return (
        monitoring_definitions.monitoring_object_instance(module_code, object_type, id)
        .get()
        .breadcrumbs(query_params)
    )


# listes pour les formulaires par exemple
@blueprint.route("list/<string:module_code>/<object_type>", methods=["GET"])
@check_cruved_scope("R")
@json_resp_accept_empty_list
def list_object_api(module_code, object_type):
    get_config(module_code, force=True)

    return monitoring_definitions.monitoring_object_instance(module_code, object_type).get_list(
        request.args
    )


# mise à jour de la synthèse
@blueprint.route("synthese/<string:module_code>", methods=["POST"])
@check_cruved_scope("U", object_code="MONITORINGS_MODULES")
@json_resp
def update_synthese_api(module_code):
    get_config(module_code, force=True)

    return (
        monitoring_definitions.monitoring_object_instance(module_code, "module")
        .get()
        .process_synthese(process_module=True)
    )


# export add mje
# export all observations
@blueprint.route("/exports/csv/<module_code>/<method>", methods=["GET"])
@check_cruved_scope("E", object_code="MONITORINGS_MODULES")
def export_all_observations(module_code, method):
    """
    Export all data in csv of a custom module view


    :params module_code: Code of the module
    :type module_code: str
    :param method: Name of the view without module code prefix
    :type method: str

    :returns: Array of dict
    """
    id_dataset = request.args.get("id_dataset", None, int)

    view = GenericTableGeo(
        tableName=f"v_export_{module_code.lower()}_{method}",
        schemaName="gn_monitoring",
        engine=DB.engine,
    )
    columns = view.tableDef.columns
    q = DB.session.query(*columns)
    # Filter with dataset if is set
    if hasattr(columns, "id_dataset") and id_dataset:
        q = q.filter(columns.id_dataset == id_dataset)
    data = q.all()

    timestamp = dt.datetime.now().strftime("%Y_%m_%d_%Hh%Mm%S")
    filename = f"{module_code}_{method}_{timestamp}"

    return to_csv_resp(
        filename,
        data=serializeQuery(data, q.column_descriptions),
        separator=";",
        columns=[
            db_col.key for db_col in columns if db_col.key != "geom"
        ],  # Exclude the geom column from CSV
    )


@blueprint.route("/exports/pdf/<module_code>/<object_type>/<int:id>", methods=["POST"])
@check_cruved_scope("E", object_code="MONITORINGS_MODULES")
def post_export_pdf(module_code, object_type, id):
    """
    Export the fiche individu as a PDF file.
    Need to push the map image in the post data to be present in PDF.
    Need to set a template in sub-module.
    """

    depth = to_int(request.args.get("depth", 0))
    monitoring_object = (
        monitoring_definitions.monitoring_object_instance(module_code, object_type, id)
        .get()
        .serialize(depth)
    )

    df = {
        "module_code": module_code,
        "monitoring_object": monitoring_object,
        "extra_data": request.json["extra_data"],
        "static_pdf_dir": url_for("media", filename=f"monitorings/{module_code}/exports/pdf/"),
        "map_image": request.json["map"],
    }

    template = request.json["template"]

    pdf_file = fm.generate_pdf(
        f"{module_code}/exports/pdf/{template}",
        df,
        # "map_area.pdf"
    )
    return current_app.response_class(pdf_file, content_type="application/pdf")
