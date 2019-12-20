from ..monitoring.repositories import MonitoringObject
from ..monitoring.objects import MonitoringSite


class MonitoringCircuit(MonitoringSite):

    def get(self, param_value=None, param_name=None):

        # teste si les points du circuit ont été modifiés

        # et le cas échéant met à jour la geometrie du circuit (polygone englobant les point)
        if (not param_name) or param_name == 'id_base_site':
            self.id_base_site = param_value

        MonitoringObject.get(self, param_value, param_name)

        return self

    def create_or_update(self, post_data):

        if not post_data.get('geometry'):
            post_data['geometry'] = self.fake_geom_circuit()

        return MonitoringObject.create_or_update(self, post_data)

    def fake_geom_circuit(self):
        return {
                "type": "Polygon",
                "coordinates": [[
                    [3.63, 44.85],
                    [3.64, 44.86],
                    [3.65, 44.85]
                ]]
            }


class MonitoringCircuitPoint(MonitoringSite):

    def process_correlations(self, post_data):
        pass

    def create_or_update(self, post_data):
        print('postData', post_data)
        self = MonitoringObject.create_or_update(self, post_data)
        self._model.check_and_set_geom_circuit()

        return self
