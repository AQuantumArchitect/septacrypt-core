"""Wraps umwelt's AgencyLoop with Q3 tension as surprise — shadow-first autonomy."""
from __future__ import annotations

from typing import Dict, Optional

from umwelt.host.api import GameHost
from umwelt.host.agency_loop import AgencyLoop, SubRoutine

from .braid import NarrativeBraid


class MythosAgencyLoop:
    """Drives umwelt's AgencyLoop; routines start in shadow, not live."""

    def __init__(self, host: GameHost):
        self.host = host
        self.loop = AgencyLoop(host)
        self._routines: Dict[str, SubRoutine] = {}

    def add_mythos_routine(
        self,
        name: str,
        actor_id: str,
        intent_name: str,
        cost: float = 1.0,
        *,
        shadow: bool = True,
        auto_live: bool = False,
    ):
        """Default: shadow=True, auto_live=False (umwelt shadow-first)."""
        routine = SubRoutine(
            name=name,
            intent_name=intent_name,
            actor_id=actor_id,
            attention_cost=cost,
            shadow=shadow,
            auto_live=auto_live,
        )
        self.loop.add_routine(routine)
        self._routines[name] = routine
        return routine

    def promote_routine(self, name: str) -> None:
        """Explicit promotion to live dispatch — call only after evidence."""
        if name not in self._routines:
            raise KeyError(f"unknown routine {name}")
        # SubRoutine may be frozen; re-add with live flags if needed
        old = self._routines[name]
        try:
            old.shadow = False  # type: ignore[misc]
            old.auto_live = True  # type: ignore[misc]
        except Exception:
            promoted = SubRoutine(
                name=old.name,
                intent_name=old.intent_name,
                actor_id=old.actor_id,
                attention_cost=old.attention_cost,
                shadow=False,
                auto_live=True,
            )
            self.loop.add_routine(promoted)
            self._routines[name] = promoted

    def demote_routine(self, name: str) -> None:
        if name not in self._routines:
            raise KeyError(f"unknown routine {name}")
        old = self._routines[name]
        try:
            old.shadow = True  # type: ignore[misc]
            old.auto_live = False  # type: ignore[misc]
        except Exception:
            demoted = SubRoutine(
                name=old.name,
                intent_name=old.intent_name,
                actor_id=old.actor_id,
                attention_cost=old.attention_cost,
                shadow=True,
                auto_live=False,
            )
            self.loop.add_routine(demoted)
            self._routines[name] = demoted

    def can_dispatch_live(self, name: str) -> bool:
        r = self._routines.get(name)
        if r is None:
            return False
        return (not getattr(r, "shadow", True)) and getattr(r, "auto_live", False)

    def tick_with_tension(self, raw_quantum_state_matrix) -> list:
        tension = NarrativeBraid.calculate_narrative_tension_from_raw(raw_quantum_state_matrix)
        decisions = self.loop.tick(surprise=tension)
        if self.loop.clock.paused:
            # Prefer structured return over print for library code
            decisions = list(decisions) if decisions else []
            decisions.append(
                {
                    "type": "mythos_pause",
                    "reason": getattr(self.loop.clock, "reason", "tension"),
                    "tension": tension,
                }
            )
        return decisions
