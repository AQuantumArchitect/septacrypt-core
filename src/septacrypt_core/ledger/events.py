"""Typed event cassettes for witnessed replay between committed anchors."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Literal, Sequence, Tuple

from .roots import canonical_serialize

EventKind = Literal["evolve", "measure"]


@dataclass(frozen=True)
class KnotEvent:
    """One substrate-executable operation with fully recorded parameters.

    Measurements store `record_z` so replay is deterministic without re-seeding RNG.
    """
    kind: EventKind
    parameters: Dict[str, Any]

    def __post_init__(self) -> None:
        if self.kind == "evolve":
            if "dt_scale" not in self.parameters:
                raise ValueError("evolve events require dt_scale")
        elif self.kind == "measure":
            for key in ("role", "record_z"):
                if key not in self.parameters:
                    raise ValueError(f"measure events require {key}")
        else:
            raise ValueError(f"unknown event kind: {self.kind}")


Cassette = Tuple[KnotEvent, ...]


def evolve_event(dt_scale: float, steps: int = 1) -> KnotEvent:
    return KnotEvent(kind="evolve", parameters={"dt_scale": float(dt_scale), "steps": int(steps)})


def measure_event(role: str, record_z: float, strength: float = 1.0) -> KnotEvent:
    return KnotEvent(
        kind="measure",
        parameters={
            "role": role,
            "record_z": float(record_z),
            "strength": float(strength),
        },
    )


def cassette_to_jsonable(cassette: Sequence[KnotEvent]) -> List[Dict[str, Any]]:
    return [asdict(e) for e in cassette]


def cassette_from_jsonable(raw: Sequence[Dict[str, Any]]) -> Cassette:
    return tuple(KnotEvent(kind=item["kind"], parameters=dict(item["parameters"])) for item in raw)


def serialize_cassette(cassette: Sequence[KnotEvent]) -> str:
    return canonical_serialize(cassette_to_jsonable(cassette))


def deserialize_cassette(blob: str) -> Cassette:
    """Parse a cassette previously produced by serialize_cassette / mint_certificate."""
    import json

    data = json.loads(blob)
    return cassette_from_jsonable(data)



def event_digest(cassette: Sequence[KnotEvent]) -> str:
    return hashlib.sha256(serialize_cassette(cassette).encode("utf-8")).hexdigest()


def rng_commitment(cassette: Sequence[KnotEvent]) -> str:
    """Hash of recorded measurement outcomes (order-preserving)."""
    outcomes = [
        {"role": e.parameters["role"], "record_z": e.parameters["record_z"]}
        for e in cassette
        if e.kind == "measure"
    ]
    payload = canonical_serialize(outcomes)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def affected_surface(cassette: Sequence[KnotEvent]) -> Tuple[str, ...]:
    roles: List[str] = []
    seen = set()
    for e in cassette:
        if e.kind == "measure":
            role = e.parameters["role"]
            if role not in seen:
                seen.add(role)
                roles.append(role)
        elif e.kind == "evolve":
            tag = "*"
            if tag not in seen:
                seen.add(tag)
                roles.append(tag)
    return tuple(roles)
