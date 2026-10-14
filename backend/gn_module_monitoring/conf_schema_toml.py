"""
Spécification du schéma toml des paramètres de configurations
Fichier spécifiant les types des paramètres et leurs valeurs par défaut
Fichier à ne pas modifier. Paramètres surcouchables dans config/config_gn_module.tml
"""

from warnings import warn

from marshmallow import Schema, fields, pre_load


class GnModuleSchemaConf(Schema):
    DESCRIPTION_MODULE = fields.String(load_default="")
    TITLE_MODULE = fields.String(load_default="Module monitoring")
    CODE_OBSERVERS_LIST = fields.String(load_default="obsocctax")
    # choose between raising errors or printing warnings
    STRICT = fields.Boolean(load_default=False)

    # Obsolète : les objets de permission associés à chaque type d'objet
    # sont définis par PERMISSION_OBJECT_CODES (gn_module_monitoring.constants)
    PERMISSION_LEVEL = fields.Dict(load_default=None)

    @pre_load
    def warn_deprecated(self, data, **kwargs):
        if "PERMISSION_LEVEL" in data:
            warn(
                "PERMISSION_LEVEL is deprecated and no longer used - "
                "permission objects are defined by PERMISSION_OBJECT_CODES "
                "in gn_module_monitoring.constants"
            )
        return data


#     AREA_TYPE = fields.List(fields.String(), missing=["COM", "M1", "M5", "M10"])
#     BORNE_OBS = fields.List(fields.Integer(), missing=[1, 20, 40, 60, 80, 100, 120])
#     BORNE_TAXON = fields.List(fields.Integer(), missing=[1, 5, 10, 15])
#     SIMPLIFY_LEVEL = fields.Integer(missing=50)
