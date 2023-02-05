'''
    serialiser
'''
import datetime
import uuid
from flask import current_app
from .base import MonitoringObjectBase, monitoring_definitions
from ..utils.utils import to_int
from ..routes.data_utils import id_field_name_dict
from geonature.utils.env import DB


class MonitoringObjectSerializer(MonitoringObjectBase):

    def get_parent(self):

        parent_type = self.parent_type()
        if not parent_type:
            return

        if not self._parent:
            self._parent = (
                monitoring_definitions
                .monitoring_object_instance(
                    self._module_code,
                    parent_type,
                    self.id_parent()
                )
                .get()
            )

        return self._parent

    def get_site_id(self):
        if not self._id:
            return
        if hasattr(self._model, 'id_base_site'):
            return self._model.id_base_site
        return
        # parent = self.get_parent()
        # if not parent:
        #     return
        # return parent.get_site_id()

    def as_dict(self, depth):
        return self._model.as_dict(depth=depth)

    def flatten_specific_properties(self, properties):
        # mise a plat des données spécifiques
        if 'data' not in properties:
            return
        data = properties.pop('data')
        data = data if data else {}
        for attribut_name in self.config_schema(type_schema='specific'):
            properties[attribut_name] = data.get(attribut_name)

    def unflatten_specific_properties(self, properties):
        data = {}
        for attribut_name in self.config_schema('specific'):
            val = properties.pop(attribut_name)
            data[attribut_name] = val

        if data:
            properties['data'] = data

    def serialize_children(self, depth):
        children_types = self.config_param('children_types')

        if not children_types:
            return

        children = {}

        for children_type in children_types:
            # attention a bien nommer les relation en children_type + 's' !!!
            relation_name = children_type + 's'

            if not hasattr(self._model, relation_name):
                continue

            children_of_type = []

            for child_model in getattr(self._model, relation_name):
                child = (
                    monitoring_definitions
                    .monitoring_object_instance(self._module_code, children_type, model=child_model)
                )
                children_of_type.append(child.serialize(depth))

            children[children_type] = children_of_type

        return children

    def properties_names(self):
        generic = list(self.config_schema('generic').keys())
        data = ['data'] if hasattr(self._model, 'data') else []
        return generic + data

    def serialize(self, depth=1):
        # TODO faire avec un as_dict propre (avec props et relationships)
        if depth is None:
            depth = 1
        depth = depth-1
        if not self._model:
            # on recupère le modèle SQLA
            Model = self.MonitoringModel()

            if not Model:
                return None

            self._model = Model()

        properties = {}

        for field_name in self.properties_names():

            # val = self._model.__dict__.get(field_name)
            val = getattr(self._model, field_name)
            if isinstance(val, (datetime.date, uuid.UUID)):
                val = str(val)
            properties[field_name] = val

        children = None
        if depth >= 0:
            children = self.serialize_children(depth)


        # processe properties
        self.flatten_specific_properties(properties)

        schema = self.config_schema()
        for key in schema:
            definition = schema[key]
            value = properties[key]
            if not isinstance(value, list):
                continue

            type_util = definition.get('type_util')

            # on passe d'une list d'objet à une liste d'id
            # si type_util est defini pour ce champs
            # si on a bien affaire à une liste de modèles sqla
            properties[key] = [
                getattr(v, id_field_name_dict[type_util]) if (isinstance(v, DB.Model) and type_util)
                else v.as_dict() if (isinstance(v, DB.Model) and not type_util)
                else v
                for v in value
            ]

        monitoring_object_dict = {
            'properties': properties,
            'object_type': self._object_type,
            'module_code': self._module_code,
            'site_id': self.get_site_id(),
            'id': self._id,
        }

        if self._object_type == 'module':
            monitoring_object_dict['cruved'] = self.get_cruved()
            monitoring_object_dict['cruved_objects'] = {}
            monitoring_object_dict['cruved_objects']['site'] = self.get_cruved("GNM_SITES")
            monitoring_object_dict['cruved_objects']['sites_group'] = self.get_cruved("GNM_GRP_SITES")
            monitoring_object_dict['cruved_objects']['visite'] = self.get_cruved("GNM_VISITES")
            monitoring_object_dict['cruved_objects']['observation'] = self.get_cruved("GNM_OBSERVATIONS")


        properties['id_parent'] = to_int(self.id_parent())
        if(children):
            monitoring_object_dict['children'] = children

        return monitoring_object_dict

    def preprocess_data(self, data):
        # a redefinir dans la classe
        pass

    def populate(self, post_data):
        # pour la partie sur les relationships mettre le from_dict dans utils_flask_sqla ???

        properties = post_data['properties']

        # données spécifiques
        self.unflatten_specific_properties(properties)

        # pretraitement (pour t_base_site et cor_site_module)
        self.preprocess_data(properties)

        # ajout des données en base
        if hasattr(self._model, 'from_geofeature'):
            self._model.from_geofeature(post_data, True)
        else:
            self._model.from_dict(properties, True)
