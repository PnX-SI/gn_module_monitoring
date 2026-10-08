from flask import current_app
from .form_enricher import enrich_monitoring_form_def
from gn_module_monitoring.modules.repositories import (
    get_modules,
)
from geonature.core.gn_permissions.tools import get_scopes_by_action


def enrich_config_from_remote(form_def_dict, _=None):
    try:
        modules = get_modules()
        # modules_out = []
        modules_out = [enrich_module(module) for module in modules if has_read_permission(module)]
    except Exception as e:
        current_app.logger.warning(f"Erreur lecture modules monitoring : {e}")
        modules_out = []

    return enrich_monitoring_form_def(form_def_dict or {}, modules_out)


def enrich_module(module):
    module_out = module.as_dict(depth=0)
    module_out["cruved"] = get_scopes_by_action(
        module_code=module.module_code, object_code="MONITORINGS_MODULES"
    )
    return module_out


def has_read_permission(module):
    """Retourne True si l'utilisateur a le droit de lecture (R > 0) sur le module."""
    try:
        scopes = get_scopes_by_action(
            module_code=module.module_code, object_code="MONITORINGS_MODULES"
        )
        return scopes.get("R", 0) > 0
    except Exception as e:
        current_app.logger.warning(
            f"[Monitoring] Erreur permission module {module.module_code} : {e}"
        )
        return False
