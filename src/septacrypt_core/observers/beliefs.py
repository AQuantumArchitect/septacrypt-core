"""Observer-specific first-moment belief store — no automatic telepathy."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..geometry.atlas import bloch_to_septacrypt
from ..ledger.events import KnotEvent
from ..narrative.lexicon import LoreLexicon
from ..world.snapshot import World


@dataclass
class ReportRecord:
    source_observer: str
    target_observer: str
    zone: str
    role: str
    z_value: float
    confidence: float
    channel: str
    turn: int


@dataclass
class ObserverBelief:
    """First-moment approximation only — not a complete private umwelt."""

    observer_id: str
    # zone -> e1 array (n, 3)
    e1: Dict[str, np.ndarray] = field(default_factory=dict)
    roles: Dict[str, List[str]] = field(default_factory=dict)
    reports: List[ReportRecord] = field(default_factory=list)
    # roles this observer has directly measured (zone.role)
    observed: set = field(default_factory=set)


class ObserverBeliefStore:
    """
    Epistemic layer. LOOK updates only the measuring observer from ground.
    Other observers change only via typed report events.
    """

    def __init__(self):
        self._beliefs: Dict[str, ObserverBelief] = {}

    def ensure(self, observer_id: str, world: World) -> ObserverBelief:
        if observer_id not in self._beliefs:
            b = ObserverBelief(observer_id=observer_id)
            for name, cluster in world.zones.items():
                # Uninformative prior: zero Bloch (maximally mixed first moment)
                n = cluster.n_qubits
                b.e1[name] = np.zeros((n, 3))
                b.roles[name] = list(cluster.qubit_roles)
            self._beliefs[observer_id] = b
        return self._beliefs[observer_id]

    def apply_event(self, world: World, event: KnotEvent, turn: int) -> None:
        if event.kind == "measure":
            obs_id = event.parameters.get("observer_id")
            if not obs_id:
                return
            b = self.ensure(obs_id, world)
            zone = event.parameters["zone"]
            role = event.parameters["role"]
            cluster = world.zones[zone]
            # Full snap of measured zone e1 for that observer after ground measurement
            b.e1[zone] = np.array(cluster.e1, copy=True)
            b.roles[zone] = list(cluster.qubit_roles)
            b.observed.add(f"{zone}.{role}")

        elif event.kind == "report":
            p = event.parameters
            target = p["target_observer"]
            b = self.ensure(target, world)
            zone = p["zone"]
            role = p["role"]
            conf = float(p["confidence"])
            z = float(p["z_value"])
            if zone not in b.e1:
                self.ensure(target, world)
            roles = b.roles[zone]
            idx = roles.index(role)
            # Blend only that role's z toward reported value
            old = b.e1[zone][idx].copy()
            target_bloch = np.array([0.0, 0.0, z])
            b.e1[zone][idx] = (1.0 - conf) * old + conf * target_bloch
            b.reports.append(
                ReportRecord(
                    source_observer=p["source_observer"],
                    target_observer=target,
                    zone=zone,
                    role=role,
                    z_value=z,
                    confidence=conf,
                    channel=p.get("channel", "heard_report"),
                    turn=turn,
                )
            )

    def bloch(self, observer_id: str, zone: str, role: str, world: World) -> Tuple[float, float, float]:
        b = self.ensure(observer_id, world)
        idx = b.roles[zone].index(role)
        v = b.e1[zone][idx]
        return float(v[0]), float(v[1]), float(v[2])

    def q3_mask(self, observer_id: str, zone: str, world: World) -> int:
        b = self.ensure(observer_id, world)
        vecs = []
        for role in b.roles[zone]:
            vecs.append(self.bloch(observer_id, zone, role, world))
        return bloch_to_septacrypt(vecs)

    def tension_proxy(self, observer_id: str, zone: str, world: World) -> float:
        """Observer-local uncertainty proxy: mean (1 - radius) — not ground tension."""
        b = self.ensure(observer_id, world)
        radii = []
        for role in b.roles[zone]:
            x, y, z = self.bloch(observer_id, zone, role, world)
            radii.append((x * x + y * y + z * z) ** 0.5)
        if not radii:
            return 0.0
        return round(float(np.mean([1.0 - min(1.0, r) for r in radii])), 5)

    def observer_view(
        self,
        observer_id: str,
        world: World,
        *,
        zone: Optional[str] = None,
    ) -> Dict[str, Any]:
        zone = zone or world.active_zone
        b = self.ensure(observer_id, world)
        mask = self.q3_mask(observer_id, zone, world)
        lore = LoreLexicon.get_state_lore(mask)
        entities = {}
        for role in b.roles[zone]:
            x, y, z = self.bloch(observer_id, zone, role, world)
            radius = (x * x + y * y + z * z) ** 0.5
            known = f"{zone}.{role}" in b.observed
            entities[role] = {
                "raw_metrics": {
                    "z_axis": z,
                    "radius": radius,
                    "phase_x": x,
                    "phase_y": y,
                },
                "semantic": {
                    "inferred_state": "active" if z > 0 else "latent",
                    "view": "private",
                    "directly_observed": known,
                },
            }
        return {
            "observer": observer_id,
            "zone": zone,
            "belief_kind": "first_moment_e1",
            "belief_note": "Not a complete private umwelt; first-moment approximation only.",
            "q3_mask": mask,
            "current_mythos": lore,
            "uncertainty": self.tension_proxy(observer_id, zone, world),
            "entities": entities,
            "reports": [
                {
                    "source": r.source_observer,
                    "role": r.role,
                    "zone": r.zone,
                    "z_value": r.z_value,
                    "confidence": r.confidence,
                    "channel": r.channel,
                    "turn": r.turn,
                }
                for r in b.reports[-8:]
            ],
        }
