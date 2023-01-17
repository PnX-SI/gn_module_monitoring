from flask_sqlalchemy import BaseQuery
from sqlalchemy import Unicode, and_
from werkzeug.datastructures import MultiDict


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
