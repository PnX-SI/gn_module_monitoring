from geonature.utils.errors import GeoNatureError

from ..routes.decorators import cruved_scope_for_user_in_monitoring_module

from ..config.repositories import (
    config_param as repositories_config_param,
    config_schema as repositories_config_schema,
    get_config as repositories_get_config,
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

    def monitoring_object_instance(self, module_code, object_type, id=None, model=None):
        return self.MonitoringObject(object_type)(module_code, object_type, id, model)

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
    _module_code = None
    _id = None

    _model = None
    _children = {}
    _parent = None

    def __init__(self, module_code, object_type, id=None, model=None):

        self._module_code = module_code
        self._object_type = object_type

        self._id = id
        if not self._id and model:
            self._id = getattr(model, self.config_param('id_field_name'))

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
            .format(self._module_code, self._object_type, self._id)
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

    def config(self):
        return repositories_get_config(self._module_code)

    def config_param(self, param_name):
        return repositories_config_param(self._module_code, self._object_type, param_name)

    def get_value_generic(self, param_name):
        if not hasattr(self._model, param_name):
            return None
        return getattr(self._model, param_name)

    def get_value_specific(self, param_name):
        return self._model.data and self._model.data.get(param_name)

    def get_value(self, param_name):
        schema_generic = self.config_schema('generic')
        if param_name in schema_generic:
            return self.get_value_generic(param_name)
        return self.get_value_specific(param_name)

    def config_value(self, param_name):
        field_name = self.config_param(param_name)
        return self.get_value(field_name)

    def parent_type(self):
        '''
            on renvoie le premier de la liste
        '''
        return self.config_param('parent_types') and self.config_param('parent_types')[0]

    def parent_config_param(self, param_name):

        parent_type = self.parent_type()
        if parent_type:
            return repositories_config_param(self._module_code, parent_type, param_name)

    def config_schema(self, type_schema='all'):
        return repositories_config_schema(self._module_code, self._object_type, type_schema)
        pass

    # def base_type_object(self):
    #     """
    #         renvoie:
    #         - le type d'objet dont herite l'objet
    #         - le type d'objet sinon

    #     """
    #     return self.config_param('inherit_type') or self._object_type

    # def is_similar_to_parent(self):
    #     '''
    #         on teste si le type de parent est similaire au type de l'object (ou au type herite de l'object)
    #     '''
    #     base_object_type = self.base_type_object()
    #     parent_type = self.config_param('parent_type')

    #     if not parent_type:
    #         return False

    #     base_parent_type = (
    #         repositories_config_param(self._module_code, parent_type, 'inherit_type') or parent_type
    #     )

    #     return base_object_type == base_parent_type

    def id_parent_fied_name(self):
        return self.parent_config_param('id_field_name')

    def id_parent(self):
        parent_type = self.parent_type()

        if not parent_type:
            return
        if 'module' in parent_type:
            return self._module_code

        return getattr(self._model, self.id_parent_fied_name())

    def get_cruved(self, object_type=None):
        return cruved_scope_for_user_in_monitoring_module(self._module_code, object_type)

    def cond_filters(self):
        filters = self.config_param('filters')

        if not filters:
            return True

        cond = True
        for key in filters:
            cond = cond and self.get_value(key) == filters[key]

        return cond
