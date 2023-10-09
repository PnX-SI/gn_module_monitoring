import json

from .repositories import MonitoringObject


class MonitoringObjectGeom(MonitoringObject):
    def as_geofeature(self, depth=None, columns=()):
        # TODO refaire
        id_field_name = self.config_param("id_field_name")
        geom_field_name = self.config_param("geom_field_name")
        return self._model.as_geofeature(
            geom_field_name, id_field_name, depth=depth, columns=columns
        )

    def serialize(self, depth, is_child=False):
        monitoring_object_dict = MonitoringObject.serialize(self, depth, is_child)
        geometry = {}

        if hasattr(self._model, "geom_geojson"):
            geom_geojson = getattr(self._model, "geom_geojson")

            geometry = (
                json.loads(
                    # self._model.__dict__.get('geom_geojson')
                    getattr(self._model, "geom_geojson")
                )
                if geom_geojson
                else None
            )
        if not self._id:
            geometry = None

        monitoring_object_dict["geometry"] = geometry
        if len(monitoring_object_dict["properties"].get("types_site", [])) != 0:
            if hasattr(self._model, "types_site"):
                # TODO: performance?
                types_site = [typ.nomenclature.label_fr for typ in self._model.types_site]
            monitoring_object_dict["properties"]["types_site"] = types_site
        return monitoring_object_dict
