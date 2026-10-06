from textwrap import indent

import click


class CheckResult:
    def __init__(self, status, result=None, **kwargs):
        self.status = click.style(status, **kwargs)
        self.result = result


def wrap_errors(message, errors):
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
    return (error_count, result)
