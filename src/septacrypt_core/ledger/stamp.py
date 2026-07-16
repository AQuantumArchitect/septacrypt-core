from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any

from ..geometry.address import ScaleAddress
from ..spirit.vector import SpiritVector


@dataclass(frozen=True)
class EntityRef:
    entity_id: str
    lineage_id: str
    parent_id: Optional[str]
    scale_path: ScaleAddress
    schema_version: str


@dataclass(frozen=True)
class KnotObservation:
    """Ledger-side observation record. Renamed from `Observation` (ADR-001):
    umwelt.host owns the plain belief-face names (Observation, Intent,
    GameHost, WorldSession); septacrypt-core's ledger vocabulary is Knot-*."""

    observer_id: str
    source_id: str
    target: EntityRef
    channel: str
    value: Any
    confidence: float
    chronological_time: float
    branch_id: str


@dataclass(frozen=True)
class KnotIntent:
    """Ledger-side intent record. Renamed from `Intent` (ADR-001)."""

    actor_id: str
    target: EntityRef
    action_type: str
    parameters: Dict[str, Any]
    spirit_gradient: Optional[SpiritVector]
    shadow: bool = True


def __getattr__(name: str):
    # Deprecation aliases for one release (ADR-001 name hygiene).
    if name in ("Observation", "Intent"):
        import warnings

        new = {"Observation": KnotObservation, "Intent": KnotIntent}[name]
        warnings.warn(
            f"septacrypt_core.ledger.stamp.{name} is deprecated; use {new.__name__} "
            "(umwelt.host owns the plain belief-face names — see ADR-001)",
            DeprecationWarning,
            stacklevel=2,
        )
        return new
    raise AttributeError(name)


@dataclass(frozen=True)
class TransitionCertificate:
    """Witness that a cassette is dynamically realizable between committed anchors.

    pre/post *_root fields hold content hashes of physical payloads (not Merkle trees).
    """
    dynamics_version: str
    pre_state_root: str
    post_state_root: str
    event_digest: str
    chronological_interval: Tuple[float, float]
    residual: float
    tolerance: float
    rng_commitment: Optional[str]
    replay_cassette: str
    affected_surface: Tuple[str, ...]
    hidden_conditions: Tuple[str, ...]


@dataclass(frozen=True)
class KnotStamp:
    stamp_id: str
    parent_ids: Tuple[str, ...]
    branch_id: str
    event_kind: str
    actor_id: Optional[str]
    observer_id: Optional[str]
    chronological_time: float
    berry_coordinate: Dict[str, Any]
    scale_address: ScaleAddress
    pre_state_root: str
    post_state_root: str
    transition_certificate_id: str
    truth_mode: str
    confidence: float
    spirit_vector: Optional[SpiritVector]
