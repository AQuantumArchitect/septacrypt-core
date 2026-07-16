"""Checkpoints and single-cluster replay helpers (world path uses World.apply_*)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from .events import Cassette, KnotEvent
from .roots import generate_state_hash
from .substrate import (
    physical_payload_from_cluster,
    residual_between,
    restore_cluster,
)


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    chronological_time: float
    state_data: Dict[str, Any]
    state_hash: str

    @property
    def state_root(self) -> str:
        return self.state_hash

    @classmethod
    def create(cls, checkpoint_id: str, time: float, state_data: Dict[str, Any]) -> "Checkpoint":
        h = generate_state_hash(state_data)
        return cls(
            checkpoint_id=checkpoint_id,
            chronological_time=time,
            state_data=state_data,
            state_hash=h,
        )

    @classmethod
    def from_cluster(cls, checkpoint_id: str, time: float, cluster) -> "Checkpoint":
        payload = physical_payload_from_cluster(cluster)
        return cls(
            checkpoint_id=checkpoint_id,
            chronological_time=time,
            state_data=payload,
            state_hash=generate_state_hash(payload),
        )


def apply_event(cluster, event: KnotEvent) -> None:
    """Apply evolve/measure to a single cluster (witnessed-knot / legacy proofs)."""
    if event.kind == "evolve":
        steps = int(event.parameters.get("steps", 1))
        dt_scale = float(event.parameters["dt_scale"])
        for _ in range(steps):
            cluster.step(dt_scale=dt_scale)
    elif event.kind == "measure":
        role = event.parameters["role"]
        idx = cluster.role_index.get(role)
        if idx is None:
            raise ValueError(f"unknown role for measure: {role}")
        cluster.measure_qubit(
            idx,
            record_z=float(event.parameters["record_z"]),
            strength=float(event.parameters.get("strength", 1.0)),
        )
    else:
        raise ValueError(f"single-cluster apply_event does not support kind={event.kind}")


def sample_measure_outcome(cluster, role: str) -> float:
    import random

    z_before = float(cluster.role_bloch(role)[2])
    p_plus = (z_before + 1.0) / 2.0
    return 1.0 if random.random() < p_plus else -1.0


def run_segment(cluster, plan: Sequence[KnotEvent], *, sample_unresolved_measures: bool = False) -> Cassette:
    recorded: List[KnotEvent] = []
    for event in plan:
        apply_event(cluster, event)
        recorded.append(event)
    return tuple(recorded)


def replay_from_checkpoint(cluster, checkpoint: Checkpoint, cassette: Sequence[KnotEvent]) -> Checkpoint:
    restore_cluster(cluster, checkpoint.state_data)
    for event in cassette:
        apply_event(cluster, event)
    return Checkpoint.from_cluster(
        checkpoint_id=f"replay_of_{checkpoint.checkpoint_id}",
        time=checkpoint.chronological_time + len(cassette),
        cluster=cluster,
    )


def residual_vs_checkpoint(replayed: Checkpoint, expected: Checkpoint) -> float:
    return residual_between(replayed.state_data, expected.state_data)


def legacy_dict_overlay(base_checkpoint: Checkpoint, events: list) -> Checkpoint:
    new_state = dict(base_checkpoint.state_data)
    for event in events:
        new_state["applied_events"] = new_state.get("applied_events", []) + [event]
    return Checkpoint.create(
        checkpoint_id=f"derived_from_{base_checkpoint.checkpoint_id}",
        time=base_checkpoint.chronological_time + len(events),
        state_data=new_state,
    )


def replay_overlay(base_checkpoint: Checkpoint, events: list) -> Checkpoint:
    return legacy_dict_overlay(base_checkpoint, events)
