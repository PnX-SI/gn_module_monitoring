"""
    Modèles SQLAlchemy pour les modules de suivi
"""

import geoalchemy2

from flask import g

from uuid import uuid4

from sqlalchemy import join, select, func, and_
from sqlalchemy.orm import (
    column_property,
    aliased,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from utils_flask_sqla.serializers import serializable
from utils_flask_sqla_geo.serializers import geoserializable

from sqlalchemy.ext.hybrid import hybrid_property

from geonature.utils.env import DB
from geonature.core.gn_commons.models import TMedias
from geonature.core.gn_monitoring.models import (
    TBaseSites,
    TBaseVisits,
    cor_module_type,
    cor_site_type,
    cor_visit_observer,
    cor_site_observer,
    TObservations,
)
from geonature.core.gn_meta.models import TDatasets
from geonature.core.gn_commons.models import TModules, cor_module_dataset
from geonature.core.gn_permissions.tools import has_any_permissions_by_action

from pypnusershub.db.models import User

from gn_module_monitoring.monitoring.queries import (
    GnMonitoringGenericFilter as MonitoringQuery,
    SitesQuery,
    SitesGroupsQuery,
    VisitQuery,
    ObservationsQuery,
)


class PermissionModel:
    def has_permission(
        self,
        cruved_object={"C": False, "R": False, "U": False, "D": False, "E": False, "V": False},
    ):
        cruved_object_out = {}
        for action_key, action_value in cruved_object.items():
            cruved_object_out[action_key] = self.has_instance_permission(scope=action_value)
        return cruved_object_out

    def get_permission_by_action(self, module_code=None, object_code=None):
        return has_any_permissions_by_action(module_code=module_code, object_code=object_code)


@serializable
class TMonitoringObservationDetails(DB.Model):
    __tablename__ = "t_observation_details"
    __table_args__ = {"schema": "gn_monitoring"}

    id_observation_detail = DB.Column(DB.Integer, primary_key=True, nullable=False, unique=True)

    id_observation = DB.Column(DB.ForeignKey("gn_monitoring.t_observations.id_observation"))
    data = DB.Column(JSONB)
    uuid_observation_detail = DB.Column(UUID(as_uuid=True), default=uuid4)

    medias = DB.relationship(
        TMedias,
        primaryjoin=(TMedias.uuid_attached_row == uuid_observation_detail),
        foreign_keys=[TMedias.uuid_attached_row],
        overlaps="medias,medias",
    )


@serializable
class TMonitoringObservations(TObservations, PermissionModel, ObservationsQuery):
    __tablename__ = "t_observation_complements"
    __table_args__ = {"schema": "gn_monitoring"}
    __mapper_args__ = {
        "polymorphic_identity": "monitoring_observation",
    }

    data = DB.Column(JSONB)

    id_observation = DB.Column(
        DB.ForeignKey("gn_monitoring.t_observations.id_observation"),
        primary_key=True,
        nullable=False,
    )

    medias = DB.relationship(
        TMedias,
        primaryjoin=(TMedias.uuid_attached_row == TObservations.uuid_observation),
        foreign_keys=[TMedias.uuid_attached_row],
    )

    observation_details = DB.relation(
        TMonitoringObservationDetails,
        primaryjoin=(id_observation == TMonitoringObservationDetails.id_observation),
        foreign_keys=[TMonitoringObservationDetails.id_observation],
        cascade="all,delete",
    )

    @hybrid_property
    def organism_actors(self):
        # return self.digitiser.id_organisme
        actors_organism_list = []
        if isinstance(self.digitiser, list):
            for actor in self.digitiser:
                if actor.id_organisme is not None:
                    actors_organism_list.append(actor.id_organisme)
        elif isinstance(self.digitiser, User):
            actors_organism_list.append(self.digitiser.id_organisme)
        return actors_organism_list

    def has_instance_permission(self, scope):
        if scope == 0:
            return False
        elif scope in (1, 2):
            if (
                g.current_user.id_role == self.id_digitiser
            ):  # or g.current_user in self.user_actors:
                return True
            if scope == 2 and g.current_user.id_organisme in self.organism_actors:
                return True
        elif scope == 3:
            return True


TBaseVisits.dataset = DB.relationship(TDatasets)


@serializable
class TMonitoringVisits(TBaseVisits, PermissionModel, VisitQuery):
    __tablename__ = "t_visit_complements"
    __table_args__ = {"schema": "gn_monitoring"}
    __mapper_args__ = {
        "polymorphic_identity": "monitoring_visit",
    }

    id_base_visit = DB.Column(
        DB.ForeignKey("gn_monitoring.t_base_visits.id_base_visit"),
        nullable=False,
        primary_key=True,
    )

    data = DB.Column(JSONB)

    medias = DB.relationship(
        TMedias,
        primaryjoin=(TMedias.uuid_attached_row == TBaseVisits.uuid_base_visit),
        foreign_keys=[TMedias.uuid_attached_row],
        overlaps="medias,medias",
    )

    observers = DB.relationship(User, lazy="joined", secondary=cor_visit_observer)

    observations = DB.relation(
        "TMonitoringObservations",
        lazy="select",
        primaryjoin=(TObservations.id_base_visit == TBaseVisits.id_base_visit),
        foreign_keys=[TObservations.id_base_visit],
        cascade="all,delete",
    )

    nb_observations = column_property(
        select(func.count(TObservations.id_base_visit))
        .where(TObservations.id_base_visit == id_base_visit)
        .scalar_subquery()
    )

    module = DB.relationship(
        TModules,
        lazy="select",
        primaryjoin=(TModules.id_module == TBaseVisits.id_module),
        foreign_keys=[TBaseVisits.id_module],
        uselist=False,
    )

    @hybrid_property
    def organism_actors(self):
        # return self.digitiser.id_organisme
        actors_organism_list = []
        if isinstance(self.digitiser, list):
            for actor in self.digitiser:
                if actor.id_organisme is not None:
                    actors_organism_list.append(actor.id_organisme)
        elif isinstance(self.observers, list):
            for actor in self.observers:
                if actor.id_organisme is not None:
                    actors_organism_list.append(actor.id_organisme)
        elif isinstance(self.digitiser, User):
            actors_organism_list.append(self.digitiser.id_organisme)
        return actors_organism_list

    def has_instance_permission(self, scope):
        if scope == 0:
            return False
        elif scope in (1, 2):
            if g.current_user.id_role == self.id_digitiser or any(
                observer.id_role == g.current_user.id_role for observer in self.observers
            ):  # or g.current_user in self.user_actors:
                return True
            if scope == 2 and g.current_user.id_organisme in self.organism_actors:
                return True
        elif scope == 3:
            return True


@geoserializable(geoCol="geom", idCol="id_base_site")
class TMonitoringSites(TBaseSites, PermissionModel, SitesQuery):
    __tablename__ = "t_site_complements"
    __table_args__ = {"schema": "gn_monitoring"}
    __mapper_args__ = {
        "polymorphic_identity": "monitoring_site",
    }

    id_base_site = DB.Column(
        DB.ForeignKey("gn_monitoring.t_base_sites.id_base_site"), nullable=False, primary_key=True
    )

    id_sites_group = DB.Column(
        DB.ForeignKey(
            "gn_monitoring.t_sites_groups.id_sites_group",
            # ondelete='SET NULL'
        ),
        nullable=False,
    )

    data = DB.Column(JSONB)
    observers = DB.relationship(User, lazy="joined", secondary=cor_site_observer)

    visits = DB.relationship(
        TMonitoringVisits,
        lazy="select",
        primaryjoin=(TBaseSites.id_base_site == TBaseVisits.id_base_site),
        foreign_keys=[TBaseVisits.id_base_site],
        cascade="all,delete",
        overlaps="t_base_visits",
    )

    medias = DB.relationship(
        TMedias,
        lazy="select",
        primaryjoin=(TMedias.uuid_attached_row == TBaseSites.uuid_base_site),
        foreign_keys=[TMedias.uuid_attached_row],
        cascade="all",
        overlaps="medias",
    )

    last_visit = column_property(
        select(func.max(TBaseVisits.visit_date_min))
        .where(TBaseVisits.id_base_site == id_base_site)
        .scalar_subquery()
    )

    nb_visits = column_property(
        select(func.count(TBaseVisits.id_base_site))
        .where(TBaseVisits.id_base_site == id_base_site)
        .scalar_subquery()
    )

    geom_geojson = column_property(
        select(func.st_asgeojson(TBaseSites.geom))
        .where(TBaseSites.id_base_site == id_base_site)
        .correlate_except(TBaseSites)
        .scalar_subquery()
    )
    types_site = DB.relationship("BibTypeSite", secondary=cor_site_type, overlaps="sites")

    @hybrid_property
    def organism_actors(self):
        actors_organism_list = []
        if isinstance(self.digitiser, list):
            for actor in self.digitiser:
                if actor.id_organisme is not None:
                    actors_organism_list.append(actor.id_organisme)
        elif isinstance(self.observers, list):
            for actor in self.observers:
                if actor.id_organisme is not None:
                    actors_organism_list.append(actor.id_organisme)
        elif isinstance(self.digitiser, User):
            actors_organism_list.append(self.digitiser.id_organisme)
        return actors_organism_list

    def has_instance_permission(self, scope):
        if scope == 0:
            return False
        elif scope in (1, 2):
            if g.current_user.id_role == self.id_digitiser or any(
                observer.id_role == g.current_user.id_role for observer in self.observers
            ):  # or g.current_user in self.user_actors:
                return True
            if scope == 2 and g.current_user.id_organisme in self.organism_actors:
                return True
        elif scope == 3:
            return True


@geoserializable(geoCol="geom", idCol="id_sites_group")
class TMonitoringSitesGroups(DB.Model, PermissionModel, SitesGroupsQuery):
    __tablename__ = "t_sites_groups"
    __table_args__ = {"schema": "gn_monitoring"}

    id_sites_group = DB.Column(DB.Integer, primary_key=True, nullable=False, unique=True)
    id_digitiser = DB.Column(DB.Integer, DB.ForeignKey("utilisateurs.t_roles.id_role"))

    digitiser = DB.relationship(
        User, primaryjoin=(User.id_role == id_digitiser), foreign_keys=[id_digitiser]
    )
    uuid_sites_group = DB.Column(UUID(as_uuid=True), default=uuid4)

    sites_group_name = DB.Column(DB.Unicode)
    sites_group_code = DB.Column(DB.Unicode)
    sites_group_description = DB.Column(DB.Unicode)

    comments = DB.Column(DB.Unicode)
    geom = DB.Column(geoalchemy2.types.Geometry("GEOMETRY", 4326, nullable=True))
    data = DB.Column(JSONB)

    medias = DB.relationship(
        TMedias,
        primaryjoin=(TMedias.uuid_attached_row == uuid_sites_group),
        foreign_keys=[TMedias.uuid_attached_row],
        overlaps="medias",
    )

    sites = DB.relationship(
        TMonitoringSites,
        uselist=True,  # pourquoi pas par defaut ?
        primaryjoin=(TMonitoringSites.id_sites_group == id_sites_group),
        foreign_keys=[TMonitoringSites.id_sites_group],
        lazy="select",
    )

    nb_sites = column_property(
        select(func.count(TMonitoringSites.id_sites_group))
        .where(TMonitoringSites.id_sites_group == id_sites_group)
        .scalar_subquery()
    )

    altitude_min = DB.Column(DB.Integer)
    altitude_max = DB.Column(DB.Integer)
    nb_visits = column_property(
        select(func.count(TMonitoringVisits.id_base_site))
        .where(
            TMonitoringVisits.id_base_site == TMonitoringSites.id_base_site,
            TMonitoringSites.id_sites_group == id_sites_group,
        )
        .scalar_subquery()
    )

    @hybrid_property
    def organism_actors(self):
        # return self.digitiser.id_organisme
        actors_organism_list = []
        if isinstance(self.digitiser, list):
            for actor in self.digitiser:
                if actor.id_organisme is not None:
                    actors_organism_list.append(actor.id_organisme)
        elif isinstance(self.digitiser, User):
            actors_organism_list.append(self.digitiser.id_organisme)
        return actors_organism_list

    def has_instance_permission(self, scope):
        if scope == 0:
            return False
        elif scope in (1, 2):
            if (
                g.current_user.id_role == self.id_digitiser
            ):  # or g.current_user in self.user_actors:
                return True
            if scope == 2 and g.current_user.id_organisme in self.organism_actors:
                return True
        elif scope == 3:
            return True


@serializable
class TMonitoringModules(TModules, PermissionModel, MonitoringQuery):
    __tablename__ = "t_module_complements"
    __table_args__ = {"schema": "gn_monitoring"}
    __mapper_args__ = {
        "polymorphic_identity": "monitoring_module",
    }

    id_module = DB.Column(
        DB.ForeignKey("gn_commons.t_modules.id_module"),
        primary_key=True,
        nullable=False,
        unique=True,
    )

    uuid_module_complement = DB.Column(UUID(as_uuid=True), default=uuid4)

    id_list_observer = DB.Column(DB.Integer)
    id_list_taxonomy = DB.Column(DB.Integer)

    taxonomy_display_field_name = DB.Column(DB.Unicode)
    b_synthese = DB.Column(DB.Boolean)
    b_draw_sites_group = DB.Column(DB.Boolean)

    medias = DB.relationship(
        TMedias,
        primaryjoin=(TMedias.uuid_attached_row == uuid_module_complement),
        foreign_keys=[TMedias.uuid_attached_row],
        lazy="select",
        overlaps="medias,medias",
    )

    # TODO: restore it with CorCategorySite
    # sites = DB.relationship(
    #     'TMonitoringSites',
    #     uselist=True,  # pourquoi pas par defaut ?
    #     primaryjoin=TMonitoringSites.id_module == id_module,
    #     foreign_keys=[id_module],
    #     lazy="select",
    # )

    # sites_groups = DB.relationship(
    #     'TMonitoringSitesGroups',
    #     uselist=True,  # pourquoi pas par defaut ?
    #     primaryjoin=TMonitoringSitesGroups.id_module == id_module,
    #     foreign_keys=[id_module],
    #     lazy="select",
    # )

    datasets = DB.relationship(
        "TDatasets",
        secondary=cor_module_dataset,
        join_depth=0,
        overlaps="modules",
    )

    types_site = DB.relationship(
        "BibTypeSite",
        secondary=cor_module_type,
    )

    data = DB.Column(JSONB)

    # visits = DB.relationship(
    #     TMonitoringVisits,
    #     lazy="select",
    #     primaryjoin=(TModules.id_module == TBaseVisits.id_module),
    #     foreign_keys=[TBaseVisits.id_module],
    #     cascade="all,delete"
    # )


# Use alias since there is already a FROM caused by count (column_properties)
sites_alias = aliased(TMonitoringSites)
TMonitoringModules.sites_groups = DB.relationship(
    "TMonitoringSitesGroups",
    uselist=True,  # pourquoi pas par defaut ?
    primaryjoin=TMonitoringModules.id_module == cor_module_type.c.id_module,
    secondaryjoin=and_(
        TMonitoringSitesGroups.id_sites_group == sites_alias.id_sites_group,
        sites_alias.id_base_site == cor_site_type.c.id_base_site,
    ),
    secondary=join(
        cor_site_type,
        cor_module_type,
        cor_site_type.c.id_type_site == cor_module_type.c.id_type_site,
    ),
    foreign_keys=[cor_site_type.c.id_base_site, cor_module_type.c.id_module],
    viewonly=True,
)


TMonitoringModules.sites = DB.relationship(
    "TMonitoringSites",
    uselist=True,  # pourquoi pas par defaut ?
    primaryjoin=TMonitoringModules.id_module == cor_module_type.c.id_module,
    secondaryjoin=TMonitoringSites.id_base_site == cor_site_type.c.id_base_site,
    secondary=join(
        cor_site_type,
        cor_module_type,
        cor_site_type.c.id_type_site == cor_module_type.c.id_type_site,
    ),
    foreign_keys=[cor_site_type.c.id_base_site, cor_module_type.c.id_module],
    lazy="select",
    viewonly=True,
)

TMonitoringModules.visits = DB.relationship(
    TMonitoringVisits,
    lazy="select",
    primaryjoin=(TMonitoringModules.id_module == TMonitoringVisits.id_module),
    foreign_keys=[TMonitoringVisits.id_module],
    cascade="all",
    overlaps="sites,sites_group,module",
)


# add sites_group relationship to TMonitoringSites

TMonitoringSites.sites_group = DB.relationship(
    TMonitoringSitesGroups,
    primaryjoin=(TMonitoringSitesGroups.id_sites_group == TMonitoringSites.id_sites_group),
    cascade="all",
    lazy="select",
    uselist=False,
    overlaps="sites",
)

TMonitoringSitesGroups.visits = DB.relationship(
    TMonitoringVisits,
    primaryjoin=(TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group),
    secondaryjoin=(TMonitoringVisits.id_base_site == TMonitoringSites.id_base_site),
    secondary="gn_monitoring.t_site_complements",
    overlaps="sites,sites_group",
)

TMonitoringSitesGroups.nb_visits = column_property(
    select(func.count(TMonitoringVisits.id_base_site))
    .where(
        TMonitoringVisits.id_base_site == TMonitoringSites.id_base_site,
        TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group,
    )
    .scalar_subquery()
)

# note the alias is mandotory otherwise the where is done on the subquery table
# and not the global TMonitoring table
TMonitoringSitesGroups.geom_geojson = column_property(
    select(func.st_asgeojson(func.st_convexHull(func.st_collect(TBaseSites.geom))))
    .select_from(
        TMonitoringSitesGroups.__table__.alias("subquery").join(
            TMonitoringSites,
            TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group,
        )
    )
    .where(
        TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group,
    )
    .scalar_subquery()
)

# case([(TMonitoringSitesGroups.geom is None, select([func.st_asgeojson(func.st_convexHull(func.st_collect(TBaseSites.geom)))])
#             .select_from(
#                 TMonitoringSitesGroups.__table__.alias("subquery").join(
#                     TMonitoringSites,
#                     TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group,
#                 )
#             )
#             .where(
#                 TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group,
#             )), (TMonitoringSitesGroups.geom is not None,select([func.st_asgeojson(TMonitoringSitesGroups.geom)]))]))
