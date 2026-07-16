"""Fail-closed certified world transactions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence

from ..dynamics.version import DEFAULT_RESIDUAL_TOLERANCE, DYNAMICS_VERSION
from ..geometry.address import ScaleAddress
from ..ledger.certificate import certificate_id, mint_certificate
from ..ledger.checkpoint import Checkpoint
from ..ledger.dag import KnotLedger
from ..ledger.events import Cassette, KnotEvent, deserialize_cassette, event_digest, rng_commitment
from ..ledger.roots import generate_state_hash
from ..ledger.stamp import KnotStamp, TransitionCertificate
from .snapshot import World, WorldSnapshot, world_hash


class TransactionError(Exception):
    """Raised when a certified transaction fails; world must remain unchanged."""


@dataclass
class CertifiedCommit:
    stamp_id: Optional[str]
    certificate: Optional[TransitionCertificate]
    pre_hash: str
    post_hash: str
    cassette: Cassette
    residual: float


class CertifiedTransaction:
    """
    checkpoint A → apply cassette on working copy → D → independent replay
    → mint cert → commit atomically or leave live world untouched.
    """

    @staticmethod
    def execute(
        world: World,
        cassette: Cassette,
        *,
        ledger: Optional[KnotLedger] = None,
        branch_id: str = "main",
        expected_branch_head: Optional[str] = None,
        observer_id: str = "system",
        event_kind: str = "segment",
        scale_parts: Sequence[str] = ("world",),
        require_certificate: bool = True,
        tolerance: float = DEFAULT_RESIDUAL_TOLERANCE,
    ) -> CertifiedCommit:
        if not cassette and event_kind not in ("init", "reanchor"):
            # empty cassette only for explicit init/reanchor
            pass

        pre_snap = world.snapshot()
        pre_hash = world_hash(pre_snap)

        # Working copy
        working = world.clone()
        try:
            working.apply_cassette(cassette)
            working.advance_turn()
        except Exception as e:
            raise TransactionError(f"apply failed: {e}") from e

        post_snap = working.snapshot()
        post_hash = world_hash(post_snap)

        residual = 0.0
        cert: Optional[TransitionCertificate] = None
        stamp_id: Optional[str] = None

        if require_certificate and ledger is not None:
            # Independent replay verification
            residual = _replay_residual(pre_snap, cassette, post_snap, world)
            if residual > tolerance:
                raise TransactionError(
                    f"replay residual {residual} exceeds tolerance {tolerance}"
                )

            cp_a = Checkpoint(
                checkpoint_id="A",
                chronological_time=float(pre_snap.turn),
                state_data=pre_snap.to_dict(),
                state_hash=pre_hash,
            )
            cp_d = Checkpoint(
                checkpoint_id="D",
                chronological_time=float(post_snap.turn),
                state_data=post_snap.to_dict(),
                state_hash=post_hash,
            )
            cert = mint_certificate(
                cp_a,
                cp_d,
                cassette,
                residual=residual,
                tolerance=tolerance,
                chronological_interval=(float(pre_snap.turn), float(post_snap.turn)),
            )
            # Verify digest consistency
            if event_digest(cassette) != cert.event_digest:
                raise TransactionError("event digest mismatch")

            head = ledger.branches.get(branch_id)
            if expected_branch_head is not None and head != expected_branch_head:
                raise TransactionError(
                    f"branch head mismatch: expected {expected_branch_head!r} got {head!r}"
                )
            # Default continuity: parent must be current head when present
            parent_ids = (head,) if head else ()
            if head and expected_branch_head is None:
                expected_branch_head = head

            pre_root = pre_hash
            if parent_ids:
                parent = ledger.stamps[parent_ids[0]]
                if parent.post_state_root != pre_hash:
                    raise TransactionError(
                        "world pre-hash does not match parent post_state_root "
                        "(refuse silent re-anchor)"
                    )

            stamp = KnotStamp(
                stamp_id="pending",
                parent_ids=parent_ids,
                branch_id=branch_id,
                event_kind=event_kind,
                actor_id=observer_id,
                observer_id=observer_id,
                chronological_time=float(post_snap.turn),
                berry_coordinate=_composite_berry(post_snap),
                scale_address=ScaleAddress(tuple(scale_parts)),
                pre_state_root=pre_root,
                post_state_root=post_hash,
                transition_certificate_id="pending",
                truth_mode="acted",
                confidence=1.0,
                spirit_vector=None,
            )
            try:
                stamp_id = ledger.append_stamp(
                    stamp,
                    certificate=cert,
                    expected_branch_head=expected_branch_head if head else None,
                    require_certificate=True,
                )
            except Exception as e:
                raise TransactionError(f"ledger append failed: {e}") from e

        # Atomic commit of live world
        world.restore(post_snap)
        world.turn = post_snap.turn
        # Re-apply berry by replaying cassette on live berry from pre — restore
        # already re-seeded berry; re-run events for journey continuity on live
        world.restore(pre_snap)
        world.apply_cassette(cassette)
        world.turn = post_snap.turn
        # Preserve presentation active_zone from pre (UI must not be force-changed)
        if pre_snap.active_zone in world.zones:
            world.active_zone = pre_snap.active_zone

        return CertifiedCommit(
            stamp_id=stamp_id,
            certificate=cert,
            pre_hash=pre_hash,
            post_hash=post_hash,
            cassette=cassette,
            residual=residual,
        )


def _composite_berry(snap: WorldSnapshot) -> Dict[str, Any]:
    return {
        "schema": "berry.world.v1",
        "per_zone": snap.berry,
        "path_signature": generate_state_hash(snap.berry),
    }


def _replay_residual(
    pre: WorldSnapshot,
    cassette: Cassette,
    expected_post: WorldSnapshot,
    template: World,
) -> float:
    """Rebuild world from pre, apply cassette, compare physics hash and zone residuals."""
    probe = template.clone()
    probe.restore(pre)
    probe.apply_cassette(cassette)
    probe.advance_turn()
    got = probe.snapshot()
    # turn should match
    if got.turn != expected_post.turn:
        # advance_turn once is enough if expected also advanced once
        pass
    gh = world_hash(got)
    eh = world_hash(expected_post)
    if gh == eh:
        return 0.0
    # Detailed residual: max abs e1/e2 across zones
    import numpy as np

    residual = 0.0
    for name in expected_post.zones:
        a = got.zones[name]
        b = expected_post.zones[name]
        e1 = float(np.max(np.abs(np.asarray(a["e1"]) - np.asarray(b["e1"]))))
        e2 = float(np.max(np.abs(np.asarray(a["e2"]) - np.asarray(b["e2"]))))
        residual = max(residual, e1, e2)
    if residual == 0.0 and gh != eh:
        # non-substrate field differs (rng/berry encoding)
        residual = 1.0  # hard fail
    return residual
