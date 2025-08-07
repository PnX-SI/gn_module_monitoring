from flask import current_app
import requests
from .form_enricher import enrich_monitoring_form_def


def enrich_config_from_remote(form_def_dict, _=None):
    api_endpoint = current_app.config["API_ENDPOINT"]
    base_url = current_app.config["MONITORINGS"]["MODULE_URL"]
    try:
        response = requests.get(f"{api_endpoint}{base_url}/_internal/modules", timeout=5)
        response.raise_for_status()
        module_codes = response.json()
    except Exception as e:
        current_app.logger.warning(f"Erreur appel modules monitoring : {e}")
        module_codes = []

    return enrich_monitoring_form_def(form_def_dict or {}, module_codes)
