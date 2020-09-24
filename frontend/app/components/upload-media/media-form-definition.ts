export const mediaFormDefinitionDict = {
    "id_media": {
        "attribut_label": "ID media",
        "type_widget": "number",
        "hidden": true
    },
    "id_table_location": {
        "attribut_label": "ID table location",
        "type_widget": "number",
        "hidden": true
    },
    "uuid_attached_row": {
        "attribut_label": "uuid_attached_row",
        "type_widget": "text",
        "required": true,
        "hidden": true
    },
    "unique_id_media": {
        "attribut_label": "unique_id_media",
        "type_widget": "text",
        "hidden": true
    },
    "title_fr": {
        "attribut_label": "Titre",
        "type_widget": "text",
        "required": true
    },
    "description_fr": {
        "attribut_label": "Description",
        "type_widget": "text",
        "required": true
    },
    "media_url": {
        "attribut_label": "Url",
        "type_widget": "text",
    },
    "media_path": {
        "attribut_label": "Path",
        "type_widget": "text",
        "hidden": true
    },
    "id_nomenclature_media_type": {
        "attribut_label": "Type de média",
        "type_widget": "nomenclature",
        "required": true,
        "code_nomenclature_type": "TYPE_MEDIA"
    }
}
