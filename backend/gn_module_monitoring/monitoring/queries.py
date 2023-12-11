from flask import g
from sqlalchemy import Unicode, and_, Unicode, func, or_, false, true
from sqlalchemy.orm import Query, load_only, joinedload
from sqlalchemy.types import DateTime
from werkzeug.datastructures import MultiDict


from geonature.core.gn_permissions.tools import get_scopes_by_action
import gn_module_monitoring.monitoring.models as Models


class GnMonitoringGenericFilter:
    @classmethod
    def filter_by_params(cls, query: Query, params: MultiDict = None, **kwargs):
        and_list = [
            true(),
        ]
        for key, value in params.items():
            column = getattr(cls, key)
            if isinstance(column.type, Unicode):
                and_list.append(column.ilike(f"%{value}%"))
            elif isinstance(column.type, DateTime):
                and_list.append(func.to_char(column, "YYYY-MM-DD").ilike(f"%{value}%"))
            else:
                and_list.append(column == value)
        and_query = and_(*and_list)
        return query.where(and_query)

    @classmethod
    def sort(cls, query: Query, label: str, direction: str):
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
        cls, query: Query, module_code="MONITORINGS", object_code=None, user=None
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
    def filter_by_scope(cls, query: Query, scope, user=None):
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


class SitesGroupsQuery(GnMonitoringGenericFilter):
    @classmethod
    def filter_by_scope(cls, query: Query, scope, user=None):
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


class VisitQuery(GnMonitoringGenericFilter):
    @classmethod
    def filter_by_scope(cls, query: Query, scope, user=None):
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
    def filter_by_scope(cls, query: Query, scope, user=None):
        if user is None:
            user = g.current_user
        if scope == 0:
            query = query.where(false())
        elif scope in (1, 2):
            ors = [
                Models.TObservations.id_digitiser == user.id_role,
            ]
            # if organism is None => do not filter on id_organism even if level = 2
            if scope == 2 and user.id_organisme is not None:
                ors += [Models.TObservations.digitiser.has(id_organisme=user.id_organisme)]
            query = query.where(or_(*ors))
        return query
