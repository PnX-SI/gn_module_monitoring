from typing import overload, Literal, Any
from textwrap import indent

import click
import marshmallow as ma
from marshmallow import ValidationError, fields


class CheckResult:
    def __init__(self, status, result=None, **kwargs):
        self.status = click.style(status, **kwargs)
        self.result = result


@overload
def wrap_errors(message, errors) -> int: ...


@overload
def wrap_errors(message, errors, return_result: Literal[False]) -> int: ...


@overload
def wrap_errors(message, errors, return_result: Literal[True]) -> tuple[int, Any]: ...


def wrap_errors(message, errors, return_result=False):
    click.echo(f"{message} … ", nl=False)
    nl = False
    error_count = 0
    while True:
        try:
            error = next(errors)
            if not nl:
                nl = True
                click.echo("")
            lines = str(error).splitlines()
            if lines[0]:
                error_count += 1
                click.echo(indent(lines[0], prefix=click.style("[ERR] ", fg="red")))
            for line in lines[1:]:
                click.echo(indent(line, prefix="      "))
        except StopIteration as e:
            result = e.value
            break
    if type(result) == CheckResult:
        assert not nl
        click.echo(result.status)
        result = result.result
    elif error_count == 0:
        assert not nl
        click.secho("[OK]", fg="green")
    if return_result:
        return (error_count, result)
    else:
        return error_count


def get_object_types(tree: dict):
    """
    Retourne la liste des objets du protocole (sites, visites, observations...)
    pour lesquels des données spécifiques sont stockées, en parcourant
    l'arbre des objets défini dans la configuration.
    """

    def iter_tree(tree):
        for object_type, children in (tree or {}).items():
            yield object_type
            if children is not None:
                yield from iter_tree(children)

    object_types = ["module"]
    for object_type in iter_tree(tree):
        if object_type not in object_types:
            object_types.append(object_type)

    return object_types


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
