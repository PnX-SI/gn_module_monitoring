from geonature.utils.env import DB
from geonature.utils.errors import GeoNatureError
from geonature.core.gn_synthese.utils.process import import_from_table
from .serializer import MonitoringObjectSerializer

import logging

log = logging.getLogger(__name__)


class MonitoringObject(MonitoringObjectSerializer):

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

    def process_synthese(self):
        if not self.config().get('synthese'):
            return

        table_name = 'vs_{}'.format(self._module_code)
        try:
            import_from_table(
                'gn_monitoring',
                table_name,
                self.config_param('id_field_name'),
                self.config_value('id_field_name')
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

        return

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

    def breadcrumb(self):

        breadcrumb = {
            'id': self._id,
            'label': self.config_param('label'),
            'description': str(self.config_value('description_field_name')),
            'module_code': self._module_code,
            'object_type': self._object_type,
        }

        return breadcrumb

    def breadcrumbs(self):
        breadcrumbs = [self.breadcrumb()]

        parent = self.get_parent()
        if parent:
            breadcrumbs = parent.breadcrumbs() + breadcrumbs

        return breadcrumbs

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
                print(vals)
                req = req.filter(getattr(Model, key).in_(vals))

        # TODO page etc...

        res = (
            req
            .limit(limit)
            .all()
        )
        print(res)
        # TODO check if self.properties_names() == props et rel
        props = self.properties_names()

        return [
            r.as_dict(True, columns=props, relationships=props)
            for r in res
        ]
