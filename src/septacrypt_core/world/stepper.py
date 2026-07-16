"""WorldStepper — advance every zone equally; UI zone never selects physics."""
from __future__ import annotations

from typing import List, Optional

from ..dynamics.version import MAX_STABLE_DT_SCALE
from ..ledger.events import Cassette, KnotEvent, bridges_event, world_evolve_event
from .snapshot import World


class WorldStepper:
    """Builds and applies atomic world steps independent of active UI zone."""

    @staticmethod
    def plan_world_step(
        *,
        dt_scale: float = MAX_STABLE_DT_SCALE,
        steps: int = 1,
        apply_bridges: bool = True,
    ) -> Cassette:
        if dt_scale > MAX_STABLE_DT_SCALE:
            dt_scale = MAX_STABLE_DT_SCALE
        events: List[KnotEvent] = [world_evolve_event(dt_scale=dt_scale, steps=steps)]
        if apply_bridges:
            events.append(bridges_event())
        return tuple(events)

    @staticmethod
    def apply_plan(world: World, cassette: Cassette) -> None:
        world.apply_cassette(cassette)
