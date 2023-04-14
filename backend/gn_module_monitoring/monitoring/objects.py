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

    def preprocess_data(self, data):
        type_site_ids = [type_site.id_nomenclature_type_site for type_site in self._model.types_site]
        if len(data['types_site']) >0 :
            for id_type_site in data['types_site']:
                if int(id_type_site) not in type_site_ids:
                    type_site_ids.append(id_type_site)
            #TODO: A enlever une fois qu'on aura enelever le champ "id_nomenclature_type_site" du model et de la bdd
            data["id_nomenclature_type_site"]=data["types_site"][0]

        data['types_site'] = type_site_ids
