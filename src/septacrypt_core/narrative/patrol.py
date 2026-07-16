"""Wraps umwelt's AgencyLoop, injecting Q3 narrative tension as its 'surprise'
signal — high off-diagonal coherence in the quantum state pauses the loop's
feed-forward time contraction, the same gate umwelt already uses for its own
surprise/rest pauses (see host/agency_loop.py TimeContraction.update)."""
from umwelt.host.api import GameHost
from umwelt.host.agency_loop import AgencyLoop, SubRoutine

from .braid import NarrativeBraid


class MythosAgencyLoop:
    """Drives umwelt's AgencyLoop, feeding Q3 narrative tension in as 'surprise'."""

    def __init__(self, host: GameHost):
        self.host = host
        self.loop = AgencyLoop(host)

    def add_mythos_routine(self, name: str, actor_id: str, intent_name: str, cost: float = 1.0):
        routine = SubRoutine(
            name=name,
            intent_name=intent_name,
            actor_id=actor_id,
            attention_cost=cost,
            shadow=False,
            auto_live=True,
        )
        self.loop.add_routine(routine)

    def tick_with_tension(self, raw_quantum_state_matrix) -> list:
        """
        Reads a raw density matrix (ours or umwelt's own, any dimension),
        computes narrative tension, and feeds it to the AgencyLoop as 'surprise'.
        """
        tension = NarrativeBraid.calculate_narrative_tension_from_raw(raw_quantum_state_matrix)

        decisions = self.loop.tick(surprise=tension)

        if self.loop.clock.paused:
            print(f"\n[MYTHOS] Feed-forward halted. Reason: {self.loop.clock.reason}")
            print(f"[MYTHOS] The Endless Knot writhes. Tension spiked to {tension:.3f}.")

        return decisions
