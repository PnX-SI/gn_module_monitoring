import json

from marshmallow import EXCLUDE

from gn_module_monitoring.monitoring.repositories import MonitoringObject
from gn_module_monitoring.monitoring.serializer import MonitoringSerializer_dict


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

        if len(monitoring_object_dict["properties"].get("types_site", [])) != 0:
            if hasattr(self._model, "types_site"):
                # TODO: performance?
                types_site = [typ.nomenclature.label_fr for typ in self._model.types_site]
            monitoring_object_dict["properties"]["types_site"] = types_site

        # On ne sérialise la géométrie que si l'objet n'est pas un enfant
        # si l'objet est de type enfant il va être affiché au niveau du tableau
        # et sa géométrie sera récupérée a partir de la route /geometrie
        if not is_child:
            geometry = {}
            dump_object = MonitoringSerializer_dict[self._object_type](unknown=EXCLUDE).dump(
                self._model
            )
            # monitoring_object_dict['properties'] = dump_object
            if "geometry" in dump_object and self._model.geom is not None:
                geometry = (
                    json.loads(
                        # self._model.__dict__.get('geom_geojson')
                        dump_object["geometry"]
                    )
                    if dump_object["geometry"]
                    else None
                )

            elif hasattr(self._model, "geom_geojson"):
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
        return monitoring_object_dict
