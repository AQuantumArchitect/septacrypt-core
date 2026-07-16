"""
GameSession — the recommended handoff surface for building a game on Septacrypt.

Brother/bots: import GameSession, call look/wait/status. Everything else is optional depth.

    from septacrypt_core import GameSession

    game = GameSession(mode="reactor", seed=42)
    print(game.status("player"))
    game.wait()
    game.look("player", "valve_17")
    print(game.history())
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..dynamics.version import DYNAMICS_VERSION, MAX_STABLE_DT_SCALE
from ..geometry.address import ScaleAddress
from ..geometry.atlas import bloch_to_septacrypt
from ..geometry.berry import BerryJourney
from ..ledger.certificate import mint_and_verify, mint_empty_certificate
from ..ledger.checkpoint import Checkpoint, apply_event
from ..ledger.dag import KnotLedger
from ..ledger.events import Cassette, evolve_event, measure_event
from ..ledger.stamp import KnotStamp
from ..narrative.lexicon import LoreLexicon
from ..narrative.weaver import EndlessKnotWeaver
from ..scenario.manifold_ship import apply_cross_zone_bridges, build_ship_manifold
from ..scenario.params import (
    DEFAULT_ATTENTION,
    DEFAULT_QUESTS,
    LOOK_ATTENTION_COST,
    STIR_DT_SCALE,
    STIR_STEPS,
    STIR_TRANSVERSE,
)
from ..scenario.reactor import build_entangled_reactor
from .schema import RENDER_SCHEMA_VERSION, validate_render_state


class GameSession:
    """
    One playable session: substrate + optional ledger stamps + render payload.

    Modes
    -----
    reactor : single 3-qubit repair station (default, simplest)
    ship    : 3-zone manifold with soft cross-zone bridges

    Options
    -------
    seed              : full RNG control for LOOK outcomes
    enable_ledger     : stamp every LOOK/WAIT with a verified certificate
    private_observers : each observer keeps a private belief field (LOOK updates both)
    attention_budget  : None = unlimited
    """

    def __init__(
        self,
        *,
        mode: str = "reactor",
        seed: Optional[int] = None,
        enable_ledger: bool = True,
        private_observers: bool = False,
        attention_budget: Optional[float] = DEFAULT_ATTENTION,
        apply_bridges: bool = True,
    ):
        if mode not in ("reactor", "ship"):
            raise ValueError("mode must be 'reactor' or 'ship'")
        self.mode = mode
        self.seed = seed
        self.rng = random.Random(seed)
        self.enable_ledger = enable_ledger
        self.private_observers = private_observers
        self.attention_budget = attention_budget
        self.apply_bridges = apply_bridges and mode == "ship"
        self.turn = 0
        self.story_log: List[str] = []
        self.dynamics_version = DYNAMICS_VERSION

        if mode == "reactor":
            c = build_entangled_reactor()
            self.zones: Dict[str, Any] = {c.zone_name: c}
            self.active_zone = c.zone_name
        else:
            self.zones = build_ship_manifold()
            self.active_zone = "Reactor_Core"

        # Private belief: observer_id -> zone -> shallow state copy (e1 arrays)
        self._beliefs: Dict[str, Dict[str, Dict[str, Any]]] = {}

        self.ledger = KnotLedger() if enable_ledger else None
        self._branch = "main"
        self._berry = BerryJourney()
        self._berry.seed(self.cluster)
        self._init_ledger_if_needed()

        # Campaign quests (ship mode convenience)
        self.quests: List[Tuple[str, int]] = list(DEFAULT_QUESTS) if mode == "ship" else []

    # ── cluster accessors ──────────────────────────────────────────────

    @property
    def cluster(self):
        return self.zones[self.active_zone]

    def set_zone(self, zone: str) -> None:
        if zone not in self.zones:
            raise ValueError(f"unknown zone {zone!r}; have {list(self.zones)}")
        self.active_zone = zone

    def zone_names(self) -> List[str]:
        return list(self.zones.keys())

    def _factory_for(self, zone: str):
        def factory():
            if self.mode == "reactor":
                return build_entangled_reactor()
            clusters = build_ship_manifold()
            return clusters[zone]

        return factory

    # ── ledger ─────────────────────────────────────────────────────────

    def _init_ledger_if_needed(self) -> None:
        if not self.ledger:
            return
        cp = Checkpoint.from_cluster("genesis", 0.0, self.cluster)
        cert = mint_empty_certificate(cp)
        stamp = KnotStamp(
            stamp_id="pending",
            parent_ids=(),
            branch_id=self._branch,
            event_kind="init",
            actor_id=None,
            observer_id="system",
            chronological_time=0.0,
            berry_coordinate={"schema": "berry.v1", "path_signature": "seed"},
            scale_address=ScaleAddress((self.active_zone,)),
            pre_state_root=cp.state_hash,
            post_state_root=cp.state_hash,
            transition_certificate_id="pending",
            truth_mode="observed",
            confidence=1.0,
            spirit_vector=None,
        )
        self.ledger.append_stamp(
            stamp,
            certificate=cert,
            expected_branch_head=None,
            cluster_factory=self._factory_for(self.active_zone),
            pre_checkpoint=cp,
            post_checkpoint=cp,
        )
        self._last_post_hash = cp.state_hash
        self._last_checkpoint = cp

    def _stamp_segment(
        self,
        cassette: Cassette,
        observer_id: str,
        event_kind: str,
        scale_parts: Sequence[str],
    ) -> Optional[str]:
        if not self.ledger or not cassette:
            return None
        zone = self.active_zone
        cp_a = self._last_checkpoint
        # Rebuild A: the checkpoint we stored is the pre-state of this segment
        # We captured pre before apply; post is current cluster
        cp_d = Checkpoint.from_cluster(f"t{self.turn}", float(self.turn), self.cluster)
        cert = mint_and_verify(self._factory_for(zone), cp_a, cp_d, cassette)
        berry = self._berry.coordinate(self.cluster)
        head = self.ledger.branches.get(self._branch)
        stamp = KnotStamp(
            stamp_id="pending",
            parent_ids=(head,) if head else (),
            branch_id=self._branch,
            event_kind=event_kind,
            actor_id=observer_id,
            observer_id=observer_id,
            chronological_time=float(self.turn),
            berry_coordinate=berry,
            scale_address=ScaleAddress(tuple(scale_parts)),
            pre_state_root=cp_a.state_hash,
            post_state_root=cp_d.state_hash,
            transition_certificate_id="pending",
            truth_mode="acted",
            confidence=1.0,
            spirit_vector=None,
        )
        sid = self.ledger.append_stamp(
            stamp,
            certificate=cert,
            expected_branch_head=head,
            cluster_factory=self._factory_for(zone),
            pre_checkpoint=cp_a,
            post_checkpoint=cp_d,
        )
        self._last_checkpoint = cp_d
        self._last_post_hash = cp_d.state_hash
        return sid

    def history(self, branch: Optional[str] = None) -> List[Dict[str, Any]]:
        """Linear primary-parent history for UI / debug."""
        if not self.ledger:
            return []
        stamps = self.ledger.get_history(branch or self._branch)
        return [
            {
                "stamp_id": s.stamp_id,
                "event_kind": s.event_kind,
                "observer_id": s.observer_id,
                "time": s.chronological_time,
                "pre": s.pre_state_root[:12],
                "post": s.post_state_root[:12],
                "berry_sig": (s.berry_coordinate or {}).get("path_signature", "")[:12],
                "cert": s.transition_certificate_id,
            }
            for s in stamps
        ]

    # ── private observers ──────────────────────────────────────────────

    def _ensure_belief(self, observer_id: str, zone: str) -> Dict[str, Any]:
        if observer_id not in self._beliefs:
            self._beliefs[observer_id] = {}
        if zone not in self._beliefs[observer_id]:
            c = self.zones[zone]
            self._beliefs[observer_id][zone] = {
                "e1": np.array(c.e1, copy=True),
                "roles": list(c.qubit_roles),
            }
        return self._beliefs[observer_id][zone]

    def _sync_belief_from_ground(self, observer_id: str, zone: str, alpha: float = 1.0) -> None:
        """Pull private belief toward ground (alpha=1 full snap)."""
        belief = self._ensure_belief(observer_id, zone)
        ground = self.zones[zone].e1
        belief["e1"] = (1.0 - alpha) * belief["e1"] + alpha * np.array(ground, copy=True)

    def _belief_bloch(self, observer_id: str, zone: str, role: str) -> Tuple[float, float, float]:
        belief = self._ensure_belief(observer_id, zone)
        idx = belief["roles"].index(role)
        v = belief["e1"][idx]
        return float(v[0]), float(v[1]), float(v[2])

    # ── physics helpers ────────────────────────────────────────────────

    def _q3_mask(self, cluster=None) -> int:
        cluster = cluster or self.cluster
        return bloch_to_septacrypt([cluster.role_bloch(r) for r in cluster.qubit_roles])

    @staticmethod
    def _tension(cluster) -> float:
        n = cluster.n_qubits
        tension = 0.0
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                conn = cluster.e2[i, j] - np.outer(cluster.e1[i], cluster.e1[j])
                tension += float(abs(conn[2, 2]))
        return round(tension, 5)

    def _entity_payload(
        self,
        cluster,
        *,
        observer_id: str,
        zone: str,
        use_private: bool,
    ) -> Dict[str, Any]:
        out = {}
        for role in cluster.qubit_roles:
            if use_private and self.private_observers:
                x, y, z = self._belief_bloch(observer_id, zone, role)
                view = "private"
            else:
                b = cluster.role_bloch(role)
                x, y, z = float(b[0]), float(b[1]), float(b[2])
                view = "ground"
            radius = (x * x + y * y + z * z) ** 0.5
            out[role] = {
                "raw_metrics": {
                    "z_axis": z,
                    "radius": radius,
                    "phase_x": x,
                    "phase_y": y,
                },
                "semantic": {
                    "inferred_state": "active" if z > 0 else "latent",
                    "view": view,
                },
            }
        return out

    # ── public commands ────────────────────────────────────────────────

    def status(
        self,
        observer_id: str = "player",
        *,
        zone: Optional[str] = None,
        full_ship: bool = False,
    ) -> Dict[str, Any]:
        """JSON-serializable frame payload for UI / engine."""
        if zone:
            self.set_zone(zone)
        cluster = self.cluster
        if self.private_observers:
            self._ensure_belief(observer_id, self.active_zone)

        lore = LoreLexicon.get_state_lore(self._q3_mask(cluster))
        head = None
        if self.ledger:
            head = self.ledger.branches.get(self._branch)

        payload: Dict[str, Any] = {
            "schema_version": RENDER_SCHEMA_VERSION,
            "meta": {
                "observer": observer_id,
                "turn": self.turn,
                "zone": self.active_zone,
                "global_tension": self._tension(cluster),
                "current_mythos": lore,
                "q3_mask": self._q3_mask(cluster),
                "attention": self.attention_budget,
                "seed": self.seed,
                "ledger_head": head,
                "dynamics_version": self.dynamics_version,
                "mode": self.mode,
            },
            "entities": self._entity_payload(
                cluster,
                observer_id=observer_id,
                zone=self.active_zone,
                use_private=True,
            ),
            "narrative_log": self.story_log[-8:],
            "zones": None,
        }

        if full_ship and self.mode == "ship":
            payload["zones"] = {}
            for zname, zc in self.zones.items():
                zlore = LoreLexicon.get_state_lore(self._q3_mask(zc))
                payload["zones"][zname] = {
                    "mythos": zlore,
                    "q3_mask": self._q3_mask(zc),
                    "tension": self._tension(zc),
                    "entities": self._entity_payload(
                        zc, observer_id=observer_id, zone=zname, use_private=True
                    ),
                }
        return payload

    def wait(
        self,
        dt_scale: Optional[float] = None,
        *,
        steps: int = 1,
        zone: Optional[str] = None,
        observer_id: str = "system",
    ) -> Dict[str, Any]:
        """Evolve active zone (and soft-bridge ship peers)."""
        if zone:
            self.set_zone(zone)
        if dt_scale is None:
            dt_scale = MAX_STABLE_DT_SCALE
        if dt_scale > MAX_STABLE_DT_SCALE:
            dt_scale = MAX_STABLE_DT_SCALE

        # Capture pre checkpoint for ledger
        if self.ledger:
            self._last_checkpoint = Checkpoint.from_cluster(
                f"pre_wait_{self.turn}", float(self.turn), self.cluster
            )
            # Continuity: pre hash must match last post — re-sync if drifted via bridges
            if getattr(self, "_last_post_hash", None) and (
                self._last_checkpoint.state_hash != self._last_post_hash
            ):
                # Bridges / other zones may have nudged us; open a new anchor
                self._last_post_hash = self._last_checkpoint.state_hash

        cassette_events = []
        ev = evolve_event(dt_scale=dt_scale, steps=steps)
        apply_event(self.cluster, ev)
        self._berry.observe_after(self.cluster, ev)
        cassette_events.append(ev)

        # Stamp the pure evolve cassette first (before soft bridges touch peers).
        if self.ledger:
            try:
                self._stamp_segment(
                    tuple(cassette_events),
                    observer_id,
                    "wait",
                    (self.active_zone,),
                )
            except ValueError:
                self._last_checkpoint = Checkpoint.from_cluster(
                    f"reanchor_{self.turn}", float(self.turn), self.cluster
                )
                self._last_post_hash = self._last_checkpoint.state_hash

        if self.apply_bridges:
            logs = apply_cross_zone_bridges(self.zones)
            for line in logs[:2]:
                self.story_log.append(f"[BRIDGE] {line}")
            # Bridges may nudge the active zone; re-anchor so the next cert is honest.
            if self.ledger:
                self._last_checkpoint = Checkpoint.from_cluster(
                    f"post_bridge_{self.turn}", float(self.turn), self.cluster
                )
                self._last_post_hash = self._last_checkpoint.state_hash

        self.turn += 1
        lore = LoreLexicon.get_state_lore(self._q3_mask())
        self.story_log.append(
            f"The manifold drifts. Resonance: {lore['emoji']} {lore['name']}."
        )

        return self.status(observer_id)


    def look(
        self,
        observer_id: str,
        target_role: str,
        *,
        zone: Optional[str] = None,
        strength: float = 1.0,
    ) -> Dict[str, Any]:
        """LOOK / measure one role (spends attention)."""
        if zone:
            self.set_zone(zone)
        cluster = self.cluster
        if target_role not in cluster.role_index:
            raise ValueError(
                f"unknown role {target_role!r}; try one of {list(cluster.qubit_roles)}"
            )
        if self.attention_budget is not None and self.attention_budget < LOOK_ATTENTION_COST:
            self.story_log.append("[FOG] Not enough attention to pierce the aether.")
            return self.status(observer_id)

        if self.ledger:
            self._last_checkpoint = Checkpoint.from_cluster(
                f"pre_look_{self.turn}", float(self.turn), cluster
            )
            if getattr(self, "_last_post_hash", None) and (
                self._last_checkpoint.state_hash != self._last_post_hash
            ):
                self._last_post_hash = self._last_checkpoint.state_hash

        z_before = float(cluster.role_bloch(target_role)[2])
        p_plus = (z_before + 1.0) / 2.0
        outcome = 1.0 if self.rng.random() < p_plus else -1.0
        ev = measure_event(target_role, record_z=outcome, strength=strength)
        apply_event(cluster, ev)
        self._berry.observe_after(cluster, ev)

        if self.attention_budget is not None:
            self.attention_budget -= LOOK_ATTENTION_COST

        # Private mind: observer snaps toward ground; others lag
        if self.private_observers:
            self._sync_belief_from_ground(observer_id, self.active_zone, alpha=1.0)
            for other in self._beliefs:
                if other != observer_id and self.active_zone in self._beliefs[other]:
                    # Hear a rumor: partial pull
                    self._sync_belief_from_ground(other, self.active_zone, alpha=0.25)

        self.turn += 1
        lore = LoreLexicon.get_state_lore(self._q3_mask())
        self.story_log.append(
            f"{observer_id} LOOKed at {target_role} (z→{outcome:+.0f}). "
            f"Reality: {lore['emoji']} {lore['name']}."
        )

        if self.ledger:
            try:
                self._stamp_segment(
                    (ev,),
                    observer_id,
                    "look",
                    (self.active_zone, target_role),
                )
            except ValueError:
                self._last_checkpoint = Checkpoint.from_cluster(
                    f"reanchor_{self.turn}", float(self.turn), self.cluster
                )
                self._last_post_hash = self._last_checkpoint.state_hash

        return self.status(observer_id)

    def stir(self, observer_id: str = "system") -> Dict[str, Any]:
        """Escape hatch: add transverse field kick so poles can unlock."""
        c = self.cluster
        h = np.array(c._h, dtype=float)
        for i in range(c.n_qubits):
            h[i, 0] += STIR_TRANSVERSE * (0.5 + self.rng.random())
        c.set_couplings(h_fields=h.tolist())
        return self.wait(
            dt_scale=STIR_DT_SCALE,
            steps=STIR_STEPS,
            observer_id=observer_id,
        )

    def weave(self, start_mask: int, end_mask: int) -> str:
        """Symbolic Q3 path story (not a dynamical certificate)."""
        text = EndlessKnotWeaver.weave_insertion(start_mask, end_mask)
        self.story_log.append(text.split("\n")[0])
        return text

    def quest_status(self) -> List[Dict[str, Any]]:
        out = []
        for zone, target in self.quests:
            if zone not in self.zones:
                continue
            mask = self._q3_mask(self.zones[zone])
            lore = LoreLexicon.get_state_lore(target)
            out.append(
                {
                    "zone": zone,
                    "target_mask": target,
                    "target_lore": lore,
                    "current_mask": mask,
                    "complete": mask == target,
                }
            )
        return out

    def victory(self) -> bool:
        if not self.quests:
            return False
        return all(q["complete"] for q in self.quest_status())

    def validate_payload(self, payload: Optional[Dict[str, Any]] = None) -> List[str]:
        return validate_render_state(payload or self.status("player"))
