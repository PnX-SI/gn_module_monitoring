from contextvars import ContextVar
from contextlib import contextmanager

import marshmallow as ma
from cel_expr_python.cel import NewEnv
from marshmallow import ValidationError, fields, post_load, validates

JSON_TYPES = [
    type(None),
    int,
    float,
    bool,
    str,
]

CEL_ENV = NewEnv()


def check_cel_syntax(expression):
    # Seule la syntaxe est vérifiée : les variables ne sont pas connues à ce stade
    try:
        CEL_ENV.compile(expression, disable_check=True)
    except RuntimeError as e:
        raise ValidationError(f"Expression CEL invalide : {e}")


class CELValidationSchema(ma.Schema):
    class Meta:
        unknown = ma.RAISE

    condition = fields.Str(required=True)
    message = fields.Str()

    @validates("condition")
    def validate_condition(self, value, **kwargs):
        check_cel_syntax(value)

    @post_load
    def set_default_message(self, data, **kwargs):
        if "message" not in data:
            data["message"] = f"The following condition is not met: {data["condition"]}"
        return data


class CELValidationsField(fields.Field):
    """
    Ce champs attends une liste d’object {"condition": str, "message": str}  avec "condition"
    une condition CEL et "message" un message d’erreur si la condition n’est pas remplie.

    Si ne reçoit pas une liste, convertie en list.
    Si les items ne sont pas des objets mais des strings, on considère qu’il s’agit de
    la condition et on utilise un messgae par défaut (voir CELValidationSchema).
    """

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        items = value if isinstance(value, list) else [value]
        return [
            CELValidationSchema().load({"condition": item} if isinstance(item, str) else item)
            for item in items
        ]


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
        if isinstance(value, dict):
            return ValueLabelSchema().load(value)
        if type(value) in JSON_TYPES:
            return {"value": value, "label": value}
        raise ValidationError("Must be a json type or a dict.")


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
