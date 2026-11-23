import click

from flask.cli import with_appcontext
from sqlalchemy.sql import select
from sqlalchemy import exists
from marshmallow import ValidationError

from geonature.utils.env import DB
from geonature.core.gn_synthese.models import TSources
from geonature.core.gn_synthese.utils.process import import_from_table
from geonature.core.gn_commons.models import TModules
from geonature.core.imports.models import Destination

from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.modules import get_module, invalidate_module
from gn_module_monitoring.config.utils import (
    get_monitorings_path,
    get_monitoring_module,
    is_module_configured,
    monitoring_module_config_path,
)
from gn_module_monitoring.command.check import run_check
from gn_module_monitoring.command.nomenclature import add_nomenclature
from gn_module_monitoring.command.permissions import process_available_permissions
from gn_module_monitoring.command.sql import process_sql_files
from gn_module_monitoring.command.utils import (
    available_modules,
    installed_modules,
    process_module_import,
    process_update_module_import,
    remove_monitoring_module,
    check_module_code_name,
)


@click.command("process_sql")
@click.argument("module_code", type=str, required=False, default="")
@with_appcontext
def cmd_process_sql(module_code):
    """
    Met à jour les paramètres de configuration pour un module
        Fichiers sql synthese et export
    """
    if module_code:
        modules = [module_code]
    else:
        modules = [module["module_code"] for module in installed_modules()]

    for module in modules:
        # process Synthese
        process_sql_files(dir=None, module_code=module, depth=1)
        # process Exports
        process_sql_files(dir="exports/csv", module_code=module, depth=None, allowed_files=None)


@click.command("install")
@click.argument("module_code", type=str, required=False, default=None)
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

    # Check module code_name
    module_code = None if module_code in ("", None) else module_code
    module_config_dir_path = ""
    if module_code and not check_module_code_name(module_code):
        click.secho(
            f"Le nom du module {module_code} n'est pas valide !",
            fg="red",
        )
        return

    if module_code in [module["module_code"] for module in installed_modules()]:
        click.secho(f"Le module {module_code} est déjà installé !\n")
        return

    if module_code:
        module_config_dir_path = monitoring_module_config_path(module_code)

    if not (module_code and (module_config_dir_path / "module.json").is_file()):
        if module_code:
            click.secho(
                f"Le module {module_code} n'est pas présent dans le dossier {module_config_dir_path}",
                fg="red",
            )
        click.secho(f"\nModules disponibles :\n")
        for module in available_modules():
            click.secho(
                f"- {module['module_code']}: {module['module_label']} ({module['module_desc']})\n"
            )
        click.secho(f"\nModules installés :\n")
        for module in installed_modules():
            click.secho(
                f"- {module['module_code']}: {module['module_label']} ({module['module_desc']})\n"
            )
        return

    try:
        get_module(module_code)  # config v3 : lève une erreur si la configuration est invalide
    except ValidationError as e:
        click.echo("Erreurs détectées dans les fichiers de configuration:")
        click.echo(f"- {e}")
        click.echo("Installation annulée")
        return

    monitoring_module = get_module(module_code)

    click.secho(f"Installation du sous-module monitoring {module_code}")

    # process Synthese
    process_sql_files(dir=None, module_code=module_code, depth=1)
    # process Exports
    process_sql_files(dir=None, module_code=module_code, depth=None, allowed_files=None)

    module_desc = monitoring_module.entities["module"].data.get("module_desc")
    module_label = monitoring_module.entities["module"].data.get("module_label")
    synthese_object = (
        monitoring_module.get("synthese_object") or "observation"
    )  # pour retrouver la page depuis la synthese

    if not (module_desc and module_label):
        click.secho(
            f"Veuillez renseigner les valeurs des champs module_label \
et module_desc dans le fichier {module_config_dir_path}/module.json",
            fg="red",
        )
        return

    module_data = {
        "module_picto": "fa-puzzle-piece",
        **monitoring_module.entities["module"].data,
        "module_code": module_code,
        "module_path": "{}/module/{}".format(get_monitorings_path(), module_code),
        "active_frontend": False,
        "active_backend": False,
        "type": "monitoring_module",
    }

    click.secho("ajout du module {} en base".format(module_code))
    if not DB.session.scalar(
        exists(TMonitoringModules).where(TMonitoringModules.module_code == module_code).select()
    ):
        module = TMonitoringModules()
        module.from_dict(module_data)
        DB.session.add(module)
        DB.session.commit()

    # Ajouter les permissions disponibles
    process_available_permissions(module_code, session=DB.session)
    DB.session.commit()

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
            get_monitorings_path(), module_code, synthese_object
        ),
    }

    source = TSources(**source_data)
    DB.session.add(source)
    DB.session.commit()

    invalidate_module(module_code)
    click.secho(f"Sous-module monitoring '{module_code}' installé", fg="green")
    return


@click.command("process_import")
@click.argument("module_code", type=str, required=True)
@with_appcontext
def cmd_add_update_import_on_protocole(module_code):
    module_code_installed = [module["module_code"] for module in installed_modules()]
    if not module_code in module_code_installed:
        raise KeyError(
            f"Le module {module_code} n'est pas installé. Pour pouvoir importer dans ce protocole, vous devez d'abord l'installer !"
        )

    module_entity = get_module(module_code).entities["module"].data
    # Vérification de la conformité des fichier json
    try:
        get_module(module_code)  # config v3 : lève une erreur si la configuration est invalide
    except ValidationError as e:
        click.echo("Erreurs détectées dans les fichiers de configuration:")
        click.echo(f"- {e}")
        click.echo("Mise à jour de l'import annulée")
        return

    if not is_module_configured(get_monitoring_module(module_code)):
        click.secho(
            f"Le module {module_code} n'est pas configuré ! ",
            fg="red",
        )
        return

    module_data = {
        "module_picto": "fa-puzzle-piece",
        **module_entity,
        "module_code": module_code,
        "module_path": "{}/module/{}".format(get_monitorings_path(), module_code),
        "active_frontend": False,
        "active_backend": False,
        "type": "monitoring_module",
    }

    try:
        destination_exists = DB.session.scalar(
            exists(Destination).where(Destination.code == module_code).select()
        )
        # Vérifier si le module existe
        # Le module est installé (vérifié plus haut) : seul compte l'existence de la destination
        if destination_exists:
            # Effectuer une mise à jour (diff affiché, puis confirmation)
            try:
                click.secho(f"Mise à jour du module {module_code}")
                state = process_update_module_import({"module": module_entity}, module_code)
                invalidate_module(module_code)
                if state is None:
                    # rien à faire : le message est déjà affiché
                    return
                if state:
                    click.secho(f"Module {module_code} mis à jour", fg="green")
                else:
                    click.secho(f"La mise à jour du module {module_code} à été annulée", fg="red")
            except Exception:
                return
            return
    except Exception:
        pass

    # Ajouter les destinations disponibles
    process_module_import(module_data)
    DB.session.commit()
    invalidate_module(module_code)


@click.command("update_module_available_permissions")
@click.argument("module_code", required=False, default="")
@with_appcontext
def cmd_process_available_permission_module(module_code):
    """
       Mise à jour (uniquement insertion) des objets permissions associés au module
       Défini par le paramètre permission_objects du fichier module.json

    Args:
        module_code ([string]): code du sous module

    """
    if module_code:
        modules = [module_code]
    else:
        modules = [module["module_code"] for module in installed_modules()]

    for module in modules:
        process_available_permissions(module, session=DB.session)
    DB.session.commit()


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
    module = DB.session.execute(
        select(TModules).where(TModules.module_code == module_code)
    ).scalar_one()
    table_name = "v_synthese_{}".format(module_code)
    import_from_table(
        "gn_monitoring",
        table_name,
        "id_module",
        module.id_module,
        offset,
    )
    click.secho("DONE", fg="green")


def check_filter_options(option_name, param_name, description):
    def decorator(func):
        func = click.option(
            option_name,
            param_name,
            is_flag=True,
            help=f"Contrôle les {description}",
        )(func)
        func = click.option(
            f"{option_name}-pk",
            f"{param_name}_pks",
            type=int,
            multiple=True,
            help=f"Contrôle uniquement certains enregistrements (répétable) ({description})",
        )(func)
        func = click.option(
            f"{option_name}-field",
            f"{param_name}_fields",
            multiple=True,
            help=f"Contrôle uniquement certains champs (répétable) ({description})",
        )(func)
        return func

    return decorator


@click.command("check")
@click.argument(
    "module_code",
    type=str,
    required=False,
)
@click.option("--data/--no-data", "check_data", default=False, help="Vérifie les données")
@check_filter_options("--site-group", "site_group", "groupes de sites")
@check_filter_options("--site", "site", "sites")
@check_filter_options("--visit", "visit", "visites")
@check_filter_options("--observation", "observation", "observations")
@check_filter_options("--observation-detail", "observation_detail", "détails d’observation")
@click.option(
    "--strict/--tolerant",
    "strict",
    default=False,
    help="Mode strict : contrôle de manière plus exigeant la configuration en refusant certaines incohérences et syntaxes obsolètes.",
)
@click.option(
    "--fix",
    is_flag=True,
    default=False,
    help="Propose de corriger les anomalies détectées",
)
@with_appcontext
def cmd_check(module_code, strict, fix, check_data, **data_filters):
    """
    Contrôle la configuration, les nomenclatures et les données des
    protocoles de suivi.

    Les fichiers de configuration de tous les protocoles (installés ou non)
    sont contrôlés. Les nomenclatures et les données ne sont contrôlées que
    pour les protocoles installés.

    Les contrôles de données peuvent être limité à une catégorie de données :
    groupe de site, site, visite, observation, détails d’observation

    Pour chaque catégorie, il est possible de limiter le contrôle de données à
    certains enregistrements (--<category>-pk) ou à certains champs (--<category>-field).
    """
    run_check(module_code, strict, check_data, data_filters, fix)


commands = [
    cmd_install_monitoring_module,
    cmd_process_available_permission_module,
    cmd_remove_monitoring_module_cmd,
    cmd_add_module_nomenclature_cli,
    cmd_process_sql,
    cmd_check,
    synchronize_synthese,
    cmd_add_update_import_on_protocole,
]
