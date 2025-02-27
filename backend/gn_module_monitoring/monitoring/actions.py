import sqlalchemy as sa

from geonature.core.imports.actions import ImportActions
from geonature.core.imports.models import TImports

from geonature.utils.env import db
from geonature.utils.sentry import start_sentry_child

from gn_module_monitoring.monitoring.models import TMonitoringSites

from bokeh.embed.standalone import StandaloneEmbedJson

import typing


class ImportStatisticsLabels(typing.TypedDict):
    key: str
    value: str


class MonitoringImportActions(ImportActions):
    @staticmethod
    def statistics_labels() -> typing.List[ImportStatisticsLabels]:
        return [
            {"key": "import_count", "value": "Nombre d'observations importées"},
            {"key": "taxa_count", "value": "Nombre de taxons"},
        ]

    # The output of this method is NEVER used
    @staticmethod
    def preprocess_transient_data(imprt: TImports, df) -> set:
        raise NotImplementedError

    @staticmethod
    def check_transient_data(task, logger, imprt: TImports) -> None:
        raise NotImplementedError

    @staticmethod
    def import_data_to_destination(imprt: TImports) -> None:
        raise NotImplementedError

    @staticmethod
    def remove_data_from_destination(imprt: TImports) -> None:
        with start_sentry_child(op="task", description="clean imported data"):
            db.session.execute(
                sa.delete(TMonitoringSites).where(TMonitoringSites.id_import == imprt.id_import)
            )

    @staticmethod
    def report_plot(imprt: TImports) -> StandaloneEmbedJson:
        raise NotImplementedError

    @staticmethod
    def compute_bounding_box(imprt: TImports) -> None:
        raise NotImplementedError
