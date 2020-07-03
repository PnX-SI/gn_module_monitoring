from .geom import MonitoringObjectGeom
from .repositories import MonitoringObject
from ..models.monitoring import CorSiteModule, CorVisitObserver, CorModuleDataset


class MonitoringVisit(MonitoringObject):

    def serialize(self, depth=0):

        monitoring_object_dict = MonitoringObject.serialize(self, depth)

        properties = monitoring_object_dict['properties']
        # on ne garde que les ids de observers
        if properties.get('observers'):
            observers = [obs.id_role for obs in properties['observers']]
            properties['observers'] = observers

        return monitoring_object_dict

    def process_correlations(self, post_data):

        properties = post_data['properties']
        observers = [id_role for id_role in properties.get('observers', [])]
        self.process_correlation(observers, CorVisitObserver, 'id_role')


class MonitoringSite(MonitoringObjectGeom):

    def process_correlations(self, post_data):

        id_module = post_data['properties']['id_module']
        self.process_correlation([id_module], CorSiteModule, 'id_module')


class MonitoringModule(MonitoringObject):

    def MonitoringModel(self):
        return MonitoringObject.MonitoringModel(self)

    def get(self, param_value=None, param_name=None):
        if not param_name:
            param_name = 'module_path'
            if not param_value:
                param_value = self._module_path
        MonitoringObject.get(self, param_value, param_name)
        self._id = self._model.id_module
        return self

    def process_correlations(self, post_data):

        datasets = post_data['properties']['datasets']
        print(datasets)
        self.process_correlation(datasets, CorModuleDataset, 'id_dataset')

    def serialize(self, depth=0):

        monitoring_object_dict = MonitoringObject.serialize(self, depth)

        properties = monitoring_object_dict['properties']
        # on ne garde que les ids de datasets
        if properties.get('datasets'):
            datasets = [dataset.id_dataset for dataset in properties['datasets']]
            properties['datasets'] = datasets

        return monitoring_object_dict



