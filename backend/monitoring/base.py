from geonature.utils.errors import GeoNatureError

from ..config.repositories import (
    config_param as repositories_config_param,
    config_schema as repositories_config_schema
)


class MonitoringDefinitions:
    '''
        class pour pouvoir obtenir les classes filles de MonitoringObjectBase
        fonction du type d'objet
        _MonitoringObjectTypes_dict sera initialisé ultérieurement
    '''

    _MonitoringObjects_dict = {}
    _MonitoringModels_dict = {}

    # partage tout avec toutes les instances de classe
    # ref: https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state

    def set(self, MonitoringObjects_dict, MonitoringModels_dict):
        self._MonitoringObjects_dict = MonitoringObjects_dict
        self._MonitoringModels_dict = MonitoringModels_dict
        return self

    def MonitoringObject(self, object_type):
        try:
            return self._MonitoringObjects_dict[object_type]
        except Exception as e:
            raise GeoNatureError(
                "MONITORING, il n'y a pas de monitoring_object pour le type {} : {}"
                .format(object_type, str(e))
            )

    def monitoring_object_instance(self, module_path, object_type, id=None, model=None):
        return self.MonitoringObject(object_type)(module_path, object_type, id, model)

    def MonitoringModel(self, object_type):
        try:
            return self._MonitoringModels_dict[object_type]
        except Exception as e:
            raise GeoNatureError(
                "MONITORING, il n'y a pas de modele pour le type {} : {}"
                .format(object_type, str(e))
            )


monitoring_definitions = MonitoringDefinitions()


class MonitoringObjectBase():

    _object_type = None
    _module_path = None
    _id = None

    _model = None
    _children = {}
    _parent = None

    def __init__(self, module_path, object_type, id=None, model=None):

        self._module_path = module_path
        self._object_type = object_type

        self.id = id
        if not self.id and model:
            self.id = getattr(model, self.config_param('id_field_name'))

        self.set_model_from(model)

    def set_model_from(self, model):
        if model:
            self._model = model
        else:
            Model = self.MonitoringModel()
            self._model = Model()

    def __str__(self):
        return (
            'monitoringobject {}, {}, {}'
            .format(self._module_path, self._object_type, self.id)
            )

    def MonitoringModel(self):

        try:
            Model = (
                monitoring_definitions
                .MonitoringModel(
                    self._object_type
                )
            )
            return Model
            pass

        except Exception:
            pass

        inherit_type = self.config_param('inherit_type')
        new_object_type = inherit_type or self._object_type

        Model = monitoring_definitions.MonitoringModel(new_object_type)
        return Model

    def config_param(self, param_name):
        return repositories_config_param(self._module_path, self._object_type, param_name)

    def config_value(self, param_name):
        field_name = self.config_param(param_name)
        return getattr(self._model, field_name)

    def parent_config_param(self, param_name):
        parent_type = self.config_param('parent_type')
        if parent_type:
            return repositories_config_param(self._module_path, parent_type, param_name)

    def config_schema(self, type_schema='all'):
        return repositories_config_schema(self._module_path, self._object_type, type_schema)
        pass

    def base_type_object(self):
        """
            renvoie:
            - le type d'objet dont herite l'objet
            - le type d'objet sinon

        """
        return self.config_param('inherit_type') or self._object_type

    def is_similar_to_parent(self):
        '''
            on teste si le type de parent est similaire au type de l'object (ou au type herite de l'object)
        '''
        base_object_type = self.base_type_object()
        parent_type = self.config_param('parent_type')

        if not parent_type:
            return False

        base_parent_type = (
            repositories_config_param(self._module_path, parent_type, 'inherit_type') or parent_type
        )

        return base_object_type == base_parent_type

    def id_parent_fied_name(self):

        if self.is_similar_to_parent():
            return 'id_parent'
        else:
            id_parent_field_name = self.parent_config_param('id_field_name')

        return id_parent_field_name

    def id_parent(self):
        parent_type = self.config_param('parent_type')

        if not parent_type:
            return
        if 'module' in parent_type:
            return self._module_path

        return getattr(self._model, self.id_parent_fied_name())
