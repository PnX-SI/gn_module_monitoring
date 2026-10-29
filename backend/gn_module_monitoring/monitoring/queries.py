import json
from copy import copy

from typing import Optional
from apptax.taxonomie.models import Taxref
from flask import g
from geonature.core.gn_permissions.tools import get_scopes_by_action
from geonature.utils.env import db
from pypnnomenclature.models import TNomenclatures
from pypnusershub.db.models import User
from pypn_habref_api.models import Habref
from geonature.core.gn_meta.models import TDatasets
from ref_geo.models import LAreas
from sqlalchemy import Unicode, and_, false, func, or_, select, true, Integer
from sqlalchemy.orm import aliased, class_mapper
from sqlalchemy.sql.expression import Select, BinaryExpression
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
                elif key == "id_digitiser" and not value.isdigit():
                    join_digitiser = aliased(User)
                    query = query.join(join_digitiser, cls.digitiser)
                    query = query.filter(join_digitiser.nom_complet.ilike(f"%{value}%"))
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

    @classmethod
    def filter_by_specific(
        cls,
        query: Select,
        params: MultiDict = None,
        specific_properties: dict = None,
    ):
        """
        Permet d'ajouter les filtres définis dans `params` à la requête SQLA `query`. Les filtres ciblent les propriétés
        spécifiques enregistrées dans le champ JSON `data` du modèle. Les définitions de ces propriétés sont attendues dans
        `specific_properties` telles que présentes dans les configs.

        le principe est pour chaque params (c-a-d filtre) d'extraire le type util et la cardinalité
            et de construire une requête sql en fonction de ces infos

        :param query: requête sql initiale
        :param params: liste des paramètres que l'on souhaite filtrer
        :param specific_properties: Configuration des propriétés spécifiques
        :return: requête sql amendée de filtre
        """
        for param, value in params.items():
            if param not in specific_properties:
                continue

            field_type = specific_properties[param].get("type_util", "text")

            if field_type in ("nomenclature", "taxonomy", "user", "area", "habitat", "dataset"):
                # Vérification des champs exotiques
                value_field = specific_properties[param].get(
                    "value_field_name"
                ) or specific_properties[param].get("keyValue")
                if value_field and value_field != getattr(
                    cls._get_relationship_clause(field_type)[1], "name", None
                ):
                    continue

                query, filter_column = _build_join_for_specific_property(
                    query, cls, param, specific_properties, field_type, is_outer_join=False
                )

                query = query.where(filter_column.ilike(f"{value}%"))
            else:
                query = query.where(cls.data[param].astext.ilike(f"%{value}%"))
        return query

    @classmethod
    def _get_relationship_clause(
        cls,
        type_util: str,
    ) -> tuple[Optional[aliased], Optional[str], Optional[str]]:
        join_table = None  # alias de la table de jointure
        join_column = None  # nom de la colonne permettant la jointure entre data et la table
        filter_column = None  # nom de la colonne sur lequel le filtre est appliqué
        if type_util == "nomenclature":
            join_table = aliased(TNomenclatures)
            join_column = join_table.id_nomenclature
            filter_column = join_table.label_default
        elif type_util == "taxonomy":
            join_table = aliased(Taxref)
            join_column = join_table.cd_nom
            filter_column = join_table.nom_vern_or_lb_nom
        elif type_util == "user":
            join_table = aliased(User)
            join_column = join_table.id_role
            filter_column = join_table.nom_complet
        elif type_util == "area":
            join_table = aliased(LAreas)
            join_column = join_table.id_area
            filter_column = join_table.area_name
        elif type_util == "dataset":
            join_table = aliased(TDatasets)
            join_column = join_table.id_dataset
            filter_column = join_table.dataset_name
        elif type_util == "habitat":
            join_table = aliased(Habref)
            join_column = join_table.cd_hab
            filter_column = join_table.lb_hab_fr

        return join_table, join_column, filter_column


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
            query = query.where(or_(*cls.scope_conditions(scope, user)))
        return query

    @staticmethod
    def scope_conditions(scope, user):
        """Conditions d'appartenance d'une visite à l'utilisateur (scope 1) ou à son organisme (scope 2)"""
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
        return ors

    @classmethod
    def filter_by_params(cls, query: Select, params: MultiDict = None, **kwargs):
        if "id_dataset" in params:
            value = params.pop("id_dataset")
            if not value.isdigit():
                join_dataset = aliased(TDatasets)
                query = query.join(join_dataset, cls.dataset)
                query = query.filter(join_dataset.dataset_name.ilike(f"%{value}%"))
            else:
                query = query.filter(cls.id_dataset == value)

        query = super().filter_by_params(query, params)

        return query

    @classmethod
    def filter_by_params(cls, query: Select, params: MultiDict = None, **kwargs):
        if "id_dataset" in params:
            value = params.pop("id_dataset")
            if not value.isdigit():
                join_dataset = aliased(TDatasets)
                query = query.join(join_dataset, cls.dataset)
                query = query.filter(join_dataset.dataset_name.ilike(f"%{value}%"))
            else:
                query = query.filter(cls.id_dataset == value)

        query = super().filter_by_params(query, params)

        return query


class ObservationsQuery(GnMonitoringGenericFilter):
    @classmethod
    def filter_by_scope(cls, query: Select, scope, user=None):
        if user is None:
            user = g.current_user
        if scope == 0:
            query = query.where(false())
        elif scope in (1, 2):
            # Pas d'objet de permission propre aux observations : celles de la visite font foi
            # (cohérent avec TMonitoringObservations.has_instance_permission)
            query = query.where(or_(*cls.scope_conditions(scope, user)))
        return query

    @staticmethod
    def scope_conditions(scope, user):
        """Observations numérisées par l'utilisateur (ou son organisme) ou rattachées à une visite
        qui lui appartient"""
        ors = [
            Models.TMonitoringObservations.id_digitiser == user.id_role,
            Models.TMonitoringObservations.visit.has(
                or_(*VisitQuery.scope_conditions(scope, user))
            ),
        ]
        # if organism is None => do not filter on id_organism even if level = 2
        if scope == 2 and user.id_organisme is not None:
            ors += [Models.TMonitoringObservations.digitiser.has(id_organisme=user.id_organisme)]
        return ors

    @classmethod
    def filter_by_params(cls, query: Select, params: MultiDict = None, **kwargs):
        if "cd_nom" in params:
            value = params.pop("cd_nom")
            # Cas ou le filtre provient du front
            # La valeur est passée en chaine de caractère
            if value.isdigit():
                query = query.where(Models.TMonitoringObservations.cd_nom == value)
            else:
                join_table = aliased(Taxref)
                join_column = join_table.cd_nom
                filter_column = join_table.nom_vern_or_lb_nom
                query = query.join(
                    join_table, Models.TMonitoringObservations.cd_nom == join_column
                )
                # Filtre sur la valeur de la table de jointure
                query = query.where(filter_column.ilike(f"{value}%"))

        query = super().filter_by_params(query, params)
        return query


class IndividualsQuery(GnMonitoringGenericFilter):
    @classmethod
    def filter_by_scope(cls, query: Select, scope, user=None):
        if user is None:
            user = g.current_user
        if scope == 0:
            query = query.where(false())
        elif scope in (1, 2):
            ors = [
                Models.TMonitoringIndividuals.id_digitiser == user.id_role,
            ]
            # if organism is None => do not filter on id_organism even if level = 2
            if scope == 2 and user.id_organisme is not None:
                ors += [
                    Models.TMonitoringIndividuals.digitiser.has(id_organisme=user.id_organisme)
                ]
            query = query.where(or_(*ors))
        return query

    @classmethod
    def filter_by_params(cls, query: Select, params: MultiDict = None, **kwargs):
        if "cd_nom" in params:
            value = params.pop("cd_nom")
            # Cas ou le filtre provient du front
            # La valeur est passée en chaine de caractère
            if value.isdigit():
                query = query.where(Models.TMonitoringIndividuals.cd_nom == value)
            else:
                join_table = aliased(Taxref)
                join_column = join_table.cd_nom
                filter_column = join_table.nom_vern_or_lb_nom
                query = query.join(join_table, Models.TMonitoringIndividuals.cd_nom == join_column)
                # Filtre sur la valeur de la table de jointure
                query = query.where(filter_column.ilike(f"{value}%"))

        query = super().filter_by_params(query, params)
        return query


class MarkingsQuery(GnMonitoringGenericFilter):
    @classmethod
    def filter_by_scope(cls, query: Select, scope, user=None):
        if user is None:
            user = g.current_user
        if scope == 0:
            query = query.where(false())
        elif scope in (1, 2):
            ors = [
                Models.TMonitoringMarkingEvent.id_digitiser == user.id_role,
                Models.TMonitoringMarkingEvent.id_operator == user.id_role,
            ]
            # if organism is None => do not filter on id_organism even if level = 2
            if scope == 2 and user.id_organisme is not None:
                ors += [
                    Models.TMonitoringMarkingEvent.digitiser.has(id_organisme=user.id_organisme),
                    Models.TMonitoringMarkingEvent.operator.has(id_organisme=user.id_organisme),
                ]
            query = query.where(or_(*ors))
        return query


class ObservationDetailsQuery(GnMonitoringGenericFilter):
    @classmethod
    def filter_by_scope(cls, query: Select, scope, user=None):
        if user is None:
            user = g.current_user
        if scope == 0:
            query = query.where(false())
        elif scope in (1, 2):
            # L'appartenance d'un détail est celle de son observation
            query = query.where(
                Models.TMonitoringObservationDetails.observation.has(
                    or_(*ObservationsQuery.scope_conditions(scope, user))
                )
            )
        return query


def _is_multiple(specific_property: dict) -> bool:
    """
    Extrait la valeur de `multiple` depuis une propriété spécifique.
    Retourne False par défaut si non défini ou invalide.
    """
    if not specific_property:
        return False
    multiple_value = specific_property.get("multiple", False)
    if isinstance(multiple_value, bool):
        return multiple_value
    try:
        return bool(json.loads(multiple_value))
    except (TypeError, ValueError):
        return False


def _build_join_for_specific_property(
    query: Select,
    model,
    param: str,
    specific_properties: dict,
    type_util: str,
    is_outer_join: bool = False,
) -> tuple[Select, BinaryExpression]:
    """
    Construit les jointures nécessaires pour une propriété spécifique (nomenclature, taxonomy, etc.).
    Retourne la requête modifiée et la colonne à utiliser pour le tri ou le filtre.

    :param query: Requête SQLAlchemy initiale.
    :param model: Modèle SQLAlchemy.
    :param param: Nom de la propriété spécifique.
    :param specific_properties: Dictionnaire des propriétés spécifiques.
    :param type_util: Type de la propriété (ex: "nomenclature").
    :param is_outer_join: Si True, utilise outerjoin pour éviter d'exclure les NULL (nécessaire pour le tri).
    :return: Tuple (requête modifiée, colonne pour le tri/filtre).
    """

    def _apply_join(query, target, onclause, is_outer: bool):
        """Applique une jointure (join ou outerjoin) et retourne la nouvelle requête."""
        if is_outer:
            return query.outerjoin(target, onclause)
        else:
            return query.join(target, onclause)

    join_table, join_column, filter_column = model._get_relationship_clause(type_util)
    multiple = _is_multiple(specific_properties.get(param, {}))

    if multiple:
        # Sous-requête pour vérifier si le champ est un tableau
        is_array = func.jsonb_typeof(model.data[param]) == "array"
        subquery_select = (
            select(func.jsonb_array_elements_text(model.data[param]).cast(Integer).label("id"))
            .where(is_array)
            .correlate_except()
            .lateral()
        )
        # Jointure latérale
        query = _apply_join(query, subquery_select, model.data[param] != None, is_outer_join)
        query = _apply_join(query, join_table, subquery_select.c.id == join_column, is_outer_join)
    else:
        # Jointure simple
        query = _apply_join(
            query, join_table, model.data[param].astext.cast(Integer) == join_column, is_outer_join
        )
    return query, filter_column
