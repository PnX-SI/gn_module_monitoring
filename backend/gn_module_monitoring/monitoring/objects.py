from .repositories import MonitoringObject
from .geom import MonitoringObjectGeom
from geonature.utils.env import DB
from geonature.core.gn_commons.models import TModules


class MonitoringModule(MonitoringObject):
    def get(self, param_value=None, param_name=None, depth=0):
        """
        pour récupérer le module sans l'id_module mais avec le module_code
        """
        if not param_name:
            param_name = "module_code"
            if not param_value:
                param_value = self._module_code
        MonitoringObject.get(self, param_value, param_name, depth)
        self._id = self._model.id_module
        return self


class MonitoringSite(MonitoringObjectGeom):
    """
    PATCH
    pour pouvoir renseigner la table cor_site_module
    avec la méthode from_dict
    """

    def preprocess_data(self, properties, data=[]):
        if len(data) != 0:
            if len(data["types_site"]) > 0 and all(isinstance(x, int) for x in data["types_site"]):
                properties["id_nomenclature_type_site"] = data["types_site"][0]
                properties["types_site"] = data["types_site"]

            elif "data" in data and data["data"]["id_nomenclature_type_site"]:
                properties["id_nomenclature_type_site"] = data["data"]["id_nomenclature_type_site"]
            else:
                properties["id_nomenclature_type_site"] = data["types_site"][0][
                    "id_nomenclature_type_site"
                ]
        elif len(properties.get("types_site", [])) != 0:
            if hasattr(self._model, "types_site"):
                properties["id_nomenclature_type_site"] = properties["types_site"][0]
                properties["types_site"] = data["types_site"]

        #         properties["types_site"] = []
        #         # TODO: performance?
        #         # for type in properties['types_site']:
        #         #     properties['types_site'].append(types_site)
        #         types_site = [
        #             typ.nomenclature.id_nomenclature for typ in self._model.types_site
        #         ]
        #         properties["types_site"] = types_site
        # TODO: A enlever une fois qu'on aura enelever le champ "id_nomenclature_type_site" du model et de la bdd
