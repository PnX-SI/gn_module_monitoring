import json

from .repositories import MonitoringObject


class MonitoringObjectGeom(MonitoringObject):

    def as_geofeature(self, depth=None, columns=()):
        # TODO refaire
        id_field_name = self.config_param('id_field_name')
        geom_field_name = self.config_param('geom_field_name')
        return self._model.as_geofeature(geom_field_name, id_field_name, depth=depth, columns=columns)

    def serialize(self, depth):
        monitoring_object_dict = MonitoringObject.serialize(self, depth)
        geometry = {}

        if hasattr(self._model, 'geom_geojson'):
            geom_geojson = getattr(self._model, 'geom_geojson')
             
            geometry = json.loads(
                # self._model.__dict__.get('geom_geojson')
                getattr(self._model, 'geom_geojson')
            ) if geom_geojson else None
        if not self._id:
            geometry = None

        monitoring_object_dict['geometry'] = geometry

        return monitoring_object_dict
