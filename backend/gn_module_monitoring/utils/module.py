def get_specific_properties(monitoringClass: object, config: dict, object_type: str):

    return get_specific_properties_from_object_config(monitoringClass, config[object_type])


def get_specific_properties_from_object_config(monitoringClass: object, object_config: dict):

    specific_properties = {
        field_name: field_data
        for field_name, field_data in object_config["fields"].items()
        if not hasattr(monitoringClass, field_name)
    }
    return specific_properties
