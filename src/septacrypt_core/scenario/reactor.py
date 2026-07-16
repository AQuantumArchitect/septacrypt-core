"""The Entangled Reactor — a real umwelt CumulantCluster (no GameHost/DomainSpec)."""
from umwelt.substrate.cumulant_cluster import CumulantCluster

from .params import REACTOR_DT, REACTOR_GAMMA, REACTOR_H_FIELDS, REACTOR_ROLES, REACTOR_ZZ

ROLES = list(REACTOR_ROLES)

# Convention (matches geometry/atlas.py axis order): valve=father, pump=son, sensor=spirit.


def build_entangled_reactor() -> CumulantCluster:
    """
    Builds a 3-qubit CumulantCluster representing the Repair Station.
    connectivity=None means dense all-pairs ZZ terms are allocated.
    """
    cluster = CumulantCluster(
        zone_name="Repair_Station",
        qubit_roles=list(REACTOR_ROLES),
        gamma=REACTOR_GAMMA,
        dt=REACTOR_DT,
    )
    cluster.set_couplings(h_fields=[list(row) for row in REACTOR_H_FIELDS], zz=dict(REACTOR_ZZ))
    return cluster
