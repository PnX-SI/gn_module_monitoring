import os
from pydoc import cli
import click

from pathlib import Path
from flask.cli import with_appcontext
from sqlalchemy.sql import text

from geonature.utils.env import DB, BACKEND_DIR
from geonature.core.gn_synthese.models import TSources
from geonature.core.gn_synthese.utils.process import import_from_table
from geonature.core.gn_commons.models import TModules


from ..monitoring.models import TMonitoringModules
from ..config.repositories import get_config
from ..config.utils import json_from_file, monitoring_module_config_path
from ..modules.repositories import get_module, get_simple_module

from .utils import (
    process_export_csv,
    insert_permission_object,
    remove_monitoring_module,
    add_nomenclature,
    available_modules,
    installed_modules
)


@click.command("process_all")
@click.argument("module_code", type=str, required=False, default="")
@with_appcontext
def cmd_process_all(module_code):
    """
    Met à jour les paramètres de configuration pour un module
    """
    # process export csv
    process_export_csv(module_code)

@click.command("process_export_csv")
@click.argument("module_code", type=str, required=False, default="")
@with_appcontext
def cmd_process_export_csv(module_code):
    """
    Met à jour les fichiers pour les exports pdf
    """
    process_export_csv(module_code)


@click.command("install")
@click.argument("module_code", type=str, required=False, default="")
@with_appcontext
def cmd_install_monitoring_module(module_code):
    """
    Module de suivi générique : installation d'un sous module

    Commande d'installation
    params :
        - module_config_dir_path (str) : chemin du répertoire
                où se situe les fichiers de configuration du module
        - module_code (str): code du module (par defaut la dernière partie de module_config_dir_path )
    """

    # module_config_dir_path = Path(module_config_dir_path)
    # module_code = module_code or module_config_dir_path.name

    click.secho(f"Installation du sous-module monitoring {module_code}")

    module_config_dir_path = monitoring_module_config_path(module_code)

    if not module_config_dir_path.is_dir():
        available_modules_txt = ", ".join(sorted(available_modules()))
        installed_modules_txt = ", ".join(sorted(installed_modules()))
        click.secho(f"Le module {module_code} n'est pas présent dans le dossier {module_config_dir_path}", fg="red")
        click.secho(f'Modules disponibles : {available_modules_txt}\n')
        click.secho(f"Modules installés : {installed_modules_txt}\n")
        return

    module_monitoring = get_simple_module("module_code", "MONITORINGS")

    try:
        module = get_simple_module("module_code", module_code)
        # test si le module existe
        if module:
            click.secho(f"Le module {module_code} existe déjà", fg="red")
            return
    except Exception:
        pass

    # process export csv
    process_export_csv(module_code)

    config = get_config(module_code, force=True)

    if not config:
        click.secho(
            f"config directory for module {module_code} does not exist",
            fg="red"
        )
        return None

    module_desc = config["module"].get("module_desc")
    module_label = config["module"].get("module_label")
    synthese_object = (
        config.get("synthese_object") or "observation"
    )  # pour retrouver la page depuis la synthese

    if not (module_desc and module_label):
        click.secho(
            f"Veuillez renseigner les valeurs des champs module_label \
et module_desc dans le fichier {module_config_dir_path}/module.json",
            fg="red"
        )
        return

    module_data = {
        "module_picto": "fa-puzzle-piece",
        **config["module"],
        "module_code": module_code,
        "module_path": "{}/module/{}".format(
            module_monitoring.module_path, module_code
        ),
        "active_frontend": False,
        "active_backend": False,
        "type": "monitoring_module"
    }

    click.secho("ajout du module {} en base".format(module_code))
    module = TMonitoringModules()
    module.from_dict(module_data)
    DB.session.add(module)
    DB.session.commit()

    # Insert permission object
    if config["module"].get("permission_objects"):
        id_module = module.id_module
        insert_permission_object(id_module, config["module"].get("permission_objects"))

    #  run specific sql
    if (module_config_dir_path / "synthese.sql").exists:
        click.secho("Execution du script synthese.sql")
        sql_script = module_config_dir_path / "synthese.sql"
        try:
            DB.engine.execute(
                text(
                    open(sql_script, "r")
                    .read()
                    .replace(":'module_code'", "'{}'".format(module_code))
                    .replace(":module_code", "{}".format(module_code))
                ).execution_options(autocommit=True)
            )
        except Exception as e:
            print(e)
            click.secho("Erreur dans le script synthese.sql", fg="red")

    # insert nomenclature
    add_nomenclature(module_code)

    source_data = {
        "name_source": "MONITORING_{}".format(module_code.upper()),
        "desc_source": "Données issues du module de suivi générique (sous-module: {})".format(
            module_label.lower()
        ),
        "entity_source_pk_field": "gn_monitoring.vs_{}.entity_source_pk_value".format(
            module_code.lower()
        ),
        "url_source": "#/{}/object/{}/{}".format(
            module_monitoring.module_path, module_code, synthese_object
        ),
    }

    source = TSources(**source_data)
    DB.session.add(source)
    DB.session.commit()

    # TODO ++++ create specific tables
    click.secho(f"Sous-module monitoring '{module_code}' installé", fg='green')
    return


@click.command("update_permission_objects")
@click.argument("module_code")
@with_appcontext
def cmd_update_perm_module_cmd(module_code):
    """
       Mise à jour (uniquement insertion) des objets permissions associés au module
       Défini par le paramètre permission_objects du fichier module.json

    Args:
        module_code ([string]): code du sous module

    """
    try:
        module = get_module("module_code", module_code)
    except Exception:
        print("le module n'existe pas")
        return
    path_module = monitoring_module_config_path(module_code) / "module.json"

    if not path_module.is_file():
        print(f"Il n'y a pas de fichier {path_module} pour ce module")
        return
    config_module = json_from_file(path_module, None)
    if not config_module:
        print("Il y a un problème avec le fichier {}".format(path_module))
        return

    print(f"Insertion des objets de permissions pour le module {module_code}")
    # Insert permission object
    if "permission_objects" in config_module:
        id_module = module.id_module
        insert_permission_object(id_module, config_module["permission_objects"])
    else:
        print("no permission")


@click.command("remove")
@click.argument("module_code")
@with_appcontext
def cmd_remove_monitoring_module_cmd(module_code):
    """
    Module de suivi générique : suppression d'un sous module

    Commande d'installation
    params :
        - module_code (str): code du module
    """

    print("Remove module {}".format(module_code))
    remove_monitoring_module(module_code)


@click.command("add_module_nomenclature")
@click.argument("module_code")
@with_appcontext
def cmd_add_module_nomenclature_cli(module_code):
    return add_nomenclature(module_code)


@click.command("synchronize_synthese")
@click.argument("module_code")
@click.option("--offset", default=100, help="Nb of data insert at each interation")
@with_appcontext
def synchronize_synthese(module_code, offset):
    """
    Synchronise les données d'un module dans la synthese
    """
    click.secho(f"Start synchronize data for module {module_code} ...", fg="green")
    module = TModules.query.filter_by(module_code=module_code).one()
    table_name = "v_synthese_{}".format(module_code)
    import_from_table(
        "gn_monitoring",
        table_name,
        "id_module",
        module.id_module,
        offset,
    )
    click.secho("DONE", fg="green")


commands = [
    cmd_process_export_csv,
    cmd_install_monitoring_module,
    cmd_update_perm_module_cmd,
    cmd_remove_monitoring_module_cmd,
    cmd_add_module_nomenclature_cli,
    cmd_process_all,
    synchronize_synthese,
]
