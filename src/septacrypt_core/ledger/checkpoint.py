from dataclasses import dataclass
from typing import Dict, Any
from .roots import generate_state_root

@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    chronological_time: float
    state_data: Dict[str, Any]
    state_root: str

    @classmethod
    def create(cls, checkpoint_id: str, time: float, state_data: Dict[str, Any]) -> 'Checkpoint':
        root = generate_state_root(state_data)
        return cls(
            checkpoint_id=checkpoint_id,
            chronological_time=time,
            state_data=state_data,
            state_root=root
        )

def replay_overlay(base_checkpoint: Checkpoint, events: list) -> Checkpoint:
    """
    Stub for applying an event overlay to a checkpoint to reach a new state.
    Full integration will pass these events through SpaceWheat/Universal Architect.
    """
    # Create a copy-on-write simulation of state change
    new_state = dict(base_checkpoint.state_data)
    for event in events:
        new_state["applied_events"] = new_state.get("applied_events", []) + [event]

    return Checkpoint.create(
        checkpoint_id=f"derived_from_{base_checkpoint.checkpoint_id}",
        time=base_checkpoint.chronological_time + len(events),
        state_data=new_state
    )
