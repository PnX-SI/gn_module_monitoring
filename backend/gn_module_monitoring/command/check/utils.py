import json
from typing import overload, Literal, Any
from textwrap import indent

import click
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
            if isinstance(error, (dict, list)):
                error = json.dumps(error, indent=2, ensure_ascii=False, default=str)
            elif not isinstance(error, str):
                error = str(error)

            lines = error.splitlines()
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
