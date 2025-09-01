from flask import current_app, g

from sqlalchemy import select
from sqlalchemy.sql import text

from geonature.utils.env import DB
from geonature.utils.errors import GeoNatureError
from geonature.core.gn_synthese.utils.process import import_from_table

from gn_module_monitoring.monitoring.serializer import MonitoringObjectSerializer
from gn_module_monitoring.utils.utils import to_int
from gn_module_monitoring.utils.routes import get_objet_with_permission_boolean
from gn_module_monitoring.monitoring.models import PermissionModel, TMonitoringModules

import logging
from ..utils.utils import to_int
from .base import monitoring_definitions
from sqlalchemy.orm import joinedload

log = logging.getLogger(__name__)


class MonitoringObject(MonitoringObjectSerializer):
    def get(self, value=None, field_name=None, depth=0):
        # par defaut on filtre sur l'id
        if not field_name:
            field_name = self.config_param("id_field_name")
            if not value:
                value = self._id

        if not value:
            return self

        try:
            Model = self.MonitoringModel()
            req = select(Model)
            # Test pour mettre les relations à joined
            # if depth > 0:
            #     options = []
            #     for children_type in self.config_param('children_types'):
            #         relation_name = children_type + 's'
            #         req = req.options(joinedload(relation_name))

            self._model = (
                DB.session.execute(req.where(getattr(Model, field_name) == value))
                .unique()
                .scalar_one()
            )

            self._id = getattr(self._model, self.config_param("id_field_name"))
            if isinstance(self._model, PermissionModel) and not isinstance(
                self._model, TMonitoringModules
            ):
                cruved_item_dict = get_objet_with_permission_boolean(
                    [self._model],
                    object_code=current_app.config["MONITORINGS"].get("PERMISSION_LEVEL", {})[
                        self._object_type
                    ],
                )
                self.cruved = cruved_item_dict[0]["cruved"]

            return self

        except Exception as e:
            raise GeoNatureError(
                f"MONITORING : get_object {self._module_code} {self._object_type} ({field_name}={value}) : {e}"
            )

    def process_post_data_properties(self, post_data):
        # id_parent dans le cas d'heritage

        properties = post_data["properties"]

        # id_parent = post_data.get('id_parent')  # TODO remove
        # if id_parent:
        #     parent_id_field_name = self.parent_config_param('id_field_name')
        #     properties[parent_id_field_name] = post_data['id_parent']

    def process_synthese(self, process_module=False, limit=1000):
        # test du parametre synthese
        if not self.config().get("synthese"):
            return

        # on ne le fait pas en automatique pour les modules
        # le process peut être trop long
        # peut être fait avec une api exprès (TODO !!)
        if self._object_type == "module" and not process_module:
            return

        table_name = "v_synthese_{}".format(self._module_code.lower())

        # Test de l'existance de la colonne de synchronisation sur la vue synthese
        column_exist = DB.engine.execute(
            text(
                """
                SELECT count(*)
                FROM information_schema.columns
                WHERE   table_schema=:table_schema
                    AND table_name=:table_name
                    AND column_name=:column_name;
                """
            ),
            table_schema="gn_monitoring",
            table_name=table_name,
            column_name=self.config_param("id_field_name"),
        ).fetchone()

        if column_exist[0] == 0:
            log.error(
                "Monitoring - Synchronisation synthèse : Column {} does not exist on view {}".format(
                    self.config_param("id_field_name"), table_name
                )
            )
            return

        import_from_table(
            "gn_monitoring",
            table_name,
            self.config_param("id_field_name"),
            self.config_value("id_field_name"),
            limit,
        )
        return True

    def create_or_update(self, post_data):
        try:
            # si id existe alors c'est un update
            self.get()

            b_creation = not self._id

            # ajout de l'objet dans le cas d'une creation

            # on assigne les données post à l'objet et on commite
            self.process_post_data_properties(post_data)
            self.populate(post_data)

            if b_creation:
                DB.session.add(self._model)
            DB.session.commit()
            self._id = getattr(self._model, self.config_param("id_field_name"))

            # TODO module have synthese enabled
            if not post_data["properties"]["id_module"] == "generic":
                self.process_synthese()

            return self

        except Exception as e:
            raise GeoNatureError("MONITORING: create_or_update {} : {}".format(self, str(e)))

    def delete(self):
        if not self._id:
            raise GeoNatureError("Monitoring : delete object has no id")

        try:
            self.get()

            monitoring_object_out = self.serialize(1)

            DB.session.delete(self._model)
            DB.session.commit()

            return monitoring_object_out

        except Exception as e:
            raise GeoNatureError("Delete {} raise error {}".format(self, str(e)))

    def breadcrumb(self, params):
        if not self._id:
            return

        breadcrumb = {
            "id": self._id,
            "label": self.config_param("label"),
            "description": str(self.config_value("description_field_name")),
            "module_code": self._module_code,
            "object_type": self._object_type,
        }

        if params["parents_path"]:
            breadcrumb["params"] = {"parents_path": [parent for parent in params["parents_path"]]}

        return breadcrumb

    def breadcrumbs(self, params):
        breadcrumb = self.breadcrumb(params)

        breadcrumbs = [breadcrumb] if breadcrumb else []

        next = None
        next_breadcrumbs = None
        if params["parents_path"]:
            object_type = params.get("parents_path", []).pop()
            if object_type == "module":
                next = None
                if g.current_module.module_code.upper() == "MONITORINGS":
                    module_code = "generic"
                else:
                    module_code = g.current_module.module_code
                next_breadcrumbs = {
                    "description": g.current_module.module_label,
                    "id": g.current_module.id_module,
                    "label": "Module",
                    "module_code": module_code,
                    "object_type": "module",
                }
            else:
                next = MonitoringObject(self._module_code, object_type, config=self._config)
                id_field_name = next.config_param("id_field_name")
                next._id = self.get_value(id_field_name) or params.get(id_field_name)
                next.get(0)
        else:
            next = self.get_parent()

        if next:
            breadcrumbs = next.breadcrumbs(params) + breadcrumbs
        if next_breadcrumbs:
            breadcrumbs = [next_breadcrumbs] + breadcrumbs

        return breadcrumbs

    def get_list(self, args=None):
        """
        renvoie une liste d'objet serialisés
        possibilité de filtrer
        args arguments de requête get
        get_list(request.args.to_dict())

        TODO ajouter sort, page ou autres avec args
        TODO traiter geojson ??
        TODO filtrer par module ++++
        """

        # test si présent dans le module
        # sinon []
        if not self.config().get(self._object_type):
            return []

        Model = self.MonitoringModel()

        limit = args.get("limit")

        order_by = args.getlist("order_by")

        req = select(Model)

        # Traitement de la liste des colonnes à retourner
        fields_list = args.getlist("fields")
        props = self.properties_names()
        if not fields_list:
            # TODO check if self.properties_names() == props et rel
            fields_list = props
        else:
            fields_list = [field for field in fields_list if field in props]

        # filtres params get
        for key in args:
            if key == "id_module" and hasattr(Model, "modules"):
                # Filtre particulier sur les modules
                req = req.where(Model.modules.any(id_module=args[key]))
            if hasattr(Model, key) and args[key] not in ["", None, "null", "undefined"]:
                vals = args.getlist(key)
                req = req.where(getattr(Model, key).in_(vals))

        #  Si le modèle est de type Permission model et qu'il implémente la fonction filter_by_readable
        #  Filtre des données retournées en fonction des permissions
        if hasattr(Model, "filter_by_readable"):
            req = Model.filter_by_readable(
                query=req,
                object_code=current_app.config["MONITORINGS"]
                .get("PERMISSION_LEVEL", {})
                .get(self._object_type, None),
                module_code=g.current_module.module_code,
            )
        # # filtres config

        # filters_config = self.config_param('filters')
        # if filters_config:
        #     req = req.filter_by(**filters_config)

        # order_by
        for s in order_by:
            if "*" in s:
                continue  # order by number
            elif s[-1] == "-":
                req = req.order_by(getattr(Model, s[:-1]).desc())
            else:
                req = req.order_by(getattr(Model, s))

        # TODO page etc...

        res = DB.session.scalars(req.limit(limit)).all()

        # patch order by number
        out = [r.as_dict(fields=fields_list) for r in res]

        # order by number
        # pour les cas 1.2 truc muche

        for s in order_by:
            if "*" in s:
                s2 = s.replace("-", "").replace("*", "")

                def extract_number(x):
                    try:
                        n = x[s2].split(" ")[0].split(".")
                        n0 = n[0]
                        n1 = n[1]
                        return to_int(n0) * 1e5 + to_int(n1)
                    except:
                        return 0

                out = sorted(out, key=extract_number)

        return out
