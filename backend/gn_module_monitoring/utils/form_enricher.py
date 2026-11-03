from gn_module_monitoring.config.utils import config_from_files


def enrich_monitoring_form_def(form_def_dict, module_codes):
    enriched_dict = {}

    def get_case_insensitive_key(d: dict, key: str):
        for k, v in d.items():
            if k.lower() == key.lower():
                return v
        return None

    for module in module_codes:
        protocole_code = module["module_code"]
        observation_def = config_from_files("observation", protocole_code)
        protocole_form = get_case_insensitive_key(form_def_dict, protocole_code)
        fields = protocole_form.get("fields_form", [])

        enriched_fields = []
        for field in fields:
            attr = field.get("attribut_name")
            if not attr:
                continue

            obs_def = observation_def.get("specific", {}).get(attr)
            if not obs_def:
                enriched_fields.append(field)
                continue

            enriched = {**obs_def, **field}  # priorité au champ TOML
            enriched_fields.append(enriched)

        enriched_dict[protocole_code] = {"fields_form": enriched_fields}

    return enriched_dict
