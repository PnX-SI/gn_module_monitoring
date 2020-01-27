from .repositories import MonitoringObject


class MonitoringObjectGeom(MonitoringObject):

    def as_geofeature(self, depth=None, columns=()):
        id_field_name = self.config_param('id_field_name')
        geom_field_name = self.config_param('geom_field_name')
        return self._model.as_geofeature(geom_field_name, id_field_name, depth=depth, columns=columns)

    def serialize(self, depth):
        monitoring_object_dict = MonitoringObject.serialize(self, depth)

        geometry = {}

        if self.config_param('geom_field_name'):
            geofeature = self.as_geofeature(False, columns=(self.config_param('geom_field_name')))
            geometry = geofeature['geometry']

        if not self._id:
            geometry = None

        monitoring_object_dict['geometry'] = geometry

        return monitoring_object_dict

    def populate(self, postData):

        properties = postData['properties']
        self.unflatten_specific_properties(properties)
        self._model.from_geofeature(postData)
