"""Bridge between umwelt CumulantCluster and septacrypt physical commitments."""
from __future__ import annotations

from typing import Any, Dict

from ..dynamics.version import DYNAMICS_VERSION
from .roots import generate_state_hash


def physical_payload_from_cluster(cluster) -> Dict[str, Any]:
    """Canonical physical payload for content-hashing and restore.

    Extends umwelt's snapshot() with septacrypt dynamics knobs (gamma, dt) and
    a schema/version so certificates refuse mismatched dynamics.
    """
    snap = cluster.snapshot()
    return {
        "schema": "cumulant.physical.v1",
        "dynamics_version": DYNAMICS_VERSION,
        "zone_name": snap["zone_name"],
        "qubit_roles": list(snap["qubit_roles"]),
        "gamma": float(cluster.gamma),
        "dt": float(cluster.dt),
        "e1": snap["e1"],
        "e2": snap["e2"],
        "h": snap["h"],
        "zz": snap["zz"],
        "xy": snap.get("xy", {}),
    }


def to_umwelt_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Strip septacrypt-only keys for CumulantCluster.load()."""
    return {
        "kind": "cumulant",
        "zone_name": payload["zone_name"],
        "qubit_roles": list(payload["qubit_roles"]),
        "e1": payload["e1"],
        "e2": payload["e2"],
        "h": payload["h"],
        "zz": payload["zz"],
        "xy": payload.get("xy", {}),
    }


def restore_cluster(cluster, payload: Dict[str, Any]) -> None:
    """Load physical payload into an already-built cluster of matching roles."""
    if payload.get("schema") != "cumulant.physical.v1":
        raise ValueError(f"unsupported physical payload schema: {payload.get('schema')}")
    if list(payload.get("qubit_roles", [])) != list(cluster.qubit_roles):
        raise ValueError("payload qubit_roles do not match cluster")
    ok = cluster.load(to_umwelt_snapshot(payload))
    if not ok:
        raise ValueError("CumulantCluster.load rejected payload")
    cluster.gamma = float(payload["gamma"])
    cluster.dt = float(payload["dt"])


def residual_between(payload_a: Dict[str, Any], payload_b: Dict[str, Any]) -> float:
    """Max absolute difference on e1 and e2. Hard structural mismatches raise."""
    for key in ("qubit_roles", "gamma", "dt", "zone_name", "dynamics_version"):
        if payload_a.get(key) != payload_b.get(key):
            raise ValueError(f"structural mismatch on {key}: {payload_a.get(key)!r} vs {payload_b.get(key)!r}")
    # h/zz must match for same dynamics segment (couplings are not events here)
    if payload_a.get("h") != payload_b.get("h") or payload_a.get("zz") != payload_b.get("zz"):
        raise ValueError("structural mismatch on couplings (h/zz)")

    import numpy as np

    e1a = np.asarray(payload_a["e1"], float)
    e1b = np.asarray(payload_b["e1"], float)
    e2a = np.asarray(payload_a["e2"], float)
    e2b = np.asarray(payload_b["e2"], float)
    return float(max(np.max(np.abs(e1a - e1b)), np.max(np.abs(e2a - e2b))))


def payload_hash(payload: Dict[str, Any]) -> str:
    return generate_state_hash(payload)
