"""
Test de bout en bout de `check --fix` sur le protocole d'import d'un module installé.

Vérifie : l'affichage du diff sans écriture (sans `--fix`), l'absence d'écriture quand la
confirmation est refusée, l'application de la correction quand elle est acceptée, et l'absence de
question quand il n'y a pas d'écart. Utilise la base de test (transactions annulées par les
fixtures) ; rien n'est écrit dans la base de dev.
"""

import pytest
from flask import current_app
from sqlalchemy import select, update

from geonature.utils.env import DB
from geonature.core.imports.models import BibFields, Destination, Entity

from gn_module_monitoring.command.cmd import cmd_check

MODULE_CODE = "test"
BROKEN_LABEL = "Libellé altéré par le test"
PROMPT = "Veuillez confirmer"


def _id_destination():
    return DB.session.execute(
        select(Destination.id_destination).filter_by(code=MODULE_CODE)
    ).scalar_one()


def _protocol_snapshot(id_destination):
    """État du protocole en base : bib_fields, bib_entities et libellé de la destination."""
    fields = (
        DB.session.execute(
            select(BibFields.__table__)
            .where(BibFields.id_destination == id_destination)
            .order_by(BibFields.id_field)
        )
        .mappings()
        .all()
    )
    entities = (
        DB.session.execute(
            select(Entity.__table__)
            .where(Entity.id_destination == id_destination)
            .order_by(Entity.id_entity)
        )
        .mappings()
        .all()
    )
    label = DB.session.execute(
        select(Destination.label).where(Destination.id_destination == id_destination)
    ).scalar_one()
    return {
        "fields": [dict(row) for row in fields],
        "entities": [dict(row) for row in entities],
        "label": label,
    }


def _break_field_label(id_destination):
    """Crée un écart contrôlé : libellé d'un bib_field modifié en base de test."""
    with DB.session.begin_nested():
        DB.session.execute(
            update(BibFields.__table__)
            .where(
                BibFields.id_destination == id_destination,
                BibFields.name_field == "s__place_name",
            )
            .values(fr_label=BROKEN_LABEL)
        )


def _field_label(id_destination, name_field="s__place_name"):
    return DB.session.execute(
        select(BibFields.fr_label).where(
            BibFields.id_destination == id_destination,
            BibFields.name_field == name_field,
        )
    ).scalar_one()


def _run_check(args, input_text=None):
    runner = current_app.test_cli_runner()
    return runner.invoke(cmd_check, [MODULE_CODE, *args], input=input_text)


@pytest.mark.usefixtures("install_module_test_with_config")
class TestCheckFixEndToEnd:
    def test_check_without_fix_shows_diff_and_writes_nothing(self):
        id_destination = _id_destination()
        _break_field_label(id_destination)
        before = _protocol_snapshot(id_destination)

        result = _run_check([])

        assert "bib_fields à modifier s__place_name" in result.output
        assert BROKEN_LABEL in result.output
        assert PROMPT not in result.output
        assert _protocol_snapshot(id_destination) == before

    def test_check_fix_refused_writes_nothing(self):
        id_destination = _id_destination()
        _break_field_label(id_destination)
        before = _protocol_snapshot(id_destination)

        result = _run_check(["--fix"], input_text="no\n")

        assert PROMPT in result.output
        assert "Mise à jour annulée, aucune modification effectuée." in result.output
        assert "Configuration du module d’import mise à jour" not in result.output
        assert _protocol_snapshot(id_destination) == before

    def test_check_fix_confirmed_applies_correction(self):
        id_destination = _id_destination()
        original_label = _field_label(id_destination)
        _break_field_label(id_destination)
        assert _field_label(id_destination) == BROKEN_LABEL

        result = _run_check(["--fix"], input_text="yes\n")

        assert PROMPT in result.output
        assert "Configuration du module d’import mise à jour" in result.output
        assert _field_label(id_destination) == original_label

        # Second passage : protocole à jour, pas de nouvelle question
        second = _run_check(["--fix"], input_text="yes\n")

        assert "Configuration dans le module d’import … [OK]" in second.output
        assert PROMPT not in second.output
        assert "bib_fields à modifier" not in second.output

    def test_check_fix_without_diff_asks_nothing(self):
        id_destination = _id_destination()
        before = _protocol_snapshot(id_destination)

        result = _run_check(["--fix"], input_text="no\n")

        assert "Configuration dans le module d’import … [OK]" in result.output
        assert PROMPT not in result.output
        assert _protocol_snapshot(id_destination) == before
