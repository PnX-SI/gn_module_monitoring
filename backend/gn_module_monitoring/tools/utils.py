from contextvars import ContextVar
from contextlib import contextmanager

import marshmallow as ma
from marshmallow import ValidationError, fields


class ContextManagedContextVar:
    def __init__(self, name: str, default=None):
        self._var = ContextVar(name, default=default)

    def get(self):
        return self._var.get()

    def set(self, value):
        return self._var.set(value)

    def reset(self, token):
        self._var.reset(token)

    @contextmanager
    def __call__(self, **kwargs):
        current = self.get() or {}
        new = {**current, **kwargs}
        token = self.set(new)
        try:
            yield new
        finally:
            self.reset(token)


schema_context = ContextManagedContextVar("schema_context", default=None)


class ValueLabelSchema(ma.Schema):
    value = fields.Raw(required=True)
    label = fields.Str(required=True)


class ValueLabelField(fields.Field):
    """
    Ce champs permet de spécifier une string, ou un dict {"value": ..., "label": ...}
    """

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, str):
            return {"value": value, "label": value}
        if isinstance(value, dict):
            return ValueLabelSchema().load(value)
        raise ValidationError("Must be a string or a dict.")


class StrOrListStr(fields.Field):
    """
    Ce champs accepte une string ou une liste de string.
    """

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return fields.List(fields.String()).deserialize(value)
        raise ValidationError("Must be a string or a list.")


class MultilineStr(fields.Field):
    """
    Ce champs accepte une string, ou une liste de string qu’il va alors joindre par des fins de ligne.
    """

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "\n".join(fields.List(fields.String()).deserialize(value))
        raise ValidationError("Must be a string or a list.")
