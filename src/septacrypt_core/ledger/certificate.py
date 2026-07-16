"""Mint and verify TransitionCertificates against real cumulant replay."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, replace
from typing import Callable, Optional, Sequence, Tuple

from ..dynamics.version import DEFAULT_RESIDUAL_TOLERANCE, DYNAMICS_VERSION
from .checkpoint import Checkpoint, replay_from_checkpoint, residual_vs_checkpoint
from .events import (
    Cassette,
    KnotEvent,
    affected_surface,
    event_digest,
    rng_commitment,
    serialize_cassette,
)
from .roots import canonical_serialize
from .stamp import TransitionCertificate

HIDDEN_CONDITIONS: Tuple[str, ...] = (
    "cumulant_2body_closure",
    "recorded_measurement_outcomes",
)


def certificate_id(cert: TransitionCertificate) -> str:
    payload = asdict(cert)
    digest = hashlib.sha256(canonical_serialize(payload).encode("utf-8")).hexdigest()
    return f"cert_{digest[:16]}"


def mint_certificate(
    cp_a: Checkpoint,
    cp_d: Checkpoint,
    cassette: Sequence[KnotEvent],
    *,
    residual: float,
    tolerance: float = DEFAULT_RESIDUAL_TOLERANCE,
    chronological_interval: Optional[Tuple[float, float]] = None,
    dynamics_version: str = DYNAMICS_VERSION,
) -> TransitionCertificate:
    """Build a certificate from already-computed residual (caller may verify later)."""
    if chronological_interval is None:
        chronological_interval = (cp_a.chronological_time, cp_d.chronological_time)
    return TransitionCertificate(
        dynamics_version=dynamics_version,
        pre_state_root=cp_a.state_hash,
        post_state_root=cp_d.state_hash,
        event_digest=event_digest(cassette),
        chronological_interval=chronological_interval,
        residual=float(residual),
        tolerance=float(tolerance),
        rng_commitment=rng_commitment(cassette),
        replay_cassette=serialize_cassette(cassette),
        affected_surface=affected_surface(cassette),
        hidden_conditions=HIDDEN_CONDITIONS,
    )


def mint_empty_certificate(cp: Checkpoint) -> TransitionCertificate:
    """Genesis / identity segment: empty cassette, residual 0, pre == post."""
    return mint_certificate(cp, cp, (), residual=0.0)


def verify_certificate(
    cert: TransitionCertificate,
    cluster_factory: Callable[[], object],
    cp_a: Checkpoint,
    cp_d: Checkpoint,
    *,
    dynamics_version: str = DYNAMICS_VERSION,
) -> bool:
    """
    Re-restore A, replay cassette on a fresh cluster, check residual ≤ tolerance
    and that pre/post hashes match the certificate and checkpoints.
    """
    if cert.dynamics_version != dynamics_version:
        return False
    if cert.pre_state_root != cp_a.state_hash:
        return False
    if cert.post_state_root != cp_d.state_hash:
        return False

    from .events import deserialize_cassette

    try:
        cassette = deserialize_cassette(cert.replay_cassette)
    except Exception:
        return False

    if event_digest(cassette) != cert.event_digest:
        return False
    if rng_commitment(cassette) != cert.rng_commitment:
        return False

    cluster = cluster_factory()
    try:
        replayed = replay_from_checkpoint(cluster, cp_a, cassette)
        residual = residual_vs_checkpoint(replayed, cp_d)
    except Exception:
        return False

    if residual > cert.tolerance:
        return False
    # Replay endpoint must commit to the same post hash.
    if replayed.state_hash != cp_d.state_hash:
        return False
    return True


def mint_and_verify(
    cluster_factory: Callable[[], object],
    cp_a: Checkpoint,
    cp_d: Checkpoint,
    cassette: Sequence[KnotEvent],
    *,
    tolerance: float = DEFAULT_RESIDUAL_TOLERANCE,
) -> TransitionCertificate:
    """Replay to measure residual, mint cert, verify; raise if verification fails."""
    cluster = cluster_factory()
    replayed = replay_from_checkpoint(cluster, cp_a, cassette)
    residual = residual_vs_checkpoint(replayed, cp_d)
    if residual > tolerance:
        raise ValueError(f"replay residual {residual} exceeds tolerance {tolerance}")
    if replayed.state_hash != cp_d.state_hash:
        raise ValueError("replayed state hash does not match checkpoint D")
    cert = mint_certificate(cp_a, cp_d, cassette, residual=residual, tolerance=tolerance)
    if not verify_certificate(cert, cluster_factory, cp_a, cp_d):
        raise ValueError("minted certificate failed verification")
    return cert
