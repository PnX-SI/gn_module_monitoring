from flask import g
from flask_sqlalchemy import BaseQuery
from sqlalchemy import Unicode, and_, Unicode, func, or_, false
from sqlalchemy.types import DateTime
from werkzeug.datastructures import MultiDict
from geonature.core.gn_permissions.tools import get_scopes_by_action
import gn_module_monitoring.monitoring.models as Models


class Query(BaseQuery):
    def _get_entity(self, entity):
        if hasattr(entity, "_entities"):
            return self._get_entity(entity._entities[0])
        return entity.entities[0]

    def _get_model(self):
        # When sqlalchemy is updated:
        # return self._raw_columns[0].entity_namespace
        # But for now:
        entity = self._get_entity(self)
        return entity.c

    def filter_by_params(self, params: MultiDict = None):
        model = self._get_model()
        and_list = []
        for key, value in params.items():
            column = getattr(model, key)
            if isinstance(column.type, Unicode):
                and_list.append(column.ilike(f"%{value}%"))
            elif isinstance(column.type, DateTime):
                and_list.append(func.to_char(column, "YYYY-MM-DD").ilike(f"%{value}%"))
            else:
                and_list.append(column == value)
        and_query = and_(*and_list)
        return self.filter(and_query)

    def sort(self, label: str, direction: str):
        model = self._get_model()
        order_by = getattr(model, label)
        if direction == "desc":
            order_by = order_by.desc()

        return self.order_by(order_by)

    def _get_cruved_scope(self, module_code=None,object_code=None, user=None):
        if user is None:
            user = g.current_user
        cruved = get_scopes_by_action(
            id_role=user.id_role, module_code=module_code, object_code=object_code
        )
        return cruved

    def _get_read_scope(self, module_code="MONITORINGS", object_code=None, user=None):
        if user is None:
            user = g.current_user
        cruved = get_scopes_by_action(
            id_role=user.id_role, module_code=module_code, object_code=object_code
        )
        return cruved["R"]

    def filter_by_readable(self, module_code="MONITORINGS", object_code=None, user=None):
        """
        Return the object where the user has autorization via its CRUVED
        """
        return self.filter_by_scope(
            self._get_read_scope(module_code=module_code, object_code=object_code, user=user)
        )


class SitesQuery(Query):
    def filter_by_scope(self, scope, user=None):
        if user is None:
            user = g.current_user
        if scope == 0:
            self = self.filter(false())
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
            self = self.filter(or_(*ors))
        return self


class SitesGroupsQuery(Query):
    def filter_by_scope(self, scope, user=None):
        if user is None:
            user = g.current_user
        if scope == 0:
            self = self.filter(false())
        elif scope in (1, 2):
            ors = [
                Models.TMonitoringSitesGroups.id_digitiser == user.id_role,
            ]
            # if organism is None => do not filter on id_organism even if level = 2
            if scope == 2 and user.id_organisme is not None:
                ors += [
                    Models.TMonitoringSitesGroups.digitiser.has(id_organisme=user.id_organisme)
                ]
            self = self.filter(or_(*ors))
        return self


class VisitQuery(Query):
    def filter_by_scope(self, scope, user=None):
        # Problem pas le même comportement que pour les sites et groupes de site
        if user is None:
            user = g.current_user
        if scope == 0:
            self = self.filter(false())
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
            self = self.filter(or_(*ors))
        return self


class ObservationsQuery(Query):
    def filter_by_scope(self, scope, user=None):
        if user is None:
            user = g.current_user
        if scope == 0:
            self = self.filter(false())
        elif scope in (1, 2):
            ors = [
                Models.TObservations.id_digitiser == user.id_role,
            ]
            # if organism is None => do not filter on id_organism even if level = 2
            if scope == 2 and user.id_organisme is not None:
                ors += [Models.TObservations.digitiser.has(id_organisme=user.id_organisme)]
            self = self.filter(or_(*ors))
        return self
