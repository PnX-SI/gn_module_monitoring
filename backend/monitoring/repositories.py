from geonature.utils.env import DB
from geonature.utils.errors import GeoNatureError
from geonature.core.gn_synthese.utils.process import import_from_table
from .serializer import MonitoringObjectSerializer
from ..config.repositories import get_config
import logging

log = logging.getLogger(__name__)

def check_config(f):
    '''
        decorateur pour s'assurer que la config est bien à jour des fichiers et de la base
        evite la multiplication des appels à la base
    '''
    def _check_config(*args, **kwargs):
        get_config(args[0]._module_code, verification_date=True)

        return f(*args, **kwargs)

    return _check_config

class MonitoringObject(MonitoringObjectSerializer):

    @check_config
    def get(self, value=None, field_name=None):

        # par defaut on filtre sur l'id

        if not field_name:
            field_name = self.config_param('id_field_name')
            if not value:
                value = self._id

        if not value:
            return self

        try:
            Model = self.MonitoringModel()
            self._model = (
                DB.session.query(Model)
                .filter(getattr(Model, field_name) == value)
                .one()
            )

            self._id = getattr(self._model, self.config_param('id_field_name'))

            return self

        except Exception as e:
            raise GeoNatureError('MONITORING : get_object : {}'.format(e))

    def process_post_data_properties(self, post_data):

        # id_parent dans le cas d'heritage

        properties = post_data['properties']

        id_parent = post_data.get('id_parent')  # TODO remove
        if id_parent:
            parent_id_field_name = self.parent_config_param('id_field_name')
            properties[parent_id_field_name] = post_data['id_parent']

    @check_config
    def process_synthese(self, process_module=False, limit=1000):

        # test du parametre synthese 
        if not self.config().get('synthese'):
            return

        # on ne le fait pas en automatique pour les modules
        # le process peut être trop long
        # peut être fait avec une api exprès (TODO !!)
        if self._object_type == 'module' and not process_module:
            return


        table_name = 'vs_{}'.format(self._module_code)
        try:
            import_from_table(
                'gn_monitoring',
                table_name,
                self.config_param('id_field_name'),
                self.config_value('id_field_name'),
                limit
            )
        except ValueError as e:
            # warning
            log.warning(
                """Error in module monitoring, process_synthese.
                Function import_from_table with parameters({}, {}, {}) raises the following error :
                {}
                """
                .format(
                    table_name,
                    self.config_param('id_field_name'),
                    self.config_value('id_field_name'),
                    e
                )
            )

        return True

    @check_config
    def create_or_update(self, post_data):

        try:

            # si id existe alors c'est un update
            self.get()

            b_creation = not self._id

            # ajout de l'objet dans le cas d'une creation

            # on assigne les données post à l'objet et on commite
            self.process_post_data_properties(post_data)
            self.populate(post_data)

            if b_creation:
                DB.session.add(self._model)
            DB.session.commit()

            self._id = getattr(self._model, self.config_param('id_field_name'))

            self.process_synthese()

            return self

        except Exception as e:
            raise GeoNatureError(
                "MONITORING: create_or_update {} : {}"
                .format(self, str(e))
            )

    @check_config
    def delete(self):

        if not self._id:
            raise GeoNatureError('Monitoring : delete object has no id')

        try:
            self.get()

            monitoring_object_out = self.serialize(1)

            DB.session.delete(self._model)
            DB.session.commit()

            return monitoring_object_out

        except Exception as e:
            raise GeoNatureError(
                'Delete {} raise error {}'
                .format(self, str(e))
            )

    @check_config
    def breadcrumb(self):

        breadcrumb = {
            'id': self._id,
            'label': self.config_param('label'),
            'description': str(self.config_value('description_field_name')),
            'module_code': self._module_code,
            'object_type': self._object_type,
        }

        return breadcrumb

    @check_config
    def breadcrumbs(self):

        breadcrumbs = [self.breadcrumb()]

        parent = self.get_parent()
        if parent:
            breadcrumbs = parent.breadcrumbs() + breadcrumbs

        return breadcrumbs

    @check_config
    def get_list(self, args=None):
        '''
            renvoie une liste d'objet serialisés
            possibilité de filtrer
            args arguments de requête get
            get_list(request.args.to_dict())

            TODO ajouter sort, page ou autres avec args
            TODO traiter geojson ?? 
            TODO filtrer par module ++++
        '''

        # test si présent dans le module 
        # sinon []

        if not self.config().get(self._object_type):
            return []

        Model = self.MonitoringModel()

        limit = args.get('limit')

        req = (
            DB.session.query(Model)
        )

        # filtres
        for key in args:
            if hasattr(Model, key):
                vals = args.getlist(key)
                req = req.filter(getattr(Model, key).in_(vals))

        # TODO page etc...

        res = (
            req
            .limit(limit)
            .all()
        )
        # TODO check if self.properties_names() == props et rel
        props = self.properties_names()

        return [
            r.as_dict(True, columns=props, relationships=props)
            for r in res
        ]
