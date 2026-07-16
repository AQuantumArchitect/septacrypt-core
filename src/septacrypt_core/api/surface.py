"""Legacy adapter over GameSession for campaign/bots."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .session import GameSession


class _TurnHost:
    def __init__(self):
        self.turn = 0


class FledgelingKernelAPI:
    """Backward-compatible surface; prefer GameSession."""

    def __init__(
        self,
        host=None,
        domain_cluster_name: str = "Repair_Station",
        cluster=None,
        *,
        seed: Optional[int] = None,
        enable_ledger: bool = False,
    ):
        self.host = host if host is not None else _TurnHost()
        self.cluster_name = domain_cluster_name
        self._session = GameSession(
            mode="reactor",
            seed=seed,
            enable_ledger=enable_ledger,
            private_observers=False,
            attention_budget=None,
            apply_bridges=False,
            include_ground_debug=False,
        )
        if cluster is not None:
            # Inject pre-built zone cluster (campaign)
            self._session.world.zones = {domain_cluster_name: cluster}
            self._session.world.active_zone = domain_cluster_name
            from ..geometry.berry import BerryJourney

            bj = BerryJourney()
            bj.seed(cluster)
            self._session.world.berry = {domain_cluster_name: bj}
            self._session.ledger = None
            self._session.enable_ledger = False
        self.story_log = self._session.story_log

    def get_cluster(self):
        return self._session.cluster

    @property
    def cluster(self):
        return self._session.cluster

    def fetch_render_state(self, observer_id: str) -> Dict[str, Any]:
        state = self._session.status(observer_id)
        self.host.turn = self._session.turn
        return {
            "meta": {
                "observer": observer_id,
                "turn": self._session.turn,
                "global_tension": state["meta"]["global_tension"],
                "current_mythos": state["meta"]["current_mythos"],
            },
            "entities": {
                role: {
                    "raw_metrics": body["raw_metrics"],
                    "semantic": {"inferred_state": body["semantic"]["inferred_state"]},
                }
                for role, body in state["entities"].items()
            },
            "narrative_log": state["narrative_log"][-5:],
        }

    def command_measure(self, observer_id: str, target_role: str) -> Dict[str, Any]:
        self._session.look(observer_id, target_role)
        self.host.turn = self._session.turn
        return self.fetch_render_state(observer_id)

    def command_evolve(self, dt_scale: float = None) -> Dict[str, Any]:
        self._session.wait(dt_scale=dt_scale)
        self.host.turn = self._session.turn
        return self.fetch_render_state("system")
