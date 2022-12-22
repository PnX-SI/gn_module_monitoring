from flask_admin.contrib.sqla import ModelView
from geonature.core.admin.admin import CruvedProtectedMixin
from geonature.core.gn_commons.models import TNomenclatures
from geonature.utils.env import DB

from gn_module_monitoring.monitoring.models import BibCategorieSite


class BibCategorieSiteView(CruvedProtectedMixin, ModelView):
    """
    Surcharge de l'administration des catégories de sites
    """

    module_code = "MONITORINGS"
    object_code = None

    def __init__(self, session, **kwargs):
        # Référence au model utilisé
        super(BibCategorieSiteView, self).__init__(BibCategorieSite, session, **kwargs)

    def get_only_type_site_asc():
        return (
            DB.session.query(TNomenclatures)
            .filter(TNomenclatures.id_type == 116)
            .order_by(TNomenclatures.label_fr.asc())
        )

    def get_label_fr_nomenclature(x):
        return x.label_fr

    def list_label_site_type_formatter(view, _context, model, _name):
        return [item.label_fr for item in model.site_type]

    # Nom de colonne user friendly
    column_labels = dict(site_type="Type de site")
    # Description des colonnes
    column_descriptions = dict(site_type="Type de site à choisir en lien avec la catégorie")

    column_hide_backrefs = False

    form_args = dict(
        site_type=dict(query_factory=get_only_type_site_asc, get_label=get_label_fr_nomenclature)
    )

    column_list = ("label", "config", "site_type")
    column_formatters = dict(site_type=list_label_site_type_formatter)
