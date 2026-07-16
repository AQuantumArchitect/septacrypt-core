"""
GameSession — public facade over hardened world runtime.

Internals: World, WorldStepper, CertifiedTransaction, ObserverBeliefStore,
NarrativeProjector, CampaignController. Do not put new cosmology here.
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..dynamics.version import DYNAMICS_VERSION, MAX_STABLE_DT_SCALE
from ..geometry.atlas import bloch_to_septacrypt
from ..ledger.certificate import mint_empty_certificate
from ..ledger.checkpoint import Checkpoint
from ..ledger.dag import KnotLedger
from ..ledger.events import (
    Cassette,
    demote_routine_event,
    measure_event,
    promote_routine_event,
    report_event,
    set_fields_event,
    world_evolve_event,
)
from ..ledger.stamp import KnotStamp
from ..geometry.address import ScaleAddress
from ..observers.beliefs import ObserverBeliefStore
from ..scenario.params import (
    DEFAULT_ATTENTION,
    LOOK_ATTENTION_COST,
    STIR_DT_SCALE,
    STIR_H_MAX,
    STIR_STEPS,
    STIR_TRANSVERSE,
)
from ..world.snapshot import World
from ..world.stepper import WorldStepper
from ..world.transaction import CertifiedTransaction, TransactionError
from .campaign_ctrl import CampaignController
from .narrative import NarrativeProjector
from .schema import RENDER_SCHEMA_VERSION, validate_render_state


class GameSession:
    """
    Playable session facade.

    Modes: reactor | ship
    enable_ledger: fail-closed certified commits (no silent re-anchor)
    private_observers: observer_view derived from beliefs only
    """

    def __init__(
        self,
        *,
        mode: str = "reactor",
        seed: Optional[int] = None,
        enable_ledger: bool = True,
        private_observers: bool = True,
        attention_budget: Optional[float] = DEFAULT_ATTENTION,
        apply_bridges: bool = True,
        include_ground_debug: bool = False,
    ):
        if mode not in ("reactor", "ship"):
            raise ValueError("mode must be 'reactor' or 'ship'")
        self.mode = mode
        self.seed = seed
        self.enable_ledger = enable_ledger
        self.private_observers = private_observers
        self.attention_budget = attention_budget
        self.include_ground_debug = include_ground_debug
        self.dynamics_version = DYNAMICS_VERSION

        if mode == "reactor":
            self.world = World.reactor(seed=seed)
            self._bridges = False
        else:
            self.world = World.ship(seed=seed, bridges_enabled=apply_bridges)
            self._bridges = apply_bridges

        self.ledger = KnotLedger() if enable_ledger else None
        self._branch = "main"
        self.beliefs = ObserverBeliefStore()
        self.narrative = NarrativeProjector()
        self.campaign = CampaignController() if mode == "ship" else CampaignController(quests=[])
        self.stepper = WorldStepper()

        if self.ledger:
            self._genesis()

    # ── properties for compatibility ───────────────────────────────────

    @property
    def turn(self) -> int:
        return self.world.turn

    @property
    def cluster(self):
        return self.world.cluster

    @property
    def zones(self):
        return self.world.zones

    @property
    def active_zone(self) -> str:
        return self.world.active_zone

    @property
    def story_log(self) -> List[str]:
        return self.narrative.log

    def zone_names(self) -> List[str]:
        return self.world.zone_names()

    def set_zone(self, zone: str) -> None:
        """Presentation only — does not change which systems evolve."""
        self.world.set_active_zone(zone)

    def _genesis(self) -> None:
        snap = self.world.snapshot()
        h = self.world.physics_hash()
        cp = Checkpoint(
            checkpoint_id="genesis",
            chronological_time=0.0,
            state_data=snap.to_dict(),
            state_hash=h,
        )
        cert = mint_empty_certificate(cp)
        # Align empty cert roots with world hash
        from dataclasses import replace
        from ..ledger.stamp import TransitionCertificate

        cert = TransitionCertificate(
            dynamics_version=cert.dynamics_version,
            pre_state_root=h,
            post_state_root=h,
            event_digest=cert.event_digest,
            chronological_interval=(0.0, 0.0),
            residual=0.0,
            tolerance=cert.tolerance,
            rng_commitment=cert.rng_commitment,
            replay_cassette=cert.replay_cassette,
            affected_surface=(),
            hidden_conditions=cert.hidden_conditions,
        )
        stamp = KnotStamp(
            stamp_id="pending",
            parent_ids=(),
            branch_id=self._branch,
            event_kind="init",
            actor_id=None,
            observer_id="system",
            chronological_time=0.0,
            berry_coordinate={"schema": "berry.world.v1", "path_signature": "seed"},
            scale_address=ScaleAddress(("world",)),
            pre_state_root=h,
            post_state_root=h,
            transition_certificate_id="pending",
            truth_mode="observed",
            confidence=1.0,
            spirit_vector=None,
        )
        self.ledger.append_stamp(stamp, certificate=cert, expected_branch_head=None)

    def _commit(self, cassette: Cassette, *, observer_id: str, event_kind: str, scale: Sequence[str]) -> None:
        pre_hash = self.world.physics_hash()
        head = self.ledger.branches.get(self._branch) if self.ledger else None
        try:
            CertifiedTransaction.execute(
                self.world,
                cassette,
                ledger=self.ledger if self.enable_ledger else None,
                branch_id=self._branch,
                expected_branch_head=head,
                observer_id=observer_id,
                event_kind=event_kind,
                scale_parts=scale,
                require_certificate=bool(self.enable_ledger and self.ledger),
            )
        except TransactionError:
            # Fail closed: world untouched
            assert self.world.physics_hash() == pre_hash
            raise
        # Epistemic updates after successful commit
        for event in cassette:
            self.beliefs.apply_event(self.world, event, self.world.turn)

    def _apply_uncertified(self, cassette: Cassette) -> None:
        """Ledger off: still apply via working clone for consistency."""
        CertifiedTransaction.execute(
            self.world,
            cassette,
            ledger=None,
            require_certificate=False,
            observer_id="system",
            event_kind="segment",
        )
        for event in cassette:
            self.beliefs.apply_event(self.world, event, self.world.turn)

    def _run(self, cassette: Cassette, **kwargs) -> None:
        if self.enable_ledger and self.ledger:
            self._commit(cassette, **kwargs)
        else:
            self._apply_uncertified(cassette)

    # ── commands ───────────────────────────────────────────────────────

    def wait(
        self,
        dt_scale: Optional[float] = None,
        *,
        steps: int = 1,
        zone: Optional[str] = None,
        observer_id: str = "system",
    ) -> Dict[str, Any]:
        if zone is not None:
            self.set_zone(zone)  # presentation only
        if dt_scale is None:
            dt_scale = MAX_STABLE_DT_SCALE
        cassette = self.stepper.plan_world_step(
            dt_scale=dt_scale,
            steps=steps,
            apply_bridges=self._bridges,
        )
        self._run(cassette, observer_id=observer_id, event_kind="wait", scale=("world",))
        lore = self.narrative.mythos(self._ground_mask(self.world.active_zone))
        self.narrative.append(
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
        if zone is not None:
            self.set_zone(zone)
        zname = self.world.active_zone
        cluster = self.world.zones[zname]
        if target_role not in cluster.role_index:
            raise ValueError(f"unknown role {target_role!r}; try {list(cluster.qubit_roles)}")
        if self.attention_budget is not None and self.attention_budget < LOOK_ATTENTION_COST:
            self.narrative.append("[FOG] Not enough attention to pierce the aether.")
            return self.status(observer_id)

        # Sample outcome without permanently advancing live RNG until commit.
        # role_bloch is a pure read on the live cluster; only the RNG state
        # needs isolating, so copy that instead of cloning the whole world.
        probe_rng = random.Random()
        probe_rng.setstate(self.world.rng.getstate())
        z_before = float(cluster.role_bloch(target_role)[2])
        p_plus = (z_before + 1.0) / 2.0
        u = probe_rng.random()
        outcome = 1.0 if u < p_plus else -1.0

        ev = measure_event(
            target_role,
            outcome,
            zone=zname,
            strength=strength,
            observer_id=observer_id,
        )
        # Attach rng draw for replay-aligned consumption
        from dataclasses import replace
        from ..ledger.events import KnotEvent

        ev = KnotEvent(
            kind="measure",
            parameters={**ev.parameters, "rng_draws": [u]},
        )
        cassette: Cassette = (ev,)

        pre_hash = self.world.physics_hash()
        try:
            self._run(
                cassette,
                observer_id=observer_id,
                event_kind="look",
                scale=(zname, target_role),
            )
        except TransactionError:
            assert self.world.physics_hash() == pre_hash
            raise

        if self.attention_budget is not None:
            self.attention_budget -= LOOK_ATTENTION_COST

        lore = self.narrative.mythos(self.beliefs.q3_mask(observer_id, zname, self.world))
        self.narrative.append(
            f"{observer_id} LOOKed at {target_role} (z→{outcome:+.0f}). "
            f"Belief: {lore['emoji']} {lore['name']}."
        )
        return self.status(observer_id)

    def stir(self, observer_id: str = "system") -> Dict[str, Any]:
        """Escape hatch: typed field update then world step — fully cassettable."""
        events = []
        for zname, cluster in self.world.zones.items():
            h = np.array(cluster._h, dtype=float).tolist()
            # Record intended new fields from probe RNG without mutating live.
            # NOTE: probe RNG is reset from live state per zone (preserving the
            # legacy per-zone world.clone() behavior exactly — every zone sees
            # the same draw sequence), so recorded fields stay hash-compatible.
            probe_rng = random.Random()
            probe_rng.setstate(self.world.rng.getstate())
            h_new = []
            draws = []
            for i, row in enumerate(h):
                u = probe_rng.random()
                draws.append(u)
                row = list(row)
                # Cap accumulated transverse field: unbounded growth over many
                # STIRs drives RK4 unstable (see STIR_H_MAX in params).
                row[0] = min(float(row[0]) + STIR_TRANSVERSE * (0.5 + u), STIR_H_MAX)
                h_new.append(row)
            # Use same draws on live via set_fields (no rng in set_fields) —
            # fields fully recorded
            events.append(set_fields_event(zname, h_new))
        events.extend(
            self.stepper.plan_world_step(
                dt_scale=STIR_DT_SCALE,
                steps=STIR_STEPS,
                apply_bridges=self._bridges,
            )
        )
        self._run(tuple(events), observer_id=observer_id, event_kind="stir", scale=("world", "stir"))
        self.narrative.append("[STIR] Transverse field event applied across the world.")
        return self.status(observer_id)

    def report(
        self,
        source_observer: str,
        target_observer: str,
        role: str,
        *,
        zone: Optional[str] = None,
        confidence: float = 0.35,
        channel: str = "heard_report",
    ) -> Dict[str, Any]:
        """Typed communication — no automatic rumor on LOOK."""
        zname = zone or self.world.active_zone
        # Report what source currently believes (or ground if they observed)
        z_val = self.beliefs.bloch(source_observer, zname, role, self.world)[2]
        ev = report_event(
            source_observer,
            target_observer,
            zone=zname,
            role=role,
            z_value=z_val,
            confidence=confidence,
            channel=channel,
        )
        # Report is epistemic; still go through transaction for ledger honesty
        self._run((ev,), observer_id=source_observer, event_kind="report", scale=("report",))
        self.narrative.append(
            f"{source_observer} reports {role} to {target_observer} via {channel}."
        )
        return self.status(target_observer)

    def promote_routine(self, name: str, actor_id: str, evidence: str = "") -> Dict[str, Any]:
        ev = promote_routine_event(name, actor_id, evidence=evidence)
        self._run((ev,), observer_id=actor_id, event_kind="promote_routine", scale=("routine", name))
        return self.status(actor_id)

    def demote_routine(self, name: str, actor_id: str, reason: str = "") -> Dict[str, Any]:
        ev = demote_routine_event(name, actor_id, reason=reason)
        self._run((ev,), observer_id=actor_id, event_kind="demote_routine", scale=("routine", name))
        return self.status(actor_id)

    def register_routine(self, name: str, actor_id: str) -> None:
        """Shadow-first registration (not live until promote)."""
        self.world.routines[name] = {
            "shadow": True,
            "auto_live": False,
            "actor_id": actor_id,
        }

    def weave(self, start_mask: int, end_mask: int) -> str:
        return self.narrative.weave(start_mask, end_mask)

    def history(self, branch: Optional[str] = None) -> List[Dict[str, Any]]:
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

    def quest_status(self) -> List[Dict[str, Any]]:
        return self.campaign.status(self.world)

    def victory(self) -> bool:
        return self.campaign.victory(self.world)

    def physics_hash(self) -> str:
        return self.world.physics_hash()

    def _ground_mask(self, zone: str) -> int:
        c = self.world.zones[zone]
        return bloch_to_septacrypt([c.role_bloch(r) for r in c.qubit_roles])

    def _ground_tension(self, zone: str) -> float:
        cluster = self.world.zones[zone]
        n = cluster.n_qubits
        tension = 0.0
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                conn = cluster.e2[i, j] - np.outer(cluster.e1[i], cluster.e1[j])
                tension += float(abs(conn[2, 2]))
        return round(tension, 5)

    def status(
        self,
        observer_id: str = "player",
        *,
        zone: Optional[str] = None,
        full_ship: bool = False,
    ) -> Dict[str, Any]:
        if zone is not None:
            self.set_zone(zone)
        zname = self.world.active_zone
        head = self.ledger.branches.get(self._branch) if self.ledger else None

        if self.private_observers:
            oview = self.beliefs.observer_view(observer_id, self.world, zone=zname)
            entities = oview["entities"]
            mythos = oview["current_mythos"]
            q3 = oview["q3_mask"]
            tension = oview["uncertainty"]
        else:
            # Admin/shared presentation mode: ground-visible (explicit)
            mythos = self.narrative.mythos(self._ground_mask(zname))
            q3 = self._ground_mask(zname)
            tension = self._ground_tension(zname)
            entities = {}
            c = self.world.zones[zname]
            for role in c.qubit_roles:
                b = c.role_bloch(role)
                x, y, z = float(b[0]), float(b[1]), float(b[2])
                r = (x * x + y * y + z * z) ** 0.5
                entities[role] = {
                    "raw_metrics": {"z_axis": z, "radius": r, "phase_x": x, "phase_y": y},
                    "semantic": {
                        "inferred_state": "active" if z > 0 else "latent",
                        "view": "ground",
                    },
                }
            oview = None

        payload: Dict[str, Any] = {
            "schema_version": RENDER_SCHEMA_VERSION,
            "meta": {
                "observer": observer_id,
                "turn": self.world.turn,
                "zone": zname,
                "attention": self.attention_budget,
                "seed": self.seed,
                "ledger_head": head,
                "dynamics_version": self.dynamics_version,
                "mode": self.mode,
                # Observer-facing (not ground)
                "global_tension": tension,
                "current_mythos": mythos,
                "q3_mask": q3,
            },
            "observer_view": oview,
            "entities": entities,
            "narrative_log": self.narrative.recent(8),
            "public_world": {
                "turn": self.world.turn,
                "zone_names": self.zone_names(),
                "active_zone": zname,
                "topology_version": self.world.topology_version,
            },
            "zones": None,
            "ground_debug": None,
        }

        if full_ship and self.mode == "ship":
            payload["zones"] = {}
            for zn in self.zone_names():
                if self.private_observers:
                    ov = self.beliefs.observer_view(observer_id, self.world, zone=zn)
                    payload["zones"][zn] = {
                        "mythos": ov["current_mythos"],
                        "q3_mask": ov["q3_mask"],
                        "tension": ov["uncertainty"],
                        "entities": ov["entities"],
                    }
                else:
                    payload["zones"][zn] = {
                        "mythos": self.narrative.mythos(self._ground_mask(zn)),
                        "q3_mask": self._ground_mask(zn),
                        "tension": self._ground_tension(zn),
                    }

        if self.include_ground_debug:
            payload["ground_debug"] = {
                "warning": "Authoritative ground — disable for player-facing builds",
                "physics_hash": self.physics_hash()[:16],
                "q3_mask": self._ground_mask(zname),
                "mythos": self.narrative.mythos(self._ground_mask(zname)),
                "tension": self._ground_tension(zname),
            }

        return payload

    def validate_payload(self, payload: Optional[Dict[str, Any]] = None) -> List[str]:
        return validate_render_state(payload or self.status("player"))
