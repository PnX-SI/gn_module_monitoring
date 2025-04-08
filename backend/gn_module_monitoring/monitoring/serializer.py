"""
serialiser
"""

from flask import current_app, g

from marshmallow import EXCLUDE

from geonature.utils.env import DB
from geonature.core.gn_permissions.tools import get_scopes_by_action

from geonature.core.gn_monitoring.models import (
    TIndividuals,
)
from geonature.core.gn_monitoring.schema import TMarkingEventSchema
from gn_module_monitoring.utils.utils import to_int
from gn_module_monitoring.routes.data_utils import id_field_name_dict
from gn_module_monitoring.utils.routes import get_objet_with_permission_boolean
from gn_module_monitoring.monitoring.models import PermissionModel, TMonitoringModules
from gn_module_monitoring.monitoring.base import MonitoringObjectBase, monitoring_definitions
from gn_module_monitoring.monitoring.schemas import (
    MonitoringModuleSchema,
    MonitoringSitesSchema,
    MonitoringSitesGroupsSchema,
    MonitoringVisitsSchema,
    MonitoringObservationsSchema,
    MonitoringObservationsDetailsSchema,
    MonitoringIndividualsSchema,
)

MonitoringSerializer_dict = {
    "module": MonitoringModuleSchema,  # besoin pour retrouver le module depuis module_code à voir si on peux faire sans
    "site": MonitoringSitesSchema,
    "visit": MonitoringVisitsSchema,
    "sites_group": MonitoringSitesGroupsSchema,
    "observation": MonitoringObservationsSchema,
    "observation_detail": MonitoringObservationsDetailsSchema,
    "individual": MonitoringIndividualsSchema,
    "marking": TMarkingEventSchema,
}


class MonitoringObjectSerializer(MonitoringObjectBase):
    def get_parent(self):
        parent_type = self.parent_type()

        if not parent_type or parent_type == "module":
            return

        if not self._parent:
            self._parent = monitoring_definitions.monitoring_object_instance(
                self._module_code, parent_type, config=self._config, id=self.id_parent()
            ).get()

        return self._parent

    def get_site_id(self):
        if not self._id:
            return
        if hasattr(self._model, "id_base_site"):
            return self._model.id_base_site

        parent = self.get_parent()
        if not parent:
            return
        return parent.get_site_id()

    def as_dict(self, depth):
        return self._model.as_dict(depth=depth)

    def flatten_specific_properties(self, properties, only=None):
        # mise a plat des données spécifiques
        if "data" not in properties:
            return
        if not only:
            only = []

        data = properties.pop("data")
        data = data if data else {}
        for attribut_name in self.config_schema(type_schema="specific"):
            if attribut_name in only or not only:
                properties[attribut_name] = data.get(attribut_name)
        # Nécessaire pour récupérer tous les données des champs additionnels mêmes ceux non présents dans la config specific
        # Nécessaire pour les récupérer coté frontend lors de l'envoie de l'objet (patch et post)
        properties["additional_data_keys"] = []
        for prop in data:
            if prop not in properties.keys():
                properties[prop] = data[prop]
                properties["additional_data_keys"].append(prop)

    def unflatten_specific_properties(self, properties):
        data = {}
        for attribut_name, attribut_value in self.config_schema("specific").items():
            if "type_widget" in attribut_value and attribut_value["type_widget"] != "html":
                if attribut_name in properties:
                    val = properties.pop(attribut_name)
                else:
                    # TODO [DEV-SUIVI-EOLIEN] évaluer l'incidence
                    # TODO [DEV-SUIVI-EOLIEN] Ici il faut exclure les properties liés à la config generic + aux propriétés du model
                    #   voir comment générer les proprités spécifiques
                    #    non définies dans le schéma
                    val = None
                data[attribut_name] = val

        if data:
            properties["data"] = data
        else:
            properties["data"] = {}
        # On ajoute les propriétés associées aux types de site qui ne sont ni dans le schema specific ni dans generic ou appartenant au modèle
        prop_remaining_to_check = list(properties.keys())

        for prop in prop_remaining_to_check:
            is_in_model = hasattr(self._model, prop)
            if (
                not is_in_model
                and prop not in self.config_schema("generic").keys()
                and prop != "id_module"
                and prop != "data"
            ):
                properties["data"][prop] = properties.pop(prop)

    def get_readable_list_object(self, relation_name, children_type):
        childs_model = monitoring_definitions.MonitoringModel(object_type=children_type)

        scope = get_scopes_by_action(
            id_role=g.current_user.id_role,
            module_code=self._module_code,
            object_code=current_app.config["MONITORINGS"].get("PERMISSION_LEVEL", {})[
                children_type
            ],
        )["R"]
        if getattr(childs_model, "has_instance_permission", None) or scope < 3:
            childs_model = [
                m for m in getattr(self._model, relation_name) if m.has_instance_permission(scope)
            ]
            return childs_model
        elif scope == 0:
            return []
        else:
            childs_model = getattr(self._model, relation_name)
            return childs_model

    def serialize_children(self, depth):
        children_types = self.config_param("children_types")

        if not children_types:
            return

        children = {}

        for children_type in children_types:
            # attention a bien nommer les relation en children_type + 's' !!!
            relation_name = children_type + "s"

            if not hasattr(self._model, relation_name):
                continue

            scope = get_scopes_by_action(
                id_role=g.current_user.id_role,
                module_code=self._module_code,
                object_code=current_app.config["MONITORINGS"].get("PERMISSION_LEVEL", {})[
                    children_type
                ],
            )
            children_of_type = []

            childs_object_readable = self.get_readable_list_object(
                relation_name, children_type=children_type
            )
            for child_model in childs_object_readable:
                child = monitoring_definitions.monitoring_object_instance(
                    self._module_code, children_type, config=self._config, model=child_model
                )
                children_of_type.append(child.serialize(depth, is_child=True, scope=scope))

            children[children_type] = children_of_type

        return children

    def get_cruved_by_object(self):
        list_model = []
        list_model.append(self._model)
        if (
            isinstance(list_model[0], PermissionModel)
            and not isinstance(list_model[0], TMonitoringModules)
            and self._module_code != "generic"
        ):
            id_name = list_model[0].get_id_name()
            cruved_item_dict = get_objet_with_permission_boolean(
                list_model,
                module_code=self._module_code,
                object_code=current_app.config["MONITORINGS"].get("PERMISSION_LEVEL", {})[
                    self._object_type
                ],
            )
            for cruved_item in cruved_item_dict:
                if self._id == cruved_item[id_name]:
                    self.cruved = cruved_item["cruved"]
        return self.cruved

    def properties_names(self):
        generic = list(self.config_schema("generic").keys())
        data = ["data"] if hasattr(self._model, "data") else []
        return generic + data

    def serialize(self, depth=1, is_child=False, scope=None):
        # TODO faire avec un as_dict propre (avec props et relationships)
        if depth is None:
            depth = 1
        depth = depth - 1
        if not self._model:
            # on recupère le modèle SQLA
            Model = self.MonitoringModel()

            if not Model:
                return None

            self._model = Model()

        # Liste des propriétés de l'objet qui doivent être récupérées
        display_properties = []
        # Liste des propriétés spécifique de l'objet qui doivent être récupérées
        display_specific = []
        if is_child:
            module_config = self.config()
            # Si l'objet est un enfant on ne serialize que les attributs utilisés dans les data list
            display_properties = module_config[self._object_type]["display_list"]
            # liste des propriétés "génériques"
            display_generic = [
                k
                for k in display_properties
                if k in module_config[self._object_type]["generic"].keys()
            ]
            # liste des propriétés "spécifique"
            display_specific = [
                k
                for k in display_properties
                if k in module_config[self._object_type]["specific"].keys()
            ]
            if hasattr(self._model, "data"):
                display_generic.append("data")
            display_generic.append(self.config_param("id_field_name"))

            # Sérialisation de l'objet
            dump_object = MonitoringSerializer_dict[self._object_type](
                unknown=EXCLUDE, only=display_generic
            ).dump(self._model)

        else:
            # Si l'objet n'est pas un enfant on récupére toutes les informations
            # Pour pourvoir afficher le détails
            dump_object = MonitoringSerializer_dict[self._object_type](unknown=EXCLUDE).dump(
                self._model
            )
        properties = dump_object

        # Extraction des proprités spécifiques au même niveau que les génériques
        self.flatten_specific_properties(properties, only=display_specific)

        # Sérialisation des enfants
        children = None
        if depth >= 0:
            children = self.serialize_children(depth)

        schema = self.config_schema()

        for key in schema:
            if key in properties:
                definition = schema[key]
                value = properties[key]
                if not isinstance(value, list):
                    continue

                type_util = definition.get("type_util")

                # on passe d'une list d'objet à une liste d'id
                # si type_util est defini pour ce champs
                # si on a bien affaire à une liste de modèles sqla
                new_values = []
                for v in value:
                    if isinstance(v, DB.Model):
                        if type_util:
                            new_values.append(getattr(v, id_field_name_dict[type_util]))
                        else:
                            new_values.append(v.as_dict())
                    else:
                        new_values.append(v)
                properties[key] = new_values

        properties["id_parent"] = to_int(self.id_parent())

        if scope:
            if 1 in (scope["C"], scope["R"], scope["U"], scope["D"]):
                cruved = self.get_cruved_by_object()
            elif 2 in (scope["C"], scope["R"], scope["U"], scope["D"]):
                cruved = self.get_cruved_by_object()
            else:
                cruved = scope
        else:
            cruved = self.get_cruved_by_object()
        monitoring_object_dict = {
            "properties": properties,
            "object_type": self._object_type,
            "module_code": self._module_code,
            "site_id": self.get_site_id(),
            "id": self._id,
            "cruved": cruved,
        }

        if children:
            monitoring_object_dict["children"] = children

        return monitoring_object_dict

    def preprocess_data(self, data):
        pass

    def populate(self, post_data):
        # pour la partie sur les relationships mettre le from_dict dans utils_flask_sqla ???

        properties = post_data["properties"]

        # données spécifiques
        self.unflatten_specific_properties(properties)

        # pretraitement (pour t_base_site et cor_site_module)
        if "dataComplement" in post_data:
            self.preprocess_data(properties, post_data["dataComplement"])
        else:
            self.preprocess_data(properties)

        # ajout des données en base
        if (
            hasattr(self._model, "from_geofeature")
            and not (len(list(post_data)) == 1 and list(post_data)[0] == "properties")
            and post_data["geometry"] is not None
        ):
            for key in list(post_data):
                if key not in ("properties", "geometry", "type"):
                    post_data.pop(key)
            self._model.from_geofeature(post_data, True)
        else:
            self._model.from_dict(properties, True)
