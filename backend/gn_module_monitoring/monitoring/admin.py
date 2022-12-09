from flask_admin.contrib.sqla import ModelView
from geonature.core.admin.admin import CruvedProtectedMixin


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
