"""WorldSpec — authoritative ground physics + game content as data.

Deliberately a SIBLING of umwelt's DomainSpec, mirroring its ergonomics
(frozen dataclasses, `load_spec("module:ATTR")`, a validate CLI) without
extending it: DomainSpec declares belief-field topology for the estimator;
WorldSpec declares the ground truth a game world runs on (clusters, ZZ
couplings, transverse fields, cross-zone bridges, quests). Keeping them
separate keeps ground truth and lore out of the belief front door.

v1 honesty constraint: exactly 3 roles per zone. The Q3 ontology tables
(geometry/counts.py, emoji, lexicon, atlas) assume 3 bits; the validator
enforces it rather than letting an n-role spec fail somewhere deep.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

ZZItem = Tuple[Tuple[int, int], float]


@dataclass(frozen=True)
class ZoneSpec:
    name: str
    roles: Tuple[str, ...]
    h_fields: Tuple[Tuple[float, float, float], ...]
    zz: Tuple[ZZItem, ...]
    gamma: float
    dt: float
    # Optional initial Bloch vector (x, y, z) per role at construction only;
    # None keeps the substrate default (ground pole). Never consulted on
    # clone/restore — snapshots always win.
    init_bloch: Optional[Tuple[Tuple[float, float, float], ...]] = None


@dataclass(frozen=True)
class BridgeSpec:
    src_zone: str
    src_role: str
    dst_zone: str
    dst_role: str
    alpha: float


@dataclass(frozen=True)
class QuestSpec:
    zone: str
    target_mask: int


@dataclass(frozen=True)
class WorldSpec:
    spec_id: str
    topology_version: str
    zones: Tuple[ZoneSpec, ...]
    bridges: Tuple[BridgeSpec, ...] = ()
    quests: Tuple[QuestSpec, ...] = ()
    attention: Optional[float] = None

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.spec_id:
            errors.append("spec_id must be non-empty")
        if not self.zones:
            errors.append("at least one zone required")
        zone_names = [z.name for z in self.zones]
        if len(set(zone_names)) != len(zone_names):
            errors.append("duplicate zone names")

        for z in self.zones:
            n = len(z.roles)
            if n != 3:
                errors.append(
                    f"zone {z.name!r}: {n} roles — v1 requires exactly 3 "
                    "(Q3 ontology tables assume 3 bits)"
                )
            if len(set(z.roles)) != len(z.roles):
                errors.append(f"zone {z.name!r}: duplicate roles")
            if len(z.h_fields) != n:
                errors.append(f"zone {z.name!r}: h_fields must have one row per role")
            for row in z.h_fields:
                if len(row) != 3:
                    errors.append(f"zone {z.name!r}: h_fields rows must be (hx, hy, hz)")
                    break
            for (i, j), _v in z.zz:
                if not (0 <= i < n and 0 <= j < n and i != j):
                    errors.append(f"zone {z.name!r}: zz index ({i},{j}) out of range")
            if z.init_bloch is not None:
                if len(z.init_bloch) != n:
                    errors.append(f"zone {z.name!r}: init_bloch must have one row per role")
                for row in z.init_bloch:
                    if len(row) != 3:
                        errors.append(f"zone {z.name!r}: init_bloch rows must be (x, y, z)")
                        break
                    if sum(c * c for c in row) > 1.0 + 1e-9:
                        errors.append(
                            f"zone {z.name!r}: init_bloch row {row} outside the Bloch ball"
                        )
                        break
            if z.gamma < 0:
                errors.append(f"zone {z.name!r}: gamma must be >= 0")
            if z.dt <= 0:
                errors.append(f"zone {z.name!r}: dt must be > 0")

        by_name = {z.name: z for z in self.zones}
        for b in self.bridges:
            for zone_key, role_key in ((b.src_zone, b.src_role), (b.dst_zone, b.dst_role)):
                z = by_name.get(zone_key)
                if z is None:
                    errors.append(f"bridge references unknown zone {zone_key!r}")
                elif role_key not in z.roles:
                    errors.append(f"bridge references unknown role {zone_key}.{role_key}")
            if not (0.0 < b.alpha <= 1.0):
                errors.append(f"bridge alpha {b.alpha} outside (0, 1]")

        for q in self.quests:
            z = by_name.get(q.zone)
            if z is None:
                errors.append(f"quest references unknown zone {q.zone!r}")
            elif not (0 <= q.target_mask < 2 ** len(z.roles)):
                errors.append(f"quest mask {q.target_mask} out of range for zone {q.zone!r}")

        if self.attention is not None and self.attention <= 0:
            errors.append("attention must be positive or None")
        return errors

    def bridge_tuples(self) -> List[Tuple[str, str, str, str, float]]:
        """The (src_zone, src_role, dst_zone, dst_role, alpha) form that
        apply_cross_zone_bridges consumes."""
        return [(b.src_zone, b.src_role, b.dst_zone, b.dst_role, b.alpha) for b in self.bridges]
