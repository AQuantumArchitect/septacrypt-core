"""Content-addressed Knot Ledger with certificate-gated append."""
from __future__ import annotations

import dataclasses
import hashlib
from typing import Dict, List, Optional

from ..geometry.address import ScaleAddress
from .certificate import certificate_id, verify_certificate
from .roots import canonical_serialize
from .stamp import KnotStamp, TransitionCertificate


class KnotLedger:
    def __init__(self):
        self.stamps: Dict[str, KnotStamp] = {}
        self.branches: Dict[str, str] = {}  # branch_id -> head_stamp_id
        self.certificates: Dict[str, TransitionCertificate] = {}

    def compute_stamp_hash(self, stamp: KnotStamp) -> str:
        payload = {k: v for k, v in stamp.__dict__.items() if k != "stamp_id"}
        # ScaleAddress must serialize stably
        if isinstance(payload.get("scale_address"), ScaleAddress):
            payload = dict(payload)
            payload["scale_address"] = {
                "segments": list(payload["scale_address"].segments),
                "display": payload["scale_address"].display_path,
            }
        serialized = canonical_serialize(payload)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def register_certificate(self, cert: TransitionCertificate) -> str:
        cid = certificate_id(cert)
        self.certificates[cid] = cert
        return cid

    def append_stamp(
        self,
        stamp: KnotStamp,
        *,
        certificate: Optional[TransitionCertificate] = None,
        expected_branch_head: Optional[str] = None,
        cluster_factory=None,
        pre_checkpoint=None,
        post_checkpoint=None,
        require_certificate: bool = True,
    ) -> str:
        """
        Append a content-addressed stamp. Non-init stamps require a verified
        TransitionCertificate and causal continuity with the branch head.
        """
        if not isinstance(stamp.scale_address, ScaleAddress):
            raise TypeError(
                f"scale_address must be ScaleAddress, got {type(stamp.scale_address).__name__}"
            )

        is_init = stamp.event_kind == "init" and not stamp.parent_ids

        if require_certificate or not is_init:
            if certificate is None:
                raise ValueError("certificate is required to append a Knot stamp")
            cid = self.register_certificate(certificate)
            if stamp.transition_certificate_id not in ("", "pending", cid):
                if stamp.transition_certificate_id != cid:
                    raise ValueError(
                        f"stamp.transition_certificate_id {stamp.transition_certificate_id!r} "
                        f"does not match certificate {cid!r}"
                    )
            # Bind certificate id onto stamp if pending
            if stamp.transition_certificate_id in ("", "pending"):
                stamp = dataclasses.replace(stamp, transition_certificate_id=cid)

            if certificate.pre_state_root != stamp.pre_state_root:
                raise ValueError("stamp.pre_state_root does not match certificate")
            if certificate.post_state_root != stamp.post_state_root:
                raise ValueError("stamp.post_state_root does not match certificate")

            # Full dynamical verify when checkpoints + factory supplied
            if cluster_factory is not None and pre_checkpoint is not None and post_checkpoint is not None:
                if not verify_certificate(
                    certificate, cluster_factory, pre_checkpoint, post_checkpoint
                ):
                    raise ValueError("TransitionCertificate failed dynamical verification")
            elif not is_init and certificate.residual > certificate.tolerance:
                raise ValueError("certificate residual exceeds tolerance")

        for parent_id in stamp.parent_ids:
            if parent_id not in self.stamps:
                raise ValueError(f"Parent stamp {parent_id} not found in ledger.")

        # Branch head continuity
        current_head = self.branches.get(stamp.branch_id)
        if expected_branch_head is not None:
            if current_head != expected_branch_head:
                raise ValueError(
                    f"expected_branch_head {expected_branch_head!r} != current head {current_head!r}"
                )
        elif current_head is not None and stamp.parent_ids:
            # Default: first parent must be current head (linear continuity)
            if stamp.parent_ids[0] != current_head:
                raise ValueError(
                    f"parent_ids[0] {stamp.parent_ids[0]!r} is not branch head {current_head!r}; "
                    f"pass expected_branch_head explicitly only when intentional"
                )

        # Causal pre/post continuity with primary parent
        if stamp.parent_ids:
            parent = self.stamps[stamp.parent_ids[0]]
            if stamp.pre_state_root != parent.post_state_root:
                raise ValueError(
                    "stamp.pre_state_root must equal parent post_state_root "
                    f"({stamp.pre_state_root[:12]}... != {parent.post_state_root[:12]}...)"
                )

        true_hash = f"stamp_{self.compute_stamp_hash(stamp)[:16]}"
        sealed_stamp = dataclasses.replace(stamp, stamp_id=true_hash)

        self.stamps[sealed_stamp.stamp_id] = sealed_stamp
        self.branches[sealed_stamp.branch_id] = sealed_stamp.stamp_id
        return sealed_stamp.stamp_id

    def branch(self, parent_stamp_id: str, new_branch_id: str) -> None:
        if parent_stamp_id not in self.stamps:
            raise ValueError(f"Cannot branch from unknown stamp {parent_stamp_id}")
        self.branches[new_branch_id] = parent_stamp_id

    def get_history(self, branch_id: str) -> List[KnotStamp]:
        """Primary-parent linearization of branch history (not full merge DAG)."""
        if branch_id not in self.branches:
            raise ValueError(f"Unknown branch {branch_id}")

        history = []
        current_id = self.branches[branch_id]

        while current_id:
            stamp = self.stamps[current_id]
            history.append(stamp)
            current_id = stamp.parent_ids[0] if stamp.parent_ids else None

        return history[::-1]
