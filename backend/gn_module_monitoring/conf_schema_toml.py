"""
Spécification du schéma toml des paramètres de configurations
Fichier spécifiant les types des paramètres et leurs valeurs par défaut
Fichier à ne pas modifier. Paramètres surcouchables dans config/config_gn_module.tml
"""

from marshmallow import Schema, fields


# Permissions associés à chaque objet monitoring
PERMISSION_LEVEL_DEFAULT = {
    "module": "MONITORINGS_MODULES",
    "site": "MONITORINGS_SITES",
    "sites_group": "MONITORINGS_GRP_SITES",
    "visit": "MONITORINGS_VISITES",
    "observation": "MONITORINGS_VISITES",
    "observation_detail": "MONITORINGS_VISITES",
    "individual": "MONITORINGS_INDIVIDUALS",
    "marking": "MONITORINGS_MARKINGS",
}


class GnModuleSchemaConf(Schema):
    DESCRIPTION_MODULE = fields.String(load_default="")
    TITLE_MODULE = fields.String(load_default="Module monitoring")
    CODE_OBSERVERS_LIST = fields.String(load_default="obsocctax")

    PERMISSION_LEVEL = fields.Dict(
        keys=fields.Str(), values=fields.Str(), load_default=PERMISSION_LEVEL_DEFAULT
    )

    ENABLE_LEAFLET_CLUSTER = fields.Boolean(load_default=False)


#     AREA_TYPE = fields.List(fields.String(), missing=["COM", "M1", "M5", "M10"])
#     BORNE_OBS = fields.List(fields.Integer(), missing=[1, 20, 40, 60, 80, 100, 120])
#     BORNE_TAXON = fields.List(fields.Integer(), missing=[1, 5, 10, 15])
#     SIMPLIFY_LEVEL = fields.Integer(missing=50)
