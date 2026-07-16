"""
Legacy thin adapter over GameSession for older call sites (campaign, bots).

Prefer: from septacrypt_core import GameSession
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from umwelt.host.api import GameHost

from .session import GameSession


class FledgelingKernelAPI:
    """
    Backward-compatible presentation surface.

    Internally delegates to GameSession (reactor or injected cluster/zone).
    """

    def __init__(
        self,
        host: Optional[GameHost] = None,
        domain_cluster_name: str = "Repair_Station",
        cluster=None,
        *,
        seed: Optional[int] = None,
        enable_ledger: bool = False,
    ):
        self.host = host if host is not None else _TurnHost()
        self.cluster_name = domain_cluster_name
        # When a pre-built cluster is supplied (campaign zones), wrap without rebuild.
        self._session = GameSession(
            mode="reactor",
            seed=seed,
            enable_ledger=enable_ledger,
            private_observers=False,
            attention_budget=None,
            apply_bridges=False,
        )
        if cluster is not None:
            self._session.zones = {domain_cluster_name: cluster}
            self._session.active_zone = domain_cluster_name
            self._session._berry.seed(cluster)
            if enable_ledger:
                self._session.ledger = None  # avoid double genesis on replaced cluster
                self._session.enable_ledger = False
        self.story_log = self._session.story_log

    def get_cluster(self):
        return self._session.cluster

    @property
    def cluster(self):
        return self._session.cluster

    def fetch_render_state(self, observer_id: str) -> Dict[str, Any]:
        state = self._session.status(observer_id)
        # Preserve legacy shape expected by bots (meta without schema_version requirement)
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


class _TurnHost:
    """Minimal stand-in when GameHost is not needed."""

    def __init__(self):
        self.turn = 0
