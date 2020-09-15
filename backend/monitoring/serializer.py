'''
    serialiser
'''
import datetime
import uuid
from .base import MonitoringObjectBase, monitoring_definitions
from ..utils.utils import to_int


class MonitoringObjectSerializer(MonitoringObjectBase):

    def get_parent(self):

        parent_type = self.config_param('parent_type')
        if not parent_type:
            return

        if self._parent:
            return self._parent

        return (
            monitoring_definitions
            .monitoring_object_instance(
                self._module_code,
                parent_type,
                self.id_parent()
            )
            .get()
        )

    def get_site_id(self):
        if not self._id:
            return
        if self._object_type == 'site':
            return self._model.id_base_site
        parent = self.get_parent()
        if not parent:
            return
        return parent.get_site_id()

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

    # def clean_properties(self, properties):
    #     # clean properties

    #     config_properties_keys = self.config_param('properties_keys')
    #     properties_clean = {}
    #     for key in properties:
    #         if key in config_properties_keys:
    #             properties_clean[key] = properties[key]
    #     return properties_clean

    # def patch_hybrid_properties(self, properties):
    #     # TODO!! idéalement à faire dans utils_flask_slqalchemy
    #     # patch pour les proprietes qui ne sortent pas avec le as_dict()
    #     # par ex le site dans last visit qui est hybride

    #     for key in self.config_param('properties_keys'):
    #         if key in properties or not hasattr(self._model, key):
    #             continue
    #         val = getattr(self._model, key)
    #         if isinstance(val, (datetime.date)):
    #             val = str(val)
    #         if not val:
    #             val = None
    #         properties[key] = val

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

            children_of_type = [
                monitoring_definitions
                .monitoring_object_instance(self._module_code, children_type, model=child_model)
                # .get()
                .serialize(depth)
                for child_model in getattr(self._model, relation_name)
            ]
            children[children_type] = children_of_type
        return children

    def properties_names(self):
        generic = list(self.config_schema('generic').keys())
        data = ['data'] if hasattr(self._model, 'data') else []
        return generic + data

    def serialize(self, depth=1):

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
            val = getattr(self._model, field_name)
            if isinstance(val, (datetime.date, uuid.UUID)):
                val = str(val)
            properties[field_name] = val

        children = None
        if depth >= 0:
            children = self.serialize_children(depth)

        # processe properties
        self.flatten_specific_properties(properties)

        if properties.get('medias'):
            medias = [media.as_dict() for media in properties['medias']]
            properties['medias'] = medias

        monitoring_object_dict = {
            'properties': properties,
            'object_type': self._object_type,
            'module_code': self._module_code,
            'site_id': self.get_site_id(),
            'id': self._id,
        }

        if self._object_type == 'module':
            monitoring_object_dict['cruved'] = self.get_cruved()

        properties['id_parent'] = to_int(self.id_parent())
        if(children):
            monitoring_object_dict['children'] = children

        return monitoring_object_dict

    def populate(self, postData):

        properties = postData['properties']

        # données spécifiques
        self.unflatten_specific_properties(properties)

        self._model.from_dict(properties)
