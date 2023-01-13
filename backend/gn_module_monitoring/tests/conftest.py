from geonature.tests.fixtures import *
from geonature.tests.fixtures import _session, app, users

pytest_plugins = [
    "gn_module_monitoring.tests.fixtures.module",
    "gn_module_monitoring.tests.fixtures.site",
    "gn_module_monitoring.tests.fixtures.sites_groups",
    "gn_module_monitoring.tests.fixtures.type_site",
]
