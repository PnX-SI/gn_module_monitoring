import pytest

from geonature.utils.env import db

from gn_module_monitoring.monitoring.models import TMonitoringMarkingEvent


# TODO: meme fixture que celle présente dans GN à l'exception que c'est TMonitoringMarkingEvent utilisé au lieu de TMarkingEvent
#  et pas les user et module utilisé
@pytest.fixture
def markings(users, monitoring_module, individuals, nomenclature_type_markings):
    user = users["user"]
    markings = []
    for key in individuals:
        markings.append(
            TMonitoringMarkingEvent(
                id_individual=individuals[key].id_individual,
                id_module=monitoring_module.id_module,
                digitiser=user,
                operator=user,
                marking_date="2025-01-01",
                marking_location="Là bas",
                marking_code="0007",
                marking_details="Super super",
                id_nomenclature_marking_type=nomenclature_type_markings.id_nomenclature,
            )
        )

    with db.session.begin_nested():
        db.session.add_all(markings)
        db.session.flush()

    return markings
