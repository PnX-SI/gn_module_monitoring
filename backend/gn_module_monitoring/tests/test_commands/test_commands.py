import pytest
import json
from pathlib import Path

from gn_module_monitoring.command.imports.constant import ValidationFlag
from gn_module_monitoring.command.utils import (
    validate_protocol_changes,
)
from gn_module_monitoring.config.repositories import get_config

from flask import url_for, current_app

from sqlalchemy import func, select, text, inspect

from geonature.utils.env import BACKEND_DIR, DB
from geonature.core.imports.models import BibFields, Destination

from gn_module_monitoring.command.cmd import (
    cmd_remove_monitoring_module_cmd,
    cmd_process_sql,
    cmd_process_available_permission_module,
    cmd_add_module_nomenclature_cli,
    synchronize_synthese,
    cmd_add_update_import_on_protocole,
)
from gn_module_monitoring.command.imports.protocol import get_protocol_data
from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.command.imports.entity import (
    insert_entities,
    insert_entity_field_relations,
)
from gn_module_monitoring.command.imports.fields import delete_bib_fields, insert_bib_field
from sqlalchemy import insert
from geonature.core.imports.models import TImports

from gn_module_monitoring.tests.fixtures.module import install_monitoring_module


class TestCommands:
    def test_install_monitoring_module(self, install_module_test):
        # Installation du module
        # Test Installation
        result = DB.session.execute(
            select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
        ).scalar_one()
        assert result.module_code == "test"

    def test_remove_monitoring_module(self, install_module_test):
        runner = current_app.test_cli_runner()

        # Suppression du module de test
        result = runner.invoke(cmd_remove_monitoring_module_cmd, ["test"])

        # Test suppression
        result = DB.session.execute(
            select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
        ).scalar_one_or_none()
        assert result == None

    def test_process_all_with_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_process_sql, ["test"])
        # Pas de result juste <Result okay>
        assert result.exit_code == 0

    def test_process_all_without_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_process_sql)
        # Pas de result
        assert result.exit_code == 0

    def test_process_available_permission_module_without_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_process_available_permission_module)
        # Pas de result juste <Result okay>
        assert result.exit_code == 0
        assert "Création des permissions pour test" in result.output

    def test_process_available_permission_module_with_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_process_available_permission_module, ["test"])
        # Pas de result juste <Result okay>
        assert result.exit_code == 0
        assert "Création des permissions pour test" in result.output

    def test_process_available_permission_module_bad_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_process_available_permission_module, ["bad_module"])
        # Pas de result juste <Result okay>
        assert result.exit_code == 0
        assert "le module n'existe pas" in result.output

    def test_cmd_add_module_nomenclature_cli(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_add_module_nomenclature_cli)
        # Pas de result juste <Result okay>
        assert result.exit_code == 2
        assert "Missing argument 'MODULE_CODE'" in result.output

    def test_cmd_add_module_nomenclature_cli(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande add_module_nomenclature
        result = runner.invoke(cmd_add_module_nomenclature_cli, ["test"])
        # Pas de result juste <Result okay>
        assert result.exit_code == 0
        assert "nomenclature type TEST_METEO - Météo - already exist" in result.output
        assert "nomenclature METEO_M - Mauvais temps - updated" in result.output
        assert 'probleme de type avec mnemonique="TEST_UNKWONW_TYPE"' in result.output

    def test_synchronize_synthese(self, install_module_test):
        # Installation du module
        # Test de la synchronisation synthese
        # Permet de tester la bonne execution du fichier synthese.sql
        runner = current_app.test_cli_runner()
        result = runner.invoke(synchronize_synthese, ["test"])
        assert result.exit_code == 0

    def test_cmd_add_module_protocol_fields(self, install_module_test_with_config):
        runner = current_app.test_cli_runner()
        result = runner.invoke(cmd_add_update_import_on_protocole, ["test"])
        assert result.exit_code == 0

        destination = DB.session.execute(
            select(Destination).where(Destination.code == "test")
        ).scalar_one()

        assert destination.code == "test"
        assert destination.label == "Monitoring - Test"

        protocol_data, entity_hierarchy_map = get_protocol_data("test", destination.id_destination)
        fields_data = []
        entities = []

        for entity_code, entity_fields in protocol_data.items():
            entities.append(entity_code)
            all_fields = entity_fields.get("generic", []) + entity_fields.get("specific", [])
            for field in all_fields:
                fields_data.append((field["name_field"], field["fr_label"]))

        existing_fields = (
            DB.session.execute(
                select(BibFields).where(BibFields.id_destination == destination.id_destination)
            )
            .scalars()
            .all()
        )
        fields = [(field.name_field, field.fr_label) for field in existing_fields]

        sorted_fields_data = sorted(fields_data)
        sorted_fields = sorted(fields)

        assert set(fields_data) == set(
            fields
        ), f"Expected fields {sorted_fields_data} but got {sorted_fields}"
        assert "observation" in entities
        assert "visit" in entities

        inspector = inspect(DB.engine)
        result = inspector.has_table(destination.table_name, schema="gn_imports")

        assert result == True

        # Test data_type integer
        fields_to_test = {
            "s__altitude_max": ("number", "integer"),
            "s__altitude_min": ("number", "integer"),
            "s__geom": ("textarea", "USER-DEFINED"),
            "s__id_inventor": ("observers", "integer"),
            "s__first_use_date": ("date", "date"),
            "s__types_site": ("datalist", "ARRAY"),
            "s__base_site_name": ("text", "character varying"),
            "s__base_site_code": ("text", "character varying"),
            "s__base_site_description": ("textarea", "text"),
            "s__multiselect": ("multiselect", "ARRAY"),
        }

        # Test qui ne peux pas fonctionner car le field_type est encore numeric dans bib_fields
        for field in existing_fields:
            if field.name_field in fields_to_test.keys():
                assert field.type_field == fields_to_test[field.name_field][0]

        # Test de la table de destination
        query = text(f"""
            SELECT column_name, data_type 
            FROM information_schema."columns" c 
            WHERE 
                table_schema = 'gn_imports'
                AND table_name = '{destination.table_name}';
            """)
        results = DB.session.execute(query).fetchall()
        for result in results:
            if result[0] in fields_to_test.keys():
                assert result[1] == fields_to_test[result[0]][1]

    def test_install_protocol_no_updates(self, install_module_test_with_config):
        runner = current_app.test_cli_runner()
        result = runner.invoke(cmd_add_update_import_on_protocole, ["test"])
        assert result.exit_code == 0
        assert "Le module test est déjà à jour" in result.output

    def test_update_protocol_with_modified_data(self, install_module_test_with_config):
        destination = DB.session.execute(select(Destination).filter_by(code="test")).scalar_one()

        protocol_data, entity_hierarchy_map = get_protocol_data("test", destination.id_destination)

        # Edit field
        for field in protocol_data["site"]["specific"]:
            if field["name_field"] == "s__place_name":
                field["fr_label"] = "Test Modified"
                field["eng_label"] = "Test Modified"
                break

        # New field
        protocol_data["site"]["specific"].append(
            {
                "name_field": "s__new_field",
                "fr_label": "New Field",
                "eng_label": None,
                "type_field": "VARCHAR",
                "mandatory": False,
                "autogenerated": False,
                "display": False,
                "mnemonique": None,
                "source_field": "src_field",
                "dest_field": "dest_field",
                "multi": False,
                "id_destination": destination.id_destination,
                "mandatory_conditions": None,
                "optional_conditions": None,
                "type_field_params": None,
            }
        )

        with DB.session.begin_nested():
            insert_bib_field(protocol_data)

            insert_entities(
                protocol_data, destination.id_destination, entity_hierarchy_map, "test"
            )

            insert_entity_field_relations(
                protocol_data, destination.id_destination, entity_hierarchy_map
            )

            # Delete field
            fields_to_delete = DB.session.execute(
                select(BibFields).where(BibFields.name_field.in_(["profondeur_grotte"]))
            ).fetchall()
            if fields_to_delete:
                delete_bib_fields(fields_to_delete)

        field_test = DB.session.execute(
            select(BibFields).filter_by(name_field="s__place_name")
        ).scalar_one()
        assert field_test.eng_label == "Test Modified"
        assert field_test.fr_label == "Test Modified"

        new_field = DB.session.execute(
            select(BibFields).filter_by(name_field="s__new_field")
        ).scalar_one()
        assert new_field is not None

        profondeur_grotte_field = DB.session.execute(
            select(BibFields).filter_by(name_field="profondeur_grotte")
        ).scalar_one_or_none()
        assert profondeur_grotte_field is None

    def test_update_protocol_invalid_config_data(self, install_module_test_with_config):
        with ModificationProtocolContext("test", run_update_command=True) as context:
            # Modification du fichier de configuration pour le rendre invalide
            site_config_file = context.site_config_file
            site_content = json.loads(site_config_file.read_text())
            site_content["specific"]["profondeur_grotte"]["type_widget"] = "invalid_widget_type"
            site_config_file.write_text(json.dumps(site_content))

            runner = current_app.test_cli_runner()
            result = runner.invoke(cmd_add_update_import_on_protocole, ["test"])
            assert result.exit_code == 0
            assert "Erreurs détectées dans les fichiers de configuration" in result.output

    def test_install_protocol_invalid_fields(self, types_site, users):
        module_code = "test"

        with ModificationProtocolContext(module_code, use_contrib=True) as context:
            # Modification du fichier de configuration pour le rendre invalide
            site_config_file = context.site_config_file
            site_content = json.loads(site_config_file.read_text())
            site_content["specific"]["profondeur_grotte"]["type_widget"] = "invalid_widget_type"
            site_config_file.write_text(json.dumps(site_content))

            # Installation du module de test
            # doit être en echec
            with pytest.raises(
                Exception, match="Erreurs détectées dans les fichiers de configuration"
            ) as e:
                install_monitoring_module(module_code, types_site, users)

        # After restoration by context manager, installation should succeed
        install_monitoring_module(module_code, types_site, users)
        result = DB.session.execute(
            select(TMonitoringModules).where(TMonitoringModules.module_code == module_code)
        ).scalar_one()
        assert result.module_code == module_code

    def test_validate_protocol_changes(self, install_module_test_with_config, users, monkeypatch):

        destination = DB.session.execute(select(Destination).filter_by(code="test")).scalar_one()
        config = get_config("test", force=True)

        flags, _, _ = validate_protocol_changes("test", config)
        assert ValidationFlag.NOTHING in flags

        # Test deletion
        with ModificationProtocolContext("test", run_update_command=True) as context:
            site_config_file = context.site_config_file
            site_content = json.loads(site_config_file.read_text())
            del site_content["specific"]["profondeur_grotte"]
            site_config_file.write_text(json.dumps(site_content))

            flags, _, fields_to_delete = validate_protocol_changes("test", config)
            assert "s__profondeur_grotte" in fields_to_delete[0]["dest_field"]
            assert ValidationFlag.FIELDS in flags

            with DB.session.begin_nested():
                imprt = TImports(destination=destination, authors=[users["user"]])
                DB.session.add(imprt)
                DB.session.flush()
                transient_table = destination.get_transient_table()
                query = insert(transient_table).values(
                    {"id_import": imprt.id_import, "line_no": 3}
                )
                DB.session.execute(query)

            monkeypatch.setattr(
                "gn_module_monitoring.command.utils.ask_confirmation",
                lambda *args, **kwargs: False,
            )
            flags, _, _ = validate_protocol_changes("test", config)
            assert ValidationFlag.INVALID in flags

            monkeypatch.setattr(
                "gn_module_monitoring.command.utils.ask_confirmation", lambda *args, **kwargs: True
            )
            flags, _, _ = validate_protocol_changes("test", config)
            assert ValidationFlag.INVALID not in flags

            monkeypatch.setattr(
                "gn_module_monitoring.command.utils.ask_confirmation", lambda *args, **kwargs: True
            )
            runner = current_app.test_cli_runner()
            result = runner.invoke(cmd_add_update_import_on_protocole, ["test"])
            assert result.exit_code == 0

            transient_table = destination.get_transient_table()
            count = DB.session.scalar(select(func.count("*")).select_from(transient_table))
            assert count == 0


class ModificationProtocolContext:
    """
    Context manager for modifying protocol configuration files.

    Parameters
    ----------
        module_code: str
            The module code
        use_contrib: bool
            If True, uses contrib/{module_code}/site.json path
            If False, uses media/monitorings/{module_code}/site.json path
        run_update_command: bool
            If True, runs cmd_add_update_import_on_protocole on exit
    """

    def __init__(self, module_code, use_contrib=False, run_update_command=False):
        self.module_code = module_code
        self.run_update_command = run_update_command

        if use_contrib:
            path_gn_monitoring = Path(__file__).absolute().parent.parent.parent.parent.parent
            self.site_config_file = path_gn_monitoring / Path(f"contrib/{module_code}/site.json")
        else:
            self.site_config_file = BACKEND_DIR / Path(
                f"media/monitorings/{module_code}/site.json"
            )

        self.init_site_content = self.site_config_file.read_text()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Restauration du fichier de configuration
        self.site_config_file.write_text(self.init_site_content)

        # Run update command if requested
        if self.run_update_command:
            runner = current_app.test_cli_runner()
            result = runner.invoke(cmd_add_update_import_on_protocole, [self.module_code])
            assert result.exit_code == 0
