import json
from copy import copy

from apptax.taxonomie.models import Taxref
from flask import g
from geonature.core.gn_permissions.tools import get_scopes_by_action
from geonature.utils.env import db
from pypnnomenclature.models import TNomenclatures
from pypnusershub.db.models import User
from ref_geo.models import LAreas
from sqlalchemy import Unicode, and_, false, func, or_, select, true
from sqlalchemy.orm import aliased, class_mapper
from sqlalchemy.sql.expression import Select
from sqlalchemy.types import DateTime
from werkzeug.datastructures import MultiDict

import gn_module_monitoring.monitoring.models as Models


class GnMonitoringGenericFilter:
    @classmethod
    def get_id_name(cls) -> None:
        pk_string = class_mapper(cls).primary_key[0].name
        if hasattr(cls, "id_g") == False:
            pk_value = getattr(cls, pk_string)
            setattr(cls, "id_g", pk_value)
        return pk_string

    @classmethod
    def filter_by_params(cls, query: Select, params: MultiDict = None, **kwargs):
        and_list = [
            true(),
        ]
        params_copy = copy(params)
        for key, value in params_copy.items():
            if hasattr(cls, key):
                column = getattr(cls, key)
                if not hasattr(column, "type"):
                    # is not an attribut
                    pass
                elif isinstance(column.type, Unicode):
                    and_list.append(column.ilike(f"%{value}%"))
                elif isinstance(column.type, DateTime):
                    and_list.append(func.to_char(column, "YYYY-MM-DD").ilike(f"%{value}%"))
                elif key == "id_inventor" and not value.isdigit():
                    join_inventor = aliased(User)
                    query = query.join(join_inventor, cls.inventor)
                    query = query.filter(join_inventor.nom_complet.ilike(f"%{value}%"))
                else:
                    and_list.append(column == value)
                params.pop(key)

        and_query = and_(*and_list)
        return query.where(and_query)

    @classmethod
    def sort(cls, query: Select, label: str, direction: str):
        order_by = getattr(cls, label)
        if direction == "desc":
            order_by = order_by.desc()

        return query.order_by(order_by)

    @classmethod
    def _get_cruved_scope(cls, module_code=None, object_code=None, user=None):
        if user is None:
            user = g.current_user
        cruved = get_scopes_by_action(
            id_role=user.id_role, module_code=module_code, object_code=object_code
        )
        return cruved

    @classmethod
    def _get_read_scope(cls, module_code="MONITORINGS", object_code=None, user=None):
        if user is None:
            user = g.current_user
        cruved = get_scopes_by_action(
            id_role=user.id_role, module_code=module_code, object_code=object_code
        )
        return cruved["R"]

    @classmethod
    def filter_by_readable(
        cls, query: Select, module_code="MONITORINGS", object_code=None, user=None
    ):
        """
        Return the object where the user has autorization via its CRUVED
        """
        return cls.filter_by_scope(
            query=query,
            scope=cls._get_read_scope(module_code=module_code, object_code=object_code, user=user),
        )


class SitesQuery(GnMonitoringGenericFilter):
    @classmethod
    def filter_by_scope(cls, query: Select, scope, user=None):
        if user is None:
            user = g.current_user
        if scope == 0:
            query = query.where(false())
        elif scope in (1, 2):
            ors = [
                Models.TMonitoringSites.id_digitiser == user.id_role,
                Models.TMonitoringSites.id_inventor == user.id_role,
            ]
            # if organism is None => do not filter on id_organism even if level = 2
            if scope == 2 and user.id_organisme is not None:
                ors += [
                    Models.TMonitoringSites.inventor.has(id_organisme=user.id_organisme),
                    Models.TMonitoringSites.digitiser.has(id_organisme=user.id_organisme),
                ]
            query = query.where(or_(*ors))
        return query

    @classmethod
    def filter_by_params(cls, query: Select, params: MultiDict = None, **kwargs):
        if "modules" in params:
            query = query.filter(cls.modules.any(id_module=params["modules"]))
            params.pop("modules")

        if "types_site" in params:
            value = params["types_site"]
            if not isinstance(value, list):
                value = [value]
            if value[0].isdigit():
                query = query.filter(
                    cls.types_site.any(Models.BibTypeSite.id_nomenclature_type_site.in_(value))
                )
            else:
                # HACK gestionnaire des sites
                # Quand filtre sur type de site envoie une chaine de caractère
                params["types_site_label"] = value[0]
        if "types_site_label" in params:
            value = params["types_site_label"]
            join_types_site = aliased(Models.BibTypeSite)
            join_nomenclature_type_site = aliased(TNomenclatures)
            query = query.join(join_types_site, cls.types_site)
            query = query.join(join_nomenclature_type_site, join_types_site.nomenclature)
            query = query.filter(join_nomenclature_type_site.label_default.ilike(f"%{value}%"))

        query = super().filter_by_params(query, params)
        return query

    @classmethod
    def filter_by_specific(
        cls,
        query: Select,
        params: MultiDict = None,
        specific_properties: dict = None,
        **kwargs,
    ):
        """
        Permet d'ajouter des filtres à la requête des sites
        en fonction des propriétés spécifiques définies au niveau du module ou des types de sites

        le principe est pour chaque params (c-a-d filtre) d'extraire le type util et la cardinalité
            et de construire une requête sql en fonction de ces infos

        :param query: requête sql initiale
        :param params: liste des paramètres que l'on souhaite filtrer
        :param specific_properties: Configuration des propriétés spécifiques des sites
        :return: requête sql amendée de filtre
        """
        for param, value in params.items():
            if param in specific_properties:
                type = "text"
                if "type_util" in specific_properties[param]:
                    type = specific_properties[param]["type_util"]
                multiple = False
                if "multiple" in specific_properties[param]:
                    multiple_value = specific_properties[param]["multiple"]
                    if isinstance(multiple_value, bool):
                        multiple = multiple_value
                    else:
                        multiple = json.loads(multiple_value)

                if type in ("nomenclature", "taxonomy", "user", "area"):
                    join_table, join_column, filter_column = cls.get_relationship_clause(type)
                    if multiple:
                        # Si la propriété est de type multiple
                        # Alors jointure sur chaque element de data->'params'
                        # extraction réalisée via fonction jsonb_array_elements_text avec une jointure lateral
                        # utilisation de correlate_except pour ne pas que t_base_site et t_sites_complement
                        #       soient de nouveau dans la clause from
                        subquery_select = (
                            select(
                                [
                                    func.jsonb_array_elements_text(cls.data[param])
                                    .cast(db.Integer)
                                    .label("id")
                                ]
                            )
                            .correlate_except()
                            .lateral()
                        )
                        query = query.join(subquery_select, cls.data[param] != None)
                        query = query.join(
                            join_table,
                            subquery_select.c.id == join_column,
                        )
                    else:
                        # Sinon type non multiple, jointure sur la valeur de data->'params'
                        query = query.join(
                            join_table, cls.data[param].astext.cast(db.Integer) == join_column
                        )
                    # Filtre sur la valeur de la table de jointure
                    query = query.where(filter_column.ilike(f"{value}%"))
                else:
                    # Sinon filtre texte simple
                    query = query.where(cls.data[param].astext.ilike(f"{value}%"))

        return query

    @classmethod
    def get_relationship_clause(
        cls,
        type,
    ):
        join_table = None  # alias de la table de jointure
        join_column = None  # nom de la colonne permettant la jointure entre data et la table
        filter_column = None  # nom de la colonne sur lequel le filtre est appliqué
        if type == "nomenclature":
            join_table = aliased(TNomenclatures)
            join_column = join_table.id_nomenclature
            filter_column = join_table.label_default
        elif type == "taxonomy":
            join_table = aliased(Taxref)
            join_column = join_table.cd_nom
            filter_column = join_table.nom_vern_or_lb_nom
        elif type == "user":
            join_table = aliased(User)
            join_column = join_table.id_role
            filter_column = join_table.nom_complet
        elif type == "area":
            join_table = aliased(LAreas)
            join_column = join_table.id_area
            filter_column = join_table.area_name
        elif type == "habitat":
            pass

        return join_table, join_column, filter_column


class SitesGroupsQuery(GnMonitoringGenericFilter):
    @classmethod
    def filter_by_scope(cls, query: Select, scope, user=None):
        if user is None:
            user = g.current_user
        if scope == 0:
            query = query.where(false())
        elif scope in (1, 2):
            ors = [
                Models.TMonitoringSitesGroups.id_digitiser == user.id_role,
            ]
            # if organism is None => do not filter on id_organism even if level = 2
            if scope == 2 and user.id_organisme is not None:
                ors += [
                    Models.TMonitoringSitesGroups.digitiser.has(id_organisme=user.id_organisme)
                ]
            query = query.where(or_(*ors))
        return query

    @classmethod
    def filter_by_params(cls, query: Select, params: MultiDict = None, **kwargs):
        if "modules" in params:
            value = params["modules"]
            # Cas ou le filtre provient du gestionnaire des groupes de sites.
            # La valeur est passée en chaine de caractère
            if not value.isdigit():
                query = query.filter(
                    cls.modules.any(Models.TMonitoringModules.module_label.ilike(f"%{value}%"))
                )
            else:
                if not isinstance(value, list):
                    value = [value]
                query = query.filter(
                    cls.modules.any(Models.TMonitoringModules.id_module.in_(value))
                )
        query = super().filter_by_params(query, params)

        return query


class VisitQuery(GnMonitoringGenericFilter):
    @classmethod
    def filter_by_scope(cls, query: Select, scope, user=None):
        # Problem pas le même comportement que pour les sites et groupes de site
        if user is None:
            user = g.current_user
        if scope == 0:
            query = query.where(false())
        elif scope in (1, 2):
            ors = [
                Models.TMonitoringVisits.id_digitiser == user.id_role,
                Models.TMonitoringVisits.observers.any(id_role=user.id_role),
            ]
            # if organism is None => do not filter on id_organism even if level = 2
            if scope == 2 and user.id_organisme is not None:
                ors += [
                    Models.TMonitoringVisits.observers.any(id_organisme=user.id_organisme),
                    Models.TMonitoringVisits.digitiser.has(id_organisme=user.id_organisme),
                ]
            query = query.where(or_(*ors))
        return query


class ObservationsQuery(GnMonitoringGenericFilter):
    @classmethod
    def filter_by_scope(cls, query: Select, scope, user=None):
        if user is None:
            user = g.current_user
        if scope == 0:
            query = query.where(false())
        elif scope in (1, 2):
            ors = [
                Models.TMonitoringObservations.id_digitiser == user.id_role,
            ]
            # if organism is None => do not filter on id_organism even if level = 2
            if scope == 2 and user.id_organisme is not None:
                ors += [
                    Models.TMonitoringObservations.digitiser.has(id_organisme=user.id_organisme)
                ]
            query = query.where(or_(*ors))
        return query
