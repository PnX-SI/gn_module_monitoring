import datetime as dt

from flask import request, url_for, g, current_app

from sqlalchemy import select
from sqlalchemy.exc import NoSuchTableError

from utils_flask_sqla.response import json_resp, json_resp_accept_empty_list
from utils_flask_sqla.response import to_csv_resp
from utils_flask_sqla_geo.generic import GenericQueryGeo

from geonature.core.gn_permissions.decorators import check_cruved_scope

from geonature.utils.env import DB
import geonature.utils.filemanager as fm

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.routes.legacy import blueprint_legacy
from gn_module_monitoring.monitoring.definitions import monitoring_definitions
from gn_module_monitoring.utils.utils import to_int
from gn_module_monitoring.config.repositories import get_config_old

# Legacy routes for backward compatibility with old modules
blueprint.register_blueprint(blueprint_legacy)


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

    config = get_config_old(module_code=module_code, force=True)
    # PATCH si module_code == "MONITORINGS" et object_type == "module"
    #  alors réponse en dur car le module monitoring n'est pas de type TModuleMonitoring
    if g.current_module.module_code.upper() == "MONITORINGS" and object_type == "module":
        return [
            {
                "description": "Monitoring",
                "id": g.current_module.id_module,
                "label": "Module",
                "module_code": "generic",
                "object_type": "module",
            }
        ]

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
    config = get_config_old(module_code, force=True)

    return monitoring_definitions.monitoring_object_instance(
        module_code, object_type, config=config
    ).get_list(request.args)


# mise à jour de la synthèse
@blueprint.route("synthese/<string:module_code>", methods=["POST"])
@check_cruved_scope("U", object_code="MONITORINGS_MODULES")
@json_resp
def update_synthese_api(module_code):
    config = get_config_old(module_code, force=True)

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
    except (KeyError, NoSuchTableError):
        return f"table v_export_{module_code.lower()}_{method} doesn't exist", 404

    model = export.get_model()
    columns = export.view.tableDef.columns
    schema = export.get_marshmallow_schema()

    q = select(export.view.tableDef)
    #  Filter with dataset if is set
    if hasattr(model, "id_dataset") and id_dataset:
        q = q.where(getattr(model, "id_dataset") == id_dataset)

    data = DB.session.execute(q).all()
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
    config = get_config_old(module_code, force=True)
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
