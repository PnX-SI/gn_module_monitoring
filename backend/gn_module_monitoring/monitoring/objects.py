from gn_module_monitoring.monitoring.repositories import MonitoringObject
from gn_module_monitoring.monitoring.geom import MonitoringObjectGeom


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
        if all(isinstance(x, int) for x in properties["types_site"]):
            return
        # TODO: VERIFIER CE QUI EST NECESSAIRE A GARDER ICI
        if len(data) != 0:
            if len(data["types_site"]) > 0 and all(isinstance(x, int) for x in data["types_site"]):
                properties["types_site"] = data["types_site"]

        elif len(properties.get("types_site", [])) != 0:
            if hasattr(self._model, "types_site"):
                properties["types_site"] = data["types_site"]

            elif "data" in data and data["data"]["id_nomenclature_type_site"]:
                properties["id_nomenclature_type_site"] = data["data"]["id_nomenclature_type_site"]
            else:
                properties["id_nomenclature_type_site"] = data["types_site"][0][
                    "id_nomenclature_type_site"
                ]

            #         properties["types_site"] = []
            #         # TODO: performance?
            #         # for type in properties['types_site']:
            #         #     properties['types_site'].append(types_site)
            #         types_site = [
            #             typ.nomenclature.id_nomenclature for typ in self._model.types_site
            #         ]
            #         properties["types_site"] = types_site
            # TODO: A enlever une fois qu'on aura enelever le champ "id_nomenclature_type_site" du model et de la bdd


class MonitoringIndividual(MonitoringObject):
    """
    PATCH
    pour pouvoir renseigner la table cor_individual_module
    avec la méthode from_dict
    """

    def get_value_specific(self, param_name):
        # DO NOT LOAD data here
        pass

    def preprocess_data(self, data):
        module_ids = [module.id_module for module in self._model.modules]
        id_module = int(data["id_module"])
        if id_module not in module_ids:
            module_ids.append(id_module)

        data["modules"] = module_ids
