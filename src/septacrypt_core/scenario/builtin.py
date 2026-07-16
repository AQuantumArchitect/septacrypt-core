"""Builtin WorldSpecs — the params.py literals expressed as data.

REACTOR_SPEC and SHIP_SPEC are exactly the legacy `mode="reactor"` /
`mode="ship"` worlds; tests/test_worldspec.py pins hash-identity between the
two construction paths over seeded play.
"""
from __future__ import annotations

from ..dynamics.version import TOPOLOGY_REACTOR, TOPOLOGY_SHIP
from ..spec.types import BridgeSpec, QuestSpec, WorldSpec, ZoneSpec
from .params import (
    CROSS_ZONE_BRIDGES,
    DEFAULT_ATTENTION,
    DEFAULT_QUESTS,
    REACTOR_DT,
    REACTOR_GAMMA,
    REACTOR_H_FIELDS,
    REACTOR_ROLES,
    REACTOR_ZZ,
    ZONE_DT,
    ZONE_GAMMA,
    ZONE_H_FIELDS,
    ZONE_ROLES,
    ZONE_ZZ,
)


def _rows(h_fields) -> tuple:
    return tuple(tuple(float(x) for x in row) for row in h_fields)


def _zz(zz_dict) -> tuple:
    return tuple(((int(i), int(j)), float(v)) for (i, j), v in zz_dict.items())


REACTOR_SPEC = WorldSpec(
    spec_id="septacrypt.reactor.v1",
    topology_version=TOPOLOGY_REACTOR,
    zones=(
        ZoneSpec(
            name="Repair_Station",
            roles=tuple(REACTOR_ROLES),
            h_fields=_rows(REACTOR_H_FIELDS),
            zz=_zz(REACTOR_ZZ),
            gamma=REACTOR_GAMMA,
            dt=REACTOR_DT,
        ),
    ),
    attention=DEFAULT_ATTENTION,
)

SHIP_SPEC = WorldSpec(
    spec_id="septacrypt.ship.v1",
    topology_version=TOPOLOGY_SHIP,
    zones=tuple(
        ZoneSpec(
            name=zone_name,
            roles=tuple(roles),
            h_fields=_rows(ZONE_H_FIELDS),
            zz=_zz(ZONE_ZZ),
            gamma=ZONE_GAMMA,
            dt=ZONE_DT,
        )
        for zone_name, roles in ZONE_ROLES.items()
    ),
    bridges=tuple(
        BridgeSpec(src_zone=s, src_role=sr, dst_zone=d, dst_role=dr, alpha=a)
        for s, sr, d, dr, a in CROSS_ZONE_BRIDGES
    ),
    quests=tuple(QuestSpec(zone=z, target_mask=m) for z, m in DEFAULT_QUESTS),
    attention=DEFAULT_ATTENTION,
)
