from contextvars import ContextVar
from contextlib import contextmanager

import marshmallow as ma
from cel_expr_python.cel import NewEnv, Type
from google.protobuf import any_pb2, descriptor_pb2, descriptor_pool, message_factory
from marshmallow import ValidationError, fields, post_load

JSON_TYPES = [
    type(None),
    int,
    float,
    bool,
    str,
]


def compile_cel_expression(env, expression):
    """
    Compile une expression dans un environnement typé (variables déclarées), vérifie son retour
    booléen (ou un type dynamique), et renvoie l’expression compilée.
    """
    try:
        compiled = env.compile(expression)
    except RuntimeError as e:
        raise ValidationError(f"Expression CEL invalide : {e}")
    return_type = compiled.return_type()
    if return_type not in (Type.BOOL, Type.DYN):
        raise ValidationError(
            f"Expression CEL non booléenne : elle renvoie '{return_type.name()}'"
        )
    return compiled


def _checked_expr_class():
    """
    Message `cel.expr.CheckedExpr`, limité aux champs utilisés. cel-expr-python n’expose pas ses
    définitions protobuf, d’où ce descripteur.

    Extrait de `proto/cel/expr/checked.proto` (google/cel-spec, licence Apache 2.0,
    https://github.com/google/cel-spec/blob/master/proto/cel/expr/checked.proto) :
    `reference_map` (champ 2, `map<int64, Reference>`) et `Reference.name` (champ 1), avec les
    mêmes numéros de champs et types. Vérifié sur la version `master` du dépôt. Le descripteur
    est écrit à la main d’après ce fichier, mais est censé être semblable à la sortie Python de
    `protoc` pour ce fichier (`checked_pb2`) : les champs utilisés doivent avoir les mêmes
    numéros et types.
    """
    field = descriptor_pb2.FieldDescriptorProto
    proto = descriptor_pb2.FileDescriptorProto(
        name="cel_checked_subset.proto", package="cel.expr", syntax="proto3"
    )
    reference = proto.message_type.add(name="Reference")
    reference.field.add(name="name", number=1, type=field.TYPE_STRING)
    checked = proto.message_type.add(name="CheckedExpr")
    entry = checked.nested_type.add(name="ReferenceMapEntry")
    entry.options.map_entry = True
    entry.field.add(name="key", number=1, type=field.TYPE_INT64)
    entry.field.add(
        name="value", number=2, type=field.TYPE_MESSAGE, type_name=".cel.expr.Reference"
    )
    checked.field.add(
        name="reference_map",
        number=2,
        type=field.TYPE_MESSAGE,
        label=field.LABEL_REPEATED,
        type_name=".cel.expr.CheckedExpr.ReferenceMapEntry",
    )
    pool = descriptor_pool.DescriptorPool()
    pool.Add(proto)
    pool.AddSerializedFile(any_pb2.DESCRIPTOR.serialized_pb)
    return message_factory.GetMessageClass(pool.FindMessageTypeByName("cel.expr.CheckedExpr"))


CheckedExpr = _checked_expr_class()


def cel_used_variables(compiled):
    """
    Noms des variables référencées par une expression compilée (avec vérification de types).

    `serialize()` renvoie un `google.protobuf.Any` contenant un `CheckedExpr` ; sa
    `reference_map` associe à chaque nœud une `Reference`, dont le `name` est renseigné pour les
    identifiants résolus (variables déclarées). Les fonctions et opérateurs n’ont pas de `name`.
    """
    any_message = any_pb2.Any()
    any_message.ParseFromString(compiled.serialize())
    checked = CheckedExpr()
    checked.ParseFromString(any_message.value)
    return {reference.name for reference in checked.reference_map.values() if reference.name}


def cel_entity_variables(entity):
    """
    Noms des variables (`fields.<nom>`) utilisées par l’ensemble des expressions CEL d’une entité :
    `required_cel`, `validate_cel` et `hidden_cel` des champs, et `validate_cel` de l’entité.
    Renvoie une liste triée.
    """
    compiled = []
    for field in entity.data["fields"].values():
        compiled.append(field["compiled_required_cel"])
        compiled.append(field["compiled_hidden_cel"])
        compiled.extend(expression for expression, _ in field["compiled_validate_cel"])
    compiled.extend(expression for expression, _ in entity.data["compiled_validate_cel"])
    variables = set()
    for expression in compiled:
        if expression is not None:
            variables |= cel_used_variables(expression)
    return sorted(variables)


class CELValidationSchema(ma.Schema):
    class Meta:
        unknown = ma.RAISE

    condition = fields.Str(required=True)
    message = fields.Str()

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
