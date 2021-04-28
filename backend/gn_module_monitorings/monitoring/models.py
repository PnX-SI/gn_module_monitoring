"""
    Modèles SQLAlchemy pour les modules de suivi
"""
from sqlalchemy import select, func, and_
from sqlalchemy.orm import column_property
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
from pypnusershub.db.models import User


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
        lazy='joined',
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
        lazy='joined',
        primaryjoin=(TMedias.uuid_attached_row == TBaseVisits.uuid_base_visit),
        foreign_keys=[TMedias.uuid_attached_row])

    observers = DB.relationship(
        User,
        'gn_monitoring.cor_visit_observer',
        lazy='joined',
        primaryjoin=(CorVisitObserver.id_base_visit == id_base_visit),
        secondaryjoin=(CorVisitObserver.id_role == User.id_role),
    )

    observations = DB.relation(
        "TMonitoringObservations",
        lazy='select',
        primaryjoin=(TObservations.id_base_visit == TBaseVisits.id_base_visit),
        foreign_keys=[TObservations.id_base_visit],
        cascade="all,delete"
    )

    nb_observations = column_property(
        select([func.count(TObservations.id_base_visit)]).\
            where(TObservations.id_base_visit==id_base_visit)
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
        primary_key=True
    )

    id_module = DB.Column(
        DB.ForeignKey('gn_commons.t_modules.id_module'),
        nullable=False,
    )

    id_sites_group = DB.Column(
        DB.ForeignKey('gn_monitoring.t_sites_groups.id_sites_group',
        # ondelete='SET NULL'
        ),
        nullable=False,
    )

    data = DB.Column(JSONB)

    visits = DB.relationship(
        TMonitoringVisits,
        lazy="select",
        primaryjoin=(TBaseSites.id_base_site == TBaseVisits.id_base_site),
        foreign_keys=[TBaseVisits.id_base_site],
        cascade="all,delete"
    )

    medias = DB.relationship(
        TMedias,
        lazy='joined',
        primaryjoin=(TMedias.uuid_attached_row == TBaseSites.uuid_base_site),
        foreign_keys=[TMedias.uuid_attached_row],
        cascade="all",
    )

    last_visit = column_property(
        select([func.max(TBaseVisits.visit_date_min)]).\
            where(TBaseVisits.id_base_site==id_base_site)
    )

    nb_visits = column_property(
        select([func.count(TBaseVisits.id_base_site)]).\
            where(TBaseVisits.id_base_site==id_base_site)
    )

    geom_geojson = column_property(
        select([func.st_asgeojson(TBaseSites.geom)]).\
            where(TBaseSites.id_base_site==id_base_site).\
                correlate_except(TBaseSites)
    )

@serializable
class TMonitoringSitesGroups(DB.Model):
    __tablename__ = 't_sites_groups'
    __table_args__ = {'schema': 'gn_monitoring'}

    id_sites_group = DB.Column(
        DB.Integer,
        primary_key=True,
        nullable=False,
        unique=True
    )

    id_module = DB.Column(
        DB.ForeignKey('gn_commons.t_modules.id_module'),
        nullable=False,
        unique=True
    )

    uuid_sites_group = DB.Column(UUID(as_uuid=True), default=uuid4)

    sites_group_name = DB.Column(DB.Unicode)
    sites_group_code = DB.Column(DB.Unicode)
    sites_group_description = DB.Column(DB.Unicode)

    comments = DB.Column(DB.Unicode)

    data = DB.Column(JSONB)

    medias = DB.relationship(
        TMedias,
        primaryjoin=(TMedias.uuid_attached_row == uuid_sites_group),
        foreign_keys=[TMedias.uuid_attached_row],
        lazy="joined",
    )

    sites = DB.relationship(
        TMonitoringSites,
        uselist=True,  # pourquoi pas par defaut ?
        primaryjoin=(TMonitoringSites.id_sites_group == id_sites_group),
        foreign_keys=[TMonitoringSites.id_sites_group],
        lazy="joined",
    )

    nb_sites = column_property(
        select([func.count(TMonitoringSites.id_sites_group)]).\
            where(TMonitoringSites.id_sites_group==id_sites_group)
    )

    nb_visits = column_property(
        select([func.count(TMonitoringVisits.id_base_site)]).\
            where(and_(
                TMonitoringVisits.id_base_site == TMonitoringSites.id_base_site,
                TMonitoringSites.id_sites_group == id_sites_group
                )
        )
    )



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
        foreign_keys=[TMedias.uuid_attached_row],
        lazy='joined'
    )

    sites = DB.relationship(
        'TMonitoringSites',
        uselist=True,  # pourquoi pas par defaut ?
        primaryjoin=TMonitoringSites.id_module == id_module,
        foreign_keys=[id_module],
        lazy="select",
    )

    sites_groups = DB.relationship(
        'TMonitoringSitesGroups',
        uselist=True,  # pourquoi pas par defaut ?
        primaryjoin=TMonitoringSitesGroups.id_module == id_module,
        foreign_keys=[id_module],
        lazy="select",
    )

    datasets = DB.relationship(
        'TDatasets',
        secondary='gn_commons.cor_module_dataset',
        secondaryjoin=TDatasets.id_dataset == CorModuleDataset.id_dataset,
        join_depth=0,
        lazy="joined",
    )

    meta_create_date = DB.Column(DB.DateTime)
    meta_update_date = DB.Column(DB.DateTime)

    data = DB.Column(JSONB)

    # visits = DB.relationship(
    #     TMonitoringVisits,
    #     lazy="select",
    #     primaryjoin=(TModules.id_module == TBaseVisits.id_module),
    #     foreign_keys=[TBaseVisits.id_module],
    #     cascade="all,delete"
    # )



TMonitoringModules.visits = DB.relationship(
        TMonitoringVisits,
        lazy="select",
        primaryjoin=(TMonitoringModules.id_module == TMonitoringVisits.id_module),
        foreign_keys=[TMonitoringVisits.id_module],
        cascade="all"
    )


# add sites_group relationship to TMonitoringSites

TMonitoringSites.sites_group = (
    DB.relationship(
        TMonitoringSitesGroups,
        primaryjoin=(
            TMonitoringSitesGroups.id_sites_group == TMonitoringSites.id_sites_group
        ),
        cascade="all",
        lazy="select",
        uselist=False
    )
)

TMonitoringSitesGroups.visits = DB.relationship(
        TMonitoringVisits,
        primaryjoin=(TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group),
        secondaryjoin=(TMonitoringVisits.id_base_site == TMonitoringSites.id_base_site),
        secondary='gn_monitoring.t_site_complements',
    )

TMonitoringSitesGroups.nb_visits = column_property(
        select([func.count(TMonitoringVisits.id_base_site)]).\
            where(and_(
                TMonitoringVisits.id_base_site == TMonitoringSites.id_base_site,
                TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group
                )
    )
)
