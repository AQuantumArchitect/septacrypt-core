"""Composite multi-zone world state with snapshot/restore and hashing."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from ..dynamics.version import DYNAMICS_VERSION, TOPOLOGY_REACTOR, TOPOLOGY_SHIP
from ..geometry.berry import BerryJourney
from ..ledger.events import Cassette, KnotEvent
from ..ledger.roots import generate_state_hash
from ..ledger.substrate import physical_payload_from_cluster, restore_cluster
from ..scenario.manifold_ship import apply_cross_zone_bridges, build_ship_manifold
from ..scenario.params import CROSS_ZONE_BRIDGES
from ..scenario.reactor import build_entangled_reactor


def _rng_getstate(rng: random.Random) -> list:
    # random.getstate() is (version, tuple_of_ints, gauss_next)
    state = rng.getstate()
    return [state[0], list(state[1]), state[2]]


def _rng_setstate(rng: random.Random, blob: list) -> None:
    rng.setstate((blob[0], tuple(blob[1]), blob[2]))


@dataclass
class WorldSnapshot:
    """Immutable-ish capture of the full authoritative world."""

    schema: str
    dynamics_version: str
    topology_version: str
    turn: int
    rng_state: list
    zones: Dict[str, Dict[str, Any]]  # zone -> physical payload
    berry: Dict[str, Dict[str, Any]]  # zone -> berry coordinate dict
    bridges_enabled: bool
    active_zone: str  # presentation only — not physics

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "dynamics_version": self.dynamics_version,
            "topology_version": self.topology_version,
            "turn": self.turn,
            "rng_state": self.rng_state,
            "zones": self.zones,
            "berry": self.berry,
            "bridges_enabled": self.bridges_enabled,
            "active_zone": self.active_zone,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WorldSnapshot":
        return cls(
            schema=d["schema"],
            dynamics_version=d["dynamics_version"],
            topology_version=d["topology_version"],
            turn=int(d["turn"]),
            rng_state=list(d["rng_state"]),
            zones=dict(d["zones"]),
            berry=dict(d.get("berry", {})),
            bridges_enabled=bool(d["bridges_enabled"]),
            active_zone=d["active_zone"],
        )


def world_hash(snapshot: WorldSnapshot) -> str:
    """Content hash of authoritative physics only (excludes active_zone presentation)."""
    payload = snapshot.to_dict()
    # active_zone must NOT affect physics hash
    payload = {k: v for k, v in payload.items() if k != "active_zone"}
    return generate_state_hash(payload)


class World:
    """Live multi-zone substrate + RNG + Berry journeys."""

    def __init__(
        self,
        zones: Dict[str, Any],
        *,
        topology_version: str,
        seed: Optional[int] = None,
        bridges_enabled: bool = False,
        turn: int = 0,
        rng: Optional[random.Random] = None,
        berry: Optional[Dict[str, BerryJourney]] = None,
        active_zone: Optional[str] = None,
        routines: Optional[Dict[str, Dict[str, Any]]] = None,
        bridge_list: Optional[List[tuple]] = None,
        spec: Optional[Any] = None,
    ):
        self.zones = zones
        self.topology_version = topology_version
        self.bridges_enabled = bridges_enabled
        self.turn = turn
        self.rng = rng if rng is not None else random.Random(seed)
        self.seed = seed
        # Which cross-zone couplings a "bridges" event applies. None means the
        # legacy builtin table (CROSS_ZONE_BRIDGES); spec-built worlds carry
        # their own.
        self.bridge_list: Optional[List[tuple]] = bridge_list
        self.spec = spec  # WorldSpec for spec-built worlds (clone dispatch)
        self.berry: Dict[str, BerryJourney] = berry if berry is not None else {}
        for name, cluster in self.zones.items():
            if name not in self.berry:
                bj = BerryJourney()
                bj.seed(cluster)
                self.berry[name] = bj
        self.active_zone = active_zone or next(iter(self.zones))
        # shadow-first routine registry: name -> {shadow, auto_live, actor_id, ...}
        self.routines: Dict[str, Dict[str, Any]] = routines if routines is not None else {}

    @classmethod
    def reactor(cls, seed: Optional[int] = None) -> "World":
        c = build_entangled_reactor()
        return cls(
            {c.zone_name: c},
            topology_version=TOPOLOGY_REACTOR,
            seed=seed,
            bridges_enabled=False,
            active_zone=c.zone_name,
        )

    @classmethod
    def ship(cls, seed: Optional[int] = None, bridges_enabled: bool = True) -> "World":
        zones = build_ship_manifold()
        return cls(
            zones,
            topology_version=TOPOLOGY_SHIP,
            seed=seed,
            bridges_enabled=bridges_enabled,
            active_zone="Reactor_Core",
        )

    @classmethod
    def from_spec(cls, spec: Any, seed: Optional[int] = None, bridges_enabled: Optional[bool] = None) -> "World":
        """Build a world from a WorldSpec (septacrypt_core.spec.types)."""
        from umwelt.substrate.cumulant_cluster import CumulantCluster

        errors = spec.validate()
        if errors:
            raise ValueError(f"invalid WorldSpec {spec.spec_id!r}: " + "; ".join(errors))
        zones: Dict[str, Any] = {}
        for z in spec.zones:
            cluster = CumulantCluster(
                zone_name=z.name,
                qubit_roles=list(z.roles),
                gamma=z.gamma,
                dt=z.dt,
            )
            cluster.set_couplings(
                h_fields=[list(row) for row in z.h_fields],
                zz={(i, j): v for (i, j), v in z.zz},
            )
            zones[z.name] = cluster
        if bridges_enabled is None:
            bridges_enabled = bool(spec.bridges)
        return cls(
            zones,
            topology_version=spec.topology_version,
            seed=seed,
            bridges_enabled=bridges_enabled,
            active_zone=spec.zones[0].name,
            bridge_list=spec.bridge_tuples(),
            spec=spec,
        )

    @property
    def cluster(self):
        return self.zones[self.active_zone]

    def zone_names(self) -> List[str]:
        return list(self.zones.keys())

    def set_active_zone(self, zone: str) -> None:
        if zone not in self.zones:
            raise ValueError(f"unknown zone {zone!r}")
        self.active_zone = zone

    def snapshot(self) -> WorldSnapshot:
        return WorldSnapshot(
            schema="world.v1",
            dynamics_version=DYNAMICS_VERSION,
            topology_version=self.topology_version,
            turn=self.turn,
            rng_state=_rng_getstate(self.rng),
            zones={n: physical_payload_from_cluster(c) for n, c in self.zones.items()},
            berry={n: j.coordinate(self.zones[n]) for n, j in self.berry.items()},
            bridges_enabled=self.bridges_enabled,
            active_zone=self.active_zone,
        )

    def physics_hash(self) -> str:
        return world_hash(self.snapshot())

    def restore(self, snap: WorldSnapshot) -> None:
        if snap.schema != "world.v1":
            raise ValueError(f"unsupported world schema {snap.schema}")
        if set(snap.zones) != set(self.zones):
            raise ValueError("zone set mismatch on restore")
        for name, payload in snap.zones.items():
            restore_cluster(self.zones[name], payload)
        self.turn = snap.turn
        self.bridges_enabled = snap.bridges_enabled
        self.topology_version = snap.topology_version
        _rng_setstate(self.rng, snap.rng_state)
        # active_zone is presentation — restore for UI continuity but not physics
        if snap.active_zone in self.zones:
            self.active_zone = snap.active_zone
        # Re-seed berry journeys from restored clusters (path history not fully restored)
        self.reseed_berry()

    def reseed_berry(self) -> None:
        """Re-seed berry journeys from current clusters (restore() semantics)."""
        for name, cluster in self.zones.items():
            bj = BerryJourney()
            bj.seed(cluster)
            self.berry[name] = bj

    def clone(self) -> "World":
        """Isolated working copy with identical physics state."""
        snap = self.snapshot()
        if self.spec is not None:
            w = World.from_spec(self.spec, seed=self.seed, bridges_enabled=self.bridges_enabled)
        elif self.topology_version == TOPOLOGY_REACTOR:
            w = World.reactor(seed=self.seed)
        else:
            w = World.ship(seed=self.seed, bridges_enabled=self.bridges_enabled)
        w.restore(snap)
        w.routines = {k: dict(v) for k, v in self.routines.items()}
        # Copy berry sample history approximately via re-seed (path_sig resets on clone
        # mid-transaction is OK: we recompute from events during apply)
        return w

    def apply_event(self, event: KnotEvent) -> None:
        """Mutate this world by one typed event (authoritative path)."""
        kind = event.kind
        p = event.parameters

        if kind == "evolve":
            zone = p.get("zone", self.active_zone)
            cluster = self.zones[zone]
            steps = int(p.get("steps", 1))
            dt = float(p["dt_scale"])
            for _ in range(steps):
                cluster.step(dt_scale=dt)
            self.berry[zone].observe_after(cluster, event)

        elif kind == "world_evolve":
            steps = int(p.get("steps", 1))
            dt = float(p["dt_scale"])
            for name, cluster in self.zones.items():
                for _ in range(steps):
                    cluster.step(dt_scale=dt)
                self.berry[name].observe_after(cluster, event)

        elif kind == "measure":
            # Consume any recorded RNG draws so session RNG stays replay-aligned
            for _ in p.get("rng_draws", []):
                self.rng.random()
            zone = p.get("zone") or self.active_zone
            cluster = self.zones[zone]
            role = p["role"]
            idx = cluster.role_index[role]
            cluster.measure_qubit(
                idx,
                record_z=float(p["record_z"]),
                strength=float(p.get("strength", 1.0)),
            )
            self.berry[zone].observe_after(cluster, event)



        elif kind == "set_fields":
            zone = p["zone"]
            cluster = self.zones[zone]
            cluster.set_couplings(h_fields=p["h_fields"])

        elif kind == "set_couplings":
            zone = p["zone"]
            cluster = self.zones[zone]
            zz = None
            if "zz" in p:
                zz = {}
                for k, v in p["zz"].items():
                    if isinstance(k, str) and "," in k:
                        i, j = (int(x) for x in k.split(","))
                        zz[(i, j)] = float(v)
                    else:
                        zz[k] = float(v)
            h = p.get("h_fields")
            cluster.set_couplings(h_fields=h, zz=zz)

        elif kind == "bridges":
            if self.bridges_enabled:
                bridges = self.bridge_list if self.bridge_list is not None else list(CROSS_ZONE_BRIDGES)
                apply_cross_zone_bridges(self.zones, bridges)

        elif kind == "report":
            # Epistemic only — no substrate mutation (handled by ObserverBeliefStore)
            pass

        elif kind == "reanchor":
            # Administrative no-op on substrate; ledger records the reason
            pass

        elif kind == "promote_routine":
            name = p["routine_name"]
            entry = self.routines.setdefault(
                name,
                {"shadow": True, "auto_live": False, "actor_id": p["actor_id"]},
            )
            entry["shadow"] = False
            entry["auto_live"] = True
            entry["promoted_by"] = p["actor_id"]
            entry["evidence"] = p.get("evidence", "")

        elif kind == "demote_routine":
            name = p["routine_name"]
            entry = self.routines.setdefault(
                name,
                {"shadow": True, "auto_live": False, "actor_id": p["actor_id"]},
            )
            entry["shadow"] = True
            entry["auto_live"] = False
            entry["demoted_by"] = p["actor_id"]

        else:
            raise ValueError(f"unhandled event kind {kind}")

    def apply_cassette(self, cassette: Cassette) -> None:
        for event in cassette:
            self.apply_event(event)
        self._check_finite()

    def _check_finite(self) -> None:
        """Non-finite substrate state must never commit: an overflowed RK4
        step returns inf/NaN without raising, and a world that carries those
        values is bricked (every later evolve/measure fails or lies). Both
        transaction paths route through apply_cassette, so one check here
        turns silent corruption into a fail-closed rollback."""
        for name, cluster in self.zones.items():
            if not (np.all(np.isfinite(cluster.e1)) and np.all(np.isfinite(cluster.e2))):
                raise ValueError(f"non-finite substrate state in zone {name!r}")

    def advance_turn(self) -> None:
        self.turn += 1
