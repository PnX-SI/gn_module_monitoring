"""
    module definissant les routes d'accès de modification des objects
        site, visit, observation, ...
"""

import datetime as dt

from werkzeug.exceptions import Forbidden

from flask import request, url_for, g, current_app

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from utils_flask_sqla.response import json_resp, json_resp_accept_empty_list
from utils_flask_sqla.response import to_csv_resp
from utils_flask_sqla_geo.generic import GenericQueryGeo

from geonature.core.gn_permissions import decorators as permissions
from geonature.core.gn_permissions.decorators import check_cruved_scope
from geonature.core.gn_commons.models.base import TModules
from geonature.core.gn_permissions.models import TObjects

from geonature.utils.env import DB, ROOT_DIR
import geonature.utils.filemanager as fm

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.monitoring.definitions import monitoring_definitions
from gn_module_monitoring.modules.repositories import get_module
from gn_module_monitoring.utils.utils import to_int
from gn_module_monitoring.config.repositories import get_config


@blueprint.before_request
def set_current_module():
    values = {**request.view_args, **request.args} if request.view_args else {**request.args}

    # recherche du sous-module courant
    requested_module_code = (
        values.get("module_code") or values.get("module_context") or MODULE_CODE
    )
    if requested_module_code == "generic":
        requested_module_code = "MONITORINGS"

    current_module = DB.first_or_404(
        statement=select(TModules)
        .options(joinedload(TModules.objects))
        .where(TModules.module_code == requested_module_code),
        description=f"No module with code {requested_module_code} ",
    )
    g.current_module = current_module

    # recherche de l'object de permission courant
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
            description=f"No permission object with code {requested_permission_object_code} ",
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

    config = get_config(module_code, force=True)

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

    config = get_config(module_code, force=True)
    return (
        monitoring_definitions.monitoring_object_instance(
            module_code, object_type, config=config, id=id
        )
        .create_or_update(post_data)
        .serialize(depth)
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
    config = get_config(module_code, force=True)

    depth = to_int(request.args.get("depth", 1))

    return (
        monitoring_definitions.monitoring_object_instance(
            module_code, object_type, config=config, id=id
        ).get(depth=depth)
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

        config = get_config(module_code, force=True)
        object = monitoring_definitions.monitoring_object_instance(
            module_code, object_type, config=config, id=id
        ).get(depth=depth)
        if not object._model.has_instance_permission(scope=scope):
            raise Forbidden(f"User {g.current_user} cannot update {object_type} {object._id}")

    post_data = dict(request.get_json())
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
    # get_config(module_code, force=True)
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

    # ??? PLUS VALABLE
    # NOTE: normalement on ne peut plus supprimer les groupes de site / sites par l'entrée protocoles
    # if object_type in ("site", "sites_group"):
    #     raise Exception(
    #         f"No right to delete {object_type} from protocol. The {object_type} with id: {id} could be linked with others protocols"
    #     )

    config = get_config(module_code=module_code, force=True)
    monitoring_obj = monitoring_definitions.monitoring_object_instance(
        module_code, object_type, config=config, id=id
    )
    if id != None:
        object = monitoring_obj.get(depth=depth)
        if not object._model.has_instance_permission(scope=scope):
            raise Forbidden(f"User {g.current_user} cannot delete {object_type} {object._id}")

    return monitoring_obj.delete()


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
    query_params = dict(**request.args)
    query_params["parents_path"] = request.args.getlist("parents_path")
    config = get_config(module_code=module_code, force=True)
    return (
        monitoring_definitions.monitoring_object_instance(
            module_code, object_type, config=config, id=id
        )
        .get()
        .breadcrumbs(query_params)
    )


# listes pour les formulaires par exemple
@blueprint.route("list/<string:module_code>/<object_type>", methods=["GET"])
@check_cruved_scope("R")
@json_resp_accept_empty_list
def list_object_api(module_code, object_type):
    config = get_config(module_code, force=True)

    return monitoring_definitions.monitoring_object_instance(
        module_code, object_type, config=config
    ).get_list(request.args)


# mise à jour de la synthèse
@blueprint.route("synthese/<string:module_code>", methods=["POST"])
@check_cruved_scope("U", object_code="MONITORINGS_MODULES")
@json_resp
def update_synthese_api(module_code):
    config = get_config(module_code, force=True)

    return (
        monitoring_definitions.monitoring_object_instance(module_code, "module", config=config)
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
    try:
        export = GenericQueryGeo(
            DB=DB,
            tableName=f"v_export_{module_code.lower()}_{method}",
            schemaName="gn_monitoring",
            filters=[],
            limit=50000,
            offset=0,
            geometry_field=None,
            srid=None,
        )
    except KeyError:
        return f"table v_export_{module_code.lower()}_{method} doesn't exist", 404

    model = export.get_model()
    columns = export.view.tableDef.columns
    schema = export.get_marshmallow_schema()

    q = select(model)
    #  Filter with dataset if is set
    if hasattr(model, "id_dataset") and id_dataset:
        q = q.where(getattr(model, "id_dataset") == id_dataset)

    data = DB.session.scalars(q).all()
    timestamp = dt.datetime.now().strftime("%Y_%m_%d_%Hh%Mm%S")
    filename = f"{module_code}_{method}_{timestamp}"
    return to_csv_resp(
        filename,
        data=schema().dump(data, many=True),
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
    config = get_config(module_code, force=True)
    monitoring_object = (
        monitoring_definitions.monitoring_object_instance(
            module_code, object_type, config=config, id=id
        )
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
