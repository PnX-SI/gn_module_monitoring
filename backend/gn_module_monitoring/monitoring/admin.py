from flask import json

from flask_admin.contrib.sqla import ModelView
from flask_admin.form import fields

from sqlalchemy import exists
from wtforms.validators import ValidationError

from geonature.utils.env import DB
from geonature.core.admin.admin import CruvedProtectedMixin

from pypnnomenclature.models import BibNomenclaturesTypes, TNomenclatures

from geonature.core.gn_monitoring.models import BibTypeSite
from gn_module_monitoring.monitoring.utils import json_formatter

SITE_TYPE = "TYPE_SITE"


class Unique:
    """validator that checks field uniqueness"""

    def __init__(self, model, field, compare_field, message=None):
        self.model = model
        self.field = field
        self.compare_field = compare_field
        if not message:
            message = "A type is already created with this nomenclature"
        self.message = message

    def __call__(self, form, field):
        if field.object_data == field.data:
            return
        if DB.session.scalar(
            exists()
            .where(getattr(self.model, self.field) == getattr(field.data, self.compare_field))
            .select()
        ):
            raise ValidationError(self.message)


class JSONField(fields.JSONField):
    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        elif self.data:
            return json.dumps(self.data, ensure_ascii=False, indent=2)
        else:
            return ""


class BibTypeSiteView(CruvedProtectedMixin, ModelView):
    """
    Surcharge de l'administration des types de sites
    """

    module_code = "MONITORINGS"
    object_code = "TYPES_SITES"

    def __init__(self, session, **kwargs):
        # Référence au model utilisé
        super(BibTypeSiteView, self).__init__(BibTypeSite, session, **kwargs)

    def get_only_nomenclature_asc():
        return (
            DB.session.query(TNomenclatures)
            .join(TNomenclatures.nomenclature_type)
            .filter(BibNomenclaturesTypes.mnemonique == SITE_TYPE)
            .order_by(TNomenclatures.label_fr.asc())
        )

    def get_label_fr_nomenclature(x):
        return x.label_fr

    def list_label_nomenclature_formatter(view, _context, model, _name):
        return model.nomenclature.label_fr

    # Nom de colonne user friendly
    column_labels = dict(nomenclature="Types de site")
    # Description des colonnes
    column_descriptions = dict(nomenclature="Nomenclature de type de site à choisir")

    column_hide_backrefs = False

    form_args = dict(
        nomenclature=dict(
            query_factory=get_only_nomenclature_asc,
            get_label=get_label_fr_nomenclature,
            validators=[Unique(BibTypeSite, "id_nomenclature_type_site", "id_nomenclature")],
        )
    )
    form_overrides = {"config": JSONField}
    column_list = ("nomenclature", "config")
    column_formatters = dict(nomenclature=list_label_nomenclature_formatter, config=json_formatter)
    form_excluded_columns = "sites"
