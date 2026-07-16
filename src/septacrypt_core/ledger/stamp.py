from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
from ..geometry.address import ScaleAddress

@dataclass(frozen=True)
class EntityRef:
    entity_id: str
    lineage_id: str
    parent_id: Optional[str]
    scale_path: ScaleAddress  # Upgraded to normalized ScaleAddress
    schema_version: str

@dataclass(frozen=True)
class SpiritVector:
    wisdom: float
    might: float
    wealth: float
    power: float
    glory: float
    honor: float
    blessing: float
    frame_id: str
    confidence: float

@dataclass(frozen=True)
class Observation:
    observer_id: str
    source_id: str
    target: EntityRef
    channel: str
    value: Any
    confidence: float
    chronological_time: float
    branch_id: str

@dataclass(frozen=True)
class Intent:
    actor_id: str
    target: EntityRef
    action_type: str
    parameters: Dict[str, Any]
    spirit_gradient: Optional[SpiritVector]
    shadow: bool = True

@dataclass(frozen=True)
class TransitionCertificate:
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
    scale_address: ScaleAddress  # Upgraded to normalized ScaleAddress
    pre_state_root: str
    post_state_root: str
    transition_certificate_id: str
    truth_mode: str
    confidence: float
    spirit_vector: Optional[SpiritVector]
