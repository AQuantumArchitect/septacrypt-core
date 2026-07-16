import hashlib
import json
from typing import Any, Dict


def canonical_serialize(data: Any) -> str:
    """
    Recursively serializes state data into a canonical, sorted JSON string.
    Ensures that identical states produce identical strings, regardless of memory layout.
    """
    if isinstance(data, dict):
        return "{" + ",".join(
            f'"{k}":{canonical_serialize(v)}' for k, v in sorted(data.items())
        ) + "}"
    elif isinstance(data, (list, tuple)):
        return "[" + ",".join(canonical_serialize(item) for item in data) + "]"
    elif isinstance(data, (int, float, str, bool, type(None))):
        return json.dumps(data)
    elif hasattr(data, "__dict__"):
        return canonical_serialize(data.__dict__)
    else:
        return json.dumps(str(data))


def generate_state_hash(state_data: Dict[str, Any]) -> str:
    """
    Deterministic SHA-256 content hash of canonicalized state data.

    This is a whole-state content hash, not a Merkle tree root. Partial proofs
    and subtree sharing require a future true Merkleization.
    """
    serialized = canonical_serialize(state_data)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def verify_state_hash(state_data: Dict[str, Any], expected_hash: str) -> bool:
    return generate_state_hash(state_data) == expected_hash


# Backward-compatible aliases (content hash, not Merkle).
generate_state_root = generate_state_hash
verify_state_root = verify_state_hash
