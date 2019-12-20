from ..models.monitoring import TMonitoringSites, TMonitoringModules, CorSiteModule
from geonature.utils.env import DB
from sqlalchemy import text
from sqlalchemy.ext.hybrid import hybrid_property
from ..utils.utils import to_int

from geonature.utils.errors import GeoNatureError


def request_circuit_geom(id_circuit):
    # !! on rajoute 1e-3 a radius sinon bug quand radius = 0 (1 seul point écoute)
    # TODO rajouter test sur dernieres modif de cicuits et points !!!!
    return """
UPDATE gn_monitoring.t_base_sites SET geom = c.geom
    FROM (
    SELECT ST_SIMPLIFY(ST_BUFFER(b.geom, (radius + 1e-3) * 0.1),(radius + 1e-3) * 0.02) as geom
        FROM (
            SELECT geom, (SELECT radius FROM ST_MinimumBoundingRadius(geom))
                FROM (
                    SELECT ST_ConvexHull(ST_Collect(cp.geom)) as geom
                        FROM gn_monitoring.t_base_sites cp
                        JOIN gn_monitoring.t_site_complements sc
                            ON sc.id_base_site = cp.id_base_site
                        JOIN gn_monitoring.t_base_sites c
                            ON c.id_base_site = {0}
                            WHERE sc.data->>'id_parent' = '{0}'
                    )a
            )b
    )c
WHERE id_base_site = {0};
            """.format(id_circuit)


class TCircuitPoints(TMonitoringSites):
    pass

    @hybrid_property
    def id_parent(self):
        if self.data:
            return to_int(self.data['id_parent'])

    @id_parent.expression
    def id_parent(cls):
        if cls.data:
            return cls.data['id_parent'].astext.cast(DB.Integer)

    # @id_parent.setter
    # def id_parent(self, value):
    #     self.data['id_parent'] = DB.cast(value, DB.Integer)
    def check_and_set_geom_circuit(self):

        id_parent = getattr(self, 'id_parent')

        if not id_parent:
            return
        try:
            DB.engine.execute(
                text(
                    request_circuit_geom(id_parent)
                )
            )

        except Exception as e:
            raise GeoNatureError(
                'pb request circuit : {}'
                .format(
                    str(e)
                )
            )


class TCircuits(TMonitoringSites):
    pass

    circuit_points = DB.relation(
        TCircuitPoints,
        primaryjoin=("foreign(TCircuitPoints.id_parent) == TCircuits.id_base_site")
    )


class TModulesCircuit(TMonitoringModules):
    # unmap site
    sites = 0
    circuits = DB.relationship(
        TCircuits,
        secondary='gn_monitoring.cor_site_module',
        primaryjoin=TMonitoringModules.id_module == CorSiteModule.id_module,
        secondaryjoin=TCircuits.id_base_site == CorSiteModule.id_base_site,
        join_depth=0,
        lazy="select",
    )
