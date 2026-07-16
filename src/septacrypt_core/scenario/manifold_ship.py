"""Multi-zone ship manifold with optional cross-zone soft bridges."""
from __future__ import annotations

from typing import Dict, List, Tuple

from umwelt.substrate.cumulant_cluster import CumulantCluster

from .params import (
    CROSS_ZONE_BRIDGES,
    ZONE_DT,
    ZONE_GAMMA,
    ZONE_H_FIELDS,
    ZONE_ROLES,
    ZONE_ZZ,
)



def build_ship_manifold() -> Dict[str, CumulantCluster]:
    """
    Constructs a 3-zone, 9-qubit Fledgeling Ship Manifold.
    Each zone is a 3-qubit Septacrypt subsystem; bridges couple them softly.
    """
    clusters: Dict[str, CumulantCluster] = {}

    for zone_name, roles in ZONE_ROLES.items():
        cluster = CumulantCluster(
            zone_name=zone_name,
            qubit_roles=list(roles),
            gamma=ZONE_GAMMA,
            dt=ZONE_DT,
        )
        cluster.set_couplings(
            h_fields=[list(row) for row in ZONE_H_FIELDS],
            zz=dict(ZONE_ZZ),
        )
        clusters[zone_name] = cluster

    return clusters


def apply_cross_zone_bridges(
    clusters: Dict[str, CumulantCluster],
    bridges: List[Tuple[str, str, str, str, float]] | None = None,
) -> List[str]:
    """
    Soft-couple zones: nudge destination qubit Bloch-z toward source Bloch-z.

    Uses observe_qubit (partial blend + decorrelation), not a joint Hamiltonian.
    Returns human-readable log lines of applied bridges.
    """
    bridges = bridges if bridges is not None else list(CROSS_ZONE_BRIDGES)
    log: List[str] = []
    for src_zone, src_role, dst_zone, dst_role, alpha in bridges:
        if src_zone not in clusters or dst_zone not in clusters:
            continue
        src = clusters[src_zone]
        dst = clusters[dst_zone]
        if src_role not in src.role_index or dst_role not in dst.role_index:
            continue
        src_bloch = src.role_bloch(src_role)
        # Target: keep x,y of dest-ish but drive z toward source z
        sx, sy, sz = float(src_bloch[0]), float(src_bloch[1]), float(src_bloch[2])
        dst_idx = dst.role_index[dst_role]
        # Partial observe toward (0, 0, sz) — classical pole transfer along z
        dst.observe_qubit(dst_idx, (0.0, 0.0, sz), alpha=float(alpha))
        log.append(
            f"bridge {src_zone}.{src_role} → {dst_zone}.{dst_role} "
            f"(α={alpha}, src_z={sz:.3f})"
        )
    return log
