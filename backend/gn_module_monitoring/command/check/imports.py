from textwrap import indent

import click

from gn_module_monitoring.command.imports.protocol import (
    compute_protocol_diff,
    format_protocol_diff,
    is_protocol_diff_empty,
)
from gn_module_monitoring.command.utils import apply_protocol_diff
from gn_module_monitoring.modules import get_module


def check_module_import(module_code: str, fix: bool) -> int:
    """
    Section « Protocole d'import » de `check` : compare la configuration du module à la base
    (bib_fields, bib_entities, table transitoire), avec le même calcul que `process_import`.

    Sans `fix`, rien n'est écrit. Avec `fix`, les écarts sont appliqués après confirmation
    (même `apply_protocol_diff` que `process_import`).

    Returns
    -------
    int
        Nombre d'anomalies restantes (0 si le protocole est à jour, ou corrigé avec `fix`).
    """
    click.echo("Configuration dans le module d’import … ", nl=False)
    module_data = {"module": get_module(module_code).entities["module"].data}
    try:
        diff = compute_protocol_diff(module_code, module_data)
    except Exception as e:
        click.secho("[ERR]", fg="red")
        click.echo(indent(f"Comparaison impossible : {e}", prefix="      "))
        return 1

    if is_protocol_diff_empty(diff):
        click.secho("[OK]", fg="green")
        return 0

    click.secho("[ERR]", fg="red")
    for line in format_protocol_diff(diff):
        click.echo(indent(f"- {line}", prefix="      "))

    if not fix:
        return 1

    if apply_protocol_diff(module_data, module_code, diff):
        click.secho("      Configuration du module d’import mise à jour", fg="green")
        return 0
    click.secho("      Configuration du module d’import non mise à jour", fg="red")
    return 1
