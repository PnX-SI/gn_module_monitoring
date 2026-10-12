import marshmallow as ma
from marshmallow import ValidationError, fields


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
