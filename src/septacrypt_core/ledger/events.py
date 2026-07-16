"""Typed event cassettes for witnessed replay between committed anchors."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Literal, Sequence, Tuple

from .roots import canonical_serialize

EventKind = Literal[
    "evolve",
    "world_evolve",
    "measure",
    "set_fields",
    "set_couplings",
    "bridges",
    "report",
    "reanchor",
    "promote_routine",
    "demote_routine",
]

_REQUIRED: Dict[str, Tuple[str, ...]] = {
    "evolve": ("dt_scale",),
    "world_evolve": ("dt_scale",),
    "measure": ("role", "record_z"),  # zone optional for single-cluster legacy
    "set_fields": ("zone", "h_fields"),
    "set_couplings": ("zone",),
    "bridges": (),
    "report": ("source_observer", "target_observer", "zone", "role", "z_value", "confidence", "channel"),
    "reanchor": ("reason",),
    "promote_routine": ("routine_name", "actor_id"),
    "demote_routine": ("routine_name", "actor_id"),
}


@dataclass(frozen=True)
class KnotEvent:
    """One substrate-executable or observer-epistemic operation.

    Authoritative world mutations must be fully recorded so replay is deterministic.
    Measurement outcomes store record_z (no live RNG on replay).
    """

    kind: EventKind
    parameters: Dict[str, Any]

    def __post_init__(self) -> None:
        if self.kind not in _REQUIRED:
            raise ValueError(f"unknown event kind: {self.kind}")
        for key in _REQUIRED[self.kind]:
            if key not in self.parameters:
                raise ValueError(f"{self.kind} events require {key}")


Cassette = Tuple[KnotEvent, ...]


def evolve_event(dt_scale: float, steps: int = 1, zone: str | None = None) -> KnotEvent:
    params: Dict[str, Any] = {"dt_scale": float(dt_scale), "steps": int(steps)}
    if zone is not None:
        params["zone"] = zone
    return KnotEvent(kind="evolve", parameters=params)


def world_evolve_event(dt_scale: float, steps: int = 1) -> KnotEvent:
    return KnotEvent(
        kind="world_evolve",
        parameters={"dt_scale": float(dt_scale), "steps": int(steps)},
    )


def measure_event(
    role: str,
    record_z: float,
    *,
    zone: str | None = None,
    strength: float = 1.0,
    observer_id: str | None = None,
) -> KnotEvent:
    params: Dict[str, Any] = {
        "role": role,
        "record_z": float(record_z),
        "strength": float(strength),
    }
    if zone is not None:
        params["zone"] = zone
    if observer_id is not None:
        params["observer_id"] = observer_id
    return KnotEvent(kind="measure", parameters=params)



def set_fields_event(zone: str, h_fields: List[List[float]]) -> KnotEvent:
    return KnotEvent(
        kind="set_fields",
        parameters={"zone": zone, "h_fields": [list(row) for row in h_fields]},
    )


def set_couplings_event(
    zone: str,
    *,
    zz: Dict[str, float] | None = None,
    h_fields: List[List[float]] | None = None,
) -> KnotEvent:
    params: Dict[str, Any] = {"zone": zone}
    if zz is not None:
        params["zz"] = dict(zz)
    if h_fields is not None:
        params["h_fields"] = [list(row) for row in h_fields]
    return KnotEvent(kind="set_couplings", parameters=params)


def bridges_event() -> KnotEvent:
    return KnotEvent(kind="bridges", parameters={})


def report_event(
    source_observer: str,
    target_observer: str,
    *,
    zone: str,
    role: str,
    z_value: float,
    confidence: float,
    channel: str = "heard_report",
) -> KnotEvent:
    return KnotEvent(
        kind="report",
        parameters={
            "source_observer": source_observer,
            "target_observer": target_observer,
            "zone": zone,
            "role": role,
            "z_value": float(z_value),
            "confidence": float(confidence),
            "channel": channel,
        },
    )


def reanchor_event(reason: str) -> KnotEvent:
    return KnotEvent(kind="reanchor", parameters={"reason": reason})


def promote_routine_event(routine_name: str, actor_id: str, evidence: str = "") -> KnotEvent:
    return KnotEvent(
        kind="promote_routine",
        parameters={
            "routine_name": routine_name,
            "actor_id": actor_id,
            "evidence": evidence,
        },
    )


def demote_routine_event(routine_name: str, actor_id: str, reason: str = "") -> KnotEvent:
    return KnotEvent(
        kind="demote_routine",
        parameters={
            "routine_name": routine_name,
            "actor_id": actor_id,
            "reason": reason,
        },
    )


def cassette_to_jsonable(cassette: Sequence[KnotEvent]) -> List[Dict[str, Any]]:
    return [asdict(e) for e in cassette]


def cassette_from_jsonable(raw: Sequence[Dict[str, Any]]) -> Cassette:
    return tuple(KnotEvent(kind=item["kind"], parameters=dict(item["parameters"])) for item in raw)


def serialize_cassette(cassette: Sequence[KnotEvent]) -> str:
    return canonical_serialize(cassette_to_jsonable(cassette))


def deserialize_cassette(blob: str) -> Cassette:
    import json

    data = json.loads(blob)
    return cassette_from_jsonable(data)


def event_digest(cassette: Sequence[KnotEvent]) -> str:
    return hashlib.sha256(serialize_cassette(cassette).encode("utf-8")).hexdigest()


def rng_commitment(cassette: Sequence[KnotEvent]) -> str:
    """Hash of recorded measurement outcomes (order-preserving)."""
    outcomes = [
        {
            "zone": e.parameters.get("zone"),
            "role": e.parameters["role"],
            "record_z": e.parameters["record_z"],
        }
        for e in cassette
        if e.kind == "measure"
    ]
    payload = canonical_serialize(outcomes)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def affected_surface(cassette: Sequence[KnotEvent]) -> Tuple[str, ...]:
    tags: List[str] = []
    seen = set()
    for e in cassette:
        if e.kind == "measure":
            tag = f"{e.parameters.get('zone', '*')}.{e.parameters['role']}"

        elif e.kind in ("evolve", "set_fields", "set_couplings"):
            tag = e.parameters.get("zone", "*")
        elif e.kind == "world_evolve":
            tag = "world.*"
        elif e.kind == "bridges":
            tag = "bridges"
        elif e.kind == "report":
            tag = f"report:{e.parameters['source_observer']}->{e.parameters['target_observer']}"
        elif e.kind in ("promote_routine", "demote_routine"):
            tag = f"routine:{e.parameters['routine_name']}"
        elif e.kind == "reanchor":
            tag = "reanchor"
        else:
            tag = e.kind
        if tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tuple(tags)
