"""The Multi-Zone Manifold -- 3 zones x 3 qubits = 9 qubits total, proving
umwelt's CumulantCluster scaling beyond a single reactor.

Returns a plain {zone_name: CumulantCluster} dict rather than attaching to
host.engine.field.clusters -- host.engine raises RuntimeError on a bare
GameHost until register_world(spec) is called with a real DomainSpec, which
these hand-built clusters don't have (same reasoning as scenario/reactor.py
and repl/terminal.py in Phase 12).
"""
from typing import Dict

from umwelt.substrate.cumulant_cluster import CumulantCluster

ZONE_ROLES = {
    "Reactor_Core": ["core_valve", "core_pump", "core_sensor"],
    "Navigation": ["nav_strut", "nav_thruster", "nav_lens"],
    "Life_Support": ["ls_filter", "ls_blower", "ls_monitor"],
}


def build_ship_manifold() -> Dict[str, CumulantCluster]:
    """
    Constructs a 3-zone, 9-qubit Fledgeling Ship Manifold.
    Each zone represents a 3-qubit (Father, Son, Spirit) Septacrypt subsystem.
    """
    clusters: Dict[str, CumulantCluster] = {}

    for zone_name, roles in ZONE_ROLES.items():
        cluster = CumulantCluster(zone_name=zone_name, qubit_roles=roles, gamma=0.03, dt=0.1)

        # Intra-zone entanglement
        zz_couplings = {(0, 1): 0.6, (1, 2): 0.4}
        h_fields = [[0.15, 0.0, 0.0], [0.15, 0.0, 0.0], [0.1, 0.0, 0.0]]

        cluster.set_couplings(h_fields=h_fields, zz=zz_couplings)
        clusters[zone_name] = cluster

    return clusters
