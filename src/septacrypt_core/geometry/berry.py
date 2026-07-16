"""Berry journey adapter — wires umwelt BlochGeometricPhase / BerryTape into stamps."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from umwelt.clocks.berry_tape import BerryTape
from umwelt.substrate.params import BlochGeometricPhase

from ..ledger.events import KnotEvent
from ..ledger.roots import canonical_serialize


def _round_floats(obj: Any, ndigits: int = 8) -> Any:
    if isinstance(obj, float):
        return round(obj, ndigits)
    if isinstance(obj, dict):
        return {k: _round_floats(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round_floats(v, ndigits) for v in obj]
    return obj


class BerryJourney:
    """Accumulate geometric phase along a cassette applied to a live cluster."""

    def __init__(self):
        self.geo = BlochGeometricPhase()
        self.tape = BerryTape()
        self.samples: List[Dict[str, Any]] = []
        self._roles: List[str] = []

    def seed(self, cluster) -> None:
        self._roles = list(cluster.qubit_roles)
        for role in self._roles:
            self.geo.update(role, cluster.role_bloch(role))
        self._tick_tape()

    def _tick_tape(self) -> None:
        phases = [float(self.geo.phases.get(r, 0.0)) for r in self._roles]
        self.tape.tick(phases)

    def _bloch_z_snap(self, cluster) -> Dict[str, float]:
        return {r: round(float(cluster.role_bloch(r)[2]), 8) for r in cluster.qubit_roles}

    def observe_after(self, cluster, event: KnotEvent) -> None:
        phase_before = float(self.geo.total)
        for role in cluster.qubit_roles:
            self.geo.update(role, cluster.role_bloch(role))
        self._roles = list(cluster.qubit_roles)
        self._tick_tape()
        phase_after = float(self.geo.total)
        z_snap = self._bloch_z_snap(cluster)

        if event.kind == "measure":
            role = event.parameters["role"]
            outcome = event.parameters.get("record_z", 0.0)
            new_state = "plus" if float(outcome) > 0 else "minus"
            self.tape.stamp_collapse(
                node=cluster.zone_name,
                role=role,
                old_state="superposed",
                new_state=new_state,
                bloch_z_snap=z_snap,
            )

        self.samples.append(
            {
                "i": len(self.samples),
                "kind": event.kind,
                "params": {
                    k: event.parameters[k]
                    for k in event.parameters
                    if k in ("dt_scale", "steps", "role", "record_z", "strength")
                },
                "d_phase": round(phase_after - phase_before, 8),
                "total_phase": round(phase_after, 8),
                "z": z_snap,
            }
        )

    def coordinate(self, cluster=None) -> Dict[str, Any]:
        per_role = {r: round(float(self.geo.phases.get(r, 0.0)), 8) for r in self._roles}
        endpoint_z = {}
        if cluster is not None:
            endpoint_z = self._bloch_z_snap(cluster)
        elif self.samples:
            endpoint_z = dict(self.samples[-1].get("z", {}))

        path_body = _round_floats(
            {
                "samples": self.samples,
                "per_role": per_role,
                "total_phase": round(float(self.geo.total), 8),
            }
        )
        path_signature = hashlib.sha256(
            canonical_serialize(path_body).encode("utf-8")
        ).hexdigest()

        return {
            "schema": "berry.v1",
            "total_phase": round(float(self.geo.total), 8),
            "per_role": per_role,
            "endpoint_bloch_z": endpoint_z,
            "path_signature": path_signature,
            "ticker": self.tape.ticker.snapshot(),
            "sample_count": len(self.samples),
        }
