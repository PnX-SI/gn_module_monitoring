from geonature.utils.env import DB
from geonature.utils.errors import GeoNatureError
from geonature.core.gn_synthese.utils.process import import_from_table
from .serializer import MonitoringObjectSerializer
from .base import MonitoringObjectBase, monitoring_definitions

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

        id_parent = post_data.get('id_parent')
        if id_parent:
            parent_id_field_name = self.parent_config_param('id_field_name')
            properties[parent_id_field_name] = post_data['id_parent']

    def process_correlations(self, post_data):
        # pour gérer et commiter les corrélations en tout genre
        # à redefinir dans class fille à definir dans les modèles sqlalchemy
        pass

    def process_correlation(self, cor_data_array, Cor, id_foreign_key_name):
        '''
            à mieux gérer avec sqlalchemy??
        '''
        id_field_name = self.config_param('id_field_name')

        cors = (
            DB.session.query(Cor)
            .filter(getattr(Cor, id_field_name) == self._id)
            .all()
        )

        for cor in cors:
            if getattr(cor, id_foreign_key_name) not in cor_data_array:
                DB.session.delete(cor)

        for foreign_id in cor_data_array:
            if int(foreign_id) not in [getattr(cor, id_foreign_key_name) for cor in cors]:
                cor_new = Cor()
                setattr(cor_new, id_foreign_key_name, foreign_id)
                setattr(cor_new, id_field_name, self._id)
                DB.session.add(cor_new)
                # new_cor.id_base_visit = self.id_base_visit
                # new_cor.id_role = id_role

        DB.session.commit()

    def process_synthese(self):
        if not self.config().get('synthese'):
            return

        table_name = 'vs_{}'.format(self._module_path)
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
            if b_creation:
                DB.session.add(self._model)

            # on assigne les données post à l'objet et on commite
            self.process_post_data_properties(post_data)
            self.populate(post_data)
            DB.session.commit()
            self._id = getattr(self._model, self.config_param('id_field_name'))

            self.process_correlations(post_data)

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
            'module_path': self._module_path,
            'object_type': self._object_type,
        }

        return breadcrumb

    def breadcrumbs(self):
        breadcrumbs = [self.breadcrumb()]

        parent = self.get_parent()
        if parent:
            breadcrumbs = parent.breadcrumbs() + breadcrumbs

        return breadcrumbs
