"""
    Modèles SQLAlchemy pour les modules de suivi
"""
from sqlalchemy.dialects.postgresql import JSONB, UUID
from uuid import uuid4

from utils_flask_sqla.serializers import serializable
from utils_flask_sqla_geo.serializers import geoserializable

from sqlalchemy.ext.hybrid import hybrid_property

from geonature.core.gn_commons.models import TMedias
from geonature.core.gn_monitoring.models import TBaseSites, TBaseVisits
from geonature.utils.env import DB
from geonature.core.gn_commons.models import TModules

# unmap_list = ['modules', 't_base_visits', 'digitiser', 'inventor', 'observers', 'dataset']
# Models = [TBaseVisits, TBaseSites]

# # unmap
# for map_name in unmap_list:
#     for Model in Models:
#         if hasattr(Model, map_name):
#             setattr(Model, map_name, 0)


class CorSiteModule(DB.Model):
    __tablename__ = 'cor_site_module'
    __table_args__ = (
        DB.PrimaryKeyConstraint('id_module', 'id_base_site'),
        {'schema': 'gn_monitoring'}
    )

    id_module = DB.Column(
        DB.ForeignKey('gn_commons.t_modules.id_module')
    )
    id_base_site = DB.Column(
        DB.ForeignKey('gn_monitoring.t_base_sites.id_base_site')
    )


class CorVisitObserver(DB.Model):
    __tablename__ = 'cor_visit_observer'
    __table_args__ = (
        DB.PrimaryKeyConstraint('id_base_visit', 'id_role'),
        {'schema': 'gn_monitoring'}
    )

    id_base_visit = DB.Column(
        DB.ForeignKey('gn_monitoring.t_base_visits.id_base_visit')
    )
    id_role = DB.Column(
        DB.ForeignKey('utilisateurs.t_roles.id_role')
    )


@serializable
class TMonitoringObservationDetails(DB.Model):
    __tablename__ = "t_observation_details"
    __table_args__ = {"schema": "gn_monitoring"}

    id_observation_detail = DB.Column(
        DB.Integer,
        primary_key=True,
        nullable=False,
        unique=True
    )

    id_observation = DB.Column(DB.ForeignKey('gn_monitoring.t_observations.id_observation'))
    data = DB.Column(JSONB)


@serializable
class TObservations(DB.Model):
    __tablename__ = "t_observations"
    __table_args__ = {"schema": "gn_monitoring"}

    id_observation = DB.Column(
        DB.Integer,
        primary_key=True,
        nullable=False,
        unique=True)
    id_base_visit = DB.Column(
        DB.ForeignKey('gn_monitoring.t_base_visits.id_base_visit'))
    cd_nom = DB.Column(DB.Integer)
    comments = DB.Column(DB.String)
    uuid_observation = DB.Column(UUID(as_uuid=True), default=uuid4)

    medias = DB.relationship(
        TMedias,
        primaryjoin=(TMedias.uuid_attached_row == uuid_observation),
        foreign_keys=[TMedias.uuid_attached_row])

    t_observation_details = DB.relation(
        TMonitoringObservationDetails,
        primaryjoin=(id_observation == TMonitoringObservationDetails.id_observation),
        foreign_keys=[TMonitoringObservationDetails.id_observation],
    )


@serializable
class TMonitoringObservations(TObservations):
    __tablename__ = "t_observation_complements"
    __table_args__ = {"schema": "gn_monitoring"}
    __mapper_args__ = {
        'polymorphic_identity': 'monitoring_observation',
    }

    data = DB.Column(JSONB)

    id_observation = DB.Column(
        DB.ForeignKey('gn_monitoring.t_observations.id_observation'),
        primary_key=True,
        nullable=False,
        )


@serializable
class TMonitoringVisits(TBaseVisits):
    __tablename__ = "t_visit_complements"
    __table_args__ = {"schema": "gn_monitoring"}
    __mapper_args__ = {
        'polymorphic_identity': 'monitoring_visit',
    }

    id_base_visit = DB.Column(
        DB.ForeignKey('gn_monitoring.t_base_visits.id_base_visit'),
        nullable=False,
        primary_key=True
        )

    data = DB.Column(JSONB)

    medias = DB.relationship(
        TMedias,
        primaryjoin=(TMedias.uuid_attached_row == TBaseVisits.uuid_base_visit),
        foreign_keys=[TMedias.uuid_attached_row])

    observations = DB.relation(
        "TMonitoringObservations",
        primaryjoin=(TObservations.id_base_visit == TBaseVisits.id_base_visit),
        foreign_keys=[TObservations.id_base_visit],
    )


@geoserializable
class TMonitoringSites(TBaseSites):

    __tablename__ = 't_site_complements'
    __table_args__ = {'schema': 'gn_monitoring'}
    __mapper_args__ = {
        'polymorphic_identity': 'monitoring_site',
    }

    id_base_site = DB.Column(
        DB.ForeignKey('gn_monitoring.t_base_sites.id_base_site'),
        nullable=False,
        primary_key=True)

    id_module = DB.Column(
        DB.ForeignKey('gn_commons.t_modules.id_module'),
        nullable=False,
        primary_key=True)

    data = DB.Column(JSONB)

    # unmap modules
    TBaseSites.modules = 0

    visits = DB.relationship(
        TMonitoringVisits,
        primaryjoin=(TBaseSites.id_base_site == TBaseVisits.id_base_site),
        foreign_keys=[TBaseVisits.id_base_site],
        # single_parent=True
        join_depth=0,
        )

    medias = DB.relationship(
        TMedias,
        primaryjoin=(TMedias.uuid_attached_row == TBaseSites.uuid_base_site),
        foreign_keys=[TMedias.uuid_attached_row])

    @hybrid_property
    def last_visit(self):
        last_visit = None
        if self.visits:
            for visit in self.visits:
                if not last_visit or last_visit < visit.visit_date_min:
                    last_visit = visit.visit_date_min

        return last_visit


@serializable
class TMonitoringModules(TModules):
    __tablename__ = 't_module_complements'
    __table_args__ = {'schema': 'gn_monitoring'}
    __mapper_args__ = {
        'polymorphic_identity': 'monitoring_module',
    }

    id_module = DB.Column(
        DB.ForeignKey('gn_commons.t_modules.id_module'),
        primary_key=True,
        nullable=False,
        unique=True
    )

    uuid_module_complement = DB.Column(UUID(as_uuid=True), default=uuid4)

    medias = DB.relationship(
        TMedias,
        primaryjoin=(TMedias.uuid_attached_row == uuid_module_complement),
        foreign_keys=[TMedias.uuid_attached_row]
    )

    sites = DB.relationship(
        'TMonitoringSites',
        secondary='gn_monitoring.cor_site_module',
        primaryjoin=id_module == CorSiteModule.id_module,
        secondaryjoin=TMonitoringSites.id_base_site == CorSiteModule.id_base_site,
        join_depth=0,
        lazy="select",
        # backref='parents'
    )
