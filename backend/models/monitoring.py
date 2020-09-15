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
from geonature.core.gn_meta.models import TDatasets
from geonature.utils.env import DB
from geonature.core.gn_commons.models import TModules


class CorSiteModule(DB.Model):
    __tablename__ = 'cor_site_module'
    __table_args__ = (
        DB.PrimaryKeyConstraint('id_module', 'id_base_site'),
        {'schema': 'gn_monitoring', 'extend_existing': True}
    )

    id_module = DB.Column(
        DB.ForeignKey('gn_commons.t_modules.id_module'),
        primary_key=True
    )
    id_base_site = DB.Column(
        DB.ForeignKey('gn_monitoring.t_base_sites.id_base_site'),
        primary_key=True
    )


class CorModuleDataset(DB.Model):
    __tablename__ = 'cor_module_dataset'
    __table_args__ = (
        DB.PrimaryKeyConstraint('id_module', 'id_dataset'),
        {'schema': 'gn_commons', 'extend_existing': True}
    )

    id_module = DB.Column(
        DB.ForeignKey('gn_commons.t_modules.id_module'),
        primary_key=True
    )
    id_dataset = DB.Column(
        DB.ForeignKey('gn_meta.t_datasets.id_dataset'),
        primary_key=True
    )


class CorVisitObserver(DB.Model):
    __tablename__ = 'cor_visit_observer'
    __table_args__ = (
        DB.PrimaryKeyConstraint('id_base_visit', 'id_role'),
        {'schema': 'gn_monitoring', 'extend_existing': True}
    )

    id_base_visit = DB.Column(
        DB.ForeignKey('gn_monitoring.t_base_visits.id_base_visit'),
        primary_key=True
    )
    id_role = DB.Column(
        DB.ForeignKey('utilisateurs.t_roles.id_role'),
        primary_key=True
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
        cascade="all,delete"
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
        cascade="all,delete"
    )

    @hybrid_property
    def nb_observations(self):
        return len(self.observations)


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
        cascade="all,delete"
        )

    medias = DB.relationship(
        TMedias,
        primaryjoin=(TMedias.uuid_attached_row == TBaseSites.uuid_base_site),
        foreign_keys=[TMedias.uuid_attached_row],
        cascade="all,delete")

    @hybrid_property
    def last_visit(self):
        last_visit = None
        if self.visits:
            for visit in self.visits:
                if not last_visit or last_visit < visit.visit_date_min:
                    last_visit = visit.visit_date_min

        return last_visit

    @hybrid_property
    def nb_visits(self):
        return len(self.visits)


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

    id_list_observer = DB.Column(DB.Integer)
    id_list_taxonomy = DB.Column(DB.Integer)

    taxonomy_display_field_name = DB.Column(DB.Unicode)
    b_synthese = DB.Column(DB.Boolean)

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

    datasets = DB.relationship(
        'TDatasets',
        secondary='gn_commons.cor_module_dataset',
        primaryjoin=id_module == CorModuleDataset.id_module,
        secondaryjoin=TDatasets.id_dataset == CorModuleDataset.id_dataset,
        join_depth=0,
        lazy="select",
    )

    meta_create_date = DB.Column(DB.DateTime)
    meta_update_date = DB.Column(DB.DateTime)