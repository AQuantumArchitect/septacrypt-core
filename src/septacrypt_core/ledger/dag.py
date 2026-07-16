import dataclasses
import hashlib
from typing import Dict, List, Optional
from .stamp import KnotStamp
from .roots import canonical_serialize

class KnotLedger:
    def __init__(self):
        self.stamps: Dict[str, KnotStamp] = {}
        self.branches: Dict[str, str] = {}  # branch_id -> head_stamp_id

    def compute_stamp_hash(self, stamp: KnotStamp) -> str:
        """
        Generates a SHA-256 hash of the stamp's content, excluding the stamp_id itself.
        """
        # Exclude the stamp_id field to prevent circular hashing
        payload = {k: v for k, v in stamp.__dict__.items() if k != "stamp_id"}
        serialized = canonical_serialize(payload)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def append_stamp(self, stamp: KnotStamp) -> str:
        """
        Enforces Content-Addressable Storage (CAS). Computes the cryptographic stamp_id,
        re-binds the stamp with its true hash, verifies parent links, and appends to the DAG.
        """
        for parent_id in stamp.parent_ids:
            if parent_id not in self.stamps:
                raise ValueError(f"Parent stamp {parent_id} not found in ledger.")

        # Cryptographically seal the stamp
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
        if branch_id not in self.branches:
            raise ValueError(f"Unknown branch {branch_id}")

        history = []
        current_id = self.branches[branch_id]

        while current_id:
            stamp = self.stamps[current_id]
            history.append(stamp)
            current_id = stamp.parent_ids[0] if stamp.parent_ids else None

        return history[::-1]
