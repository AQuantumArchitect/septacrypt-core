"""Playtester bots, driven entirely through GameSession's public API (wait/
look/status/quest_status/victory/stir) -- never through World/WorldStepper/
CertifiedTransaction directly. Monte Carlo simulation is meant to layer
outside the hardened transaction layer, not reimplement it.
"""
import random
from typing import Optional, Tuple

from ..api.session import GameSession
from ..scenario.params import GREEDY_TENSION_THRESHOLD


def _active_quest(game: GameSession) -> Optional[Tuple[str, int]]:
    for q in game.quest_status():
        if not q["complete"]:
            return q["zone"], q["target_mask"]
    return None


def _is_locked(entities: dict, threshold: float = 0.95) -> bool:
    """True if every role in this zone is saturated near a pole -- the
    self-reinforcing 'Cosmic Dance' absorbing state a hard LOOK can't escape
    (each LOOK just reconfirms the same near-certain outcome). STIR is the
    documented escape hatch for exactly this case."""
    return all(abs(e["raw_metrics"]["z_axis"]) >= threshold for e in entities.values())


class BaseBot:
    def __init__(self, name: str, seed: Optional[int] = None):
        self.name = name
        self.rng = random.Random(seed)

    def play_turn(self, game: GameSession) -> str:
        raise NotImplementedError


class RandomBot(BaseBot):
    """Spends attention wildly and waits randomly. Baseline, not a player model."""

    def play_turn(self, game: GameSession) -> str:
        active = _active_quest(game)
        if active is None:
            return "VICTORY"
        zone, _target = active

        action = self.rng.choice(["WAIT", "LOOK"])
        if action == "WAIT":
            # GameSession.wait clamps dt_scale to MAX_STABLE_DT_SCALE itself
            # (WorldStepper.plan_world_step), so this range is safe even
            # without an explicit cap on this side.
            game.wait(dt_scale=self.rng.uniform(0.2, 1.0), zone=zone)
            return "WAIT"
        if game.attention_budget is None or game.attention_budget >= 1.0:
            state = game.status(self.name, zone=zone)
            target_role = self.rng.choice(list(state["entities"].keys()))
            game.look(self.name, target_role, zone=zone)
            return "LOOK"
        game.wait(zone=zone)
        return "WAIT"


class GreedyTensionBot(BaseBot):
    """QA/stress-test style: waits for tension to build, then collapses the
    lowest-confidence node. Not intended as a realistic player proxy -- it
    tests whether the couplings ever produce a resolvable high-tension
    window, the way a tester deliberately courts edge conditions."""

    def play_turn(self, game: GameSession) -> str:
        active = _active_quest(game)
        if active is None:
            return "VICTORY"
        zone, _target = active

        state = game.status(self.name, zone=zone)
        entities = state["entities"]

        if _is_locked(entities):
            game.stir()
            return "STIR"

        if state["meta"]["global_tension"] < GREEDY_TENSION_THRESHOLD:
            game.wait(zone=zone)
            return "WAIT"

        if game.attention_budget is None or game.attention_budget >= 1.0:
            target_role = min(entities.keys(), key=lambda k: entities[k]["raw_metrics"]["radius"])
            game.look(self.name, target_role, zone=zone)
            return "LOOK"

        game.wait(zone=zone)
        return "WAIT"


class TargetBitBot(BaseBot):
    """Smarter playtester: measure whichever role's pole currently disagrees
    with the quest's target bit, preferring the most confidently-wrong one.
    Falls back to STIR when locked near poles that don't match the target."""

    # role order within a zone is (father, son, spirit) by construction --
    # see scenario/reactor.py and scenario/params.py ZONE_ROLES.
    _BITS = (0b100, 0b010, 0b001)

    def play_turn(self, game: GameSession) -> str:
        active = _active_quest(game)
        if active is None:
            return "VICTORY"
        zone, target_mask = active

        state = game.status(self.name, zone=zone)
        entities = state["entities"]
        roles = list(entities.keys())

        disagree = []
        for role, bit in zip(roles, self._BITS):
            z = entities[role]["raw_metrics"]["z_axis"]
            want_plus = bool(target_mask & bit)
            is_plus = z > 0
            if want_plus != is_plus:
                disagree.append((role, abs(z)))

        if not disagree:
            game.wait(zone=zone)
            return "WAIT"

        if _is_locked(entities):
            game.stir()
            return "STIR"

        if game.attention_budget is None or game.attention_budget >= 1.0:
            # Flip the most confidently-wrong role first.
            disagree.sort(key=lambda x: -x[1])
            game.look(self.name, disagree[0][0], zone=zone)
            return "LOOK"

        game.wait(zone=zone)
        return "WAIT"


class TensionRelieverBot(BaseBot):
    """The realistic default player proxy.

    GreedyTensionBot and TargetBitBot behave like QA testers: one waits to
    deliberately court a high-tension window, the other hunts for exactly
    the wrong bit. A real player isn't running an adversarial search -- they
    default to reducing uncertainty wherever it's currently worst, every
    turn attention allows, without waiting for a threshold to be crossed
    first. This bot always resolves the foggiest (lowest-confidence) role in
    the active quest's zone immediately, and reaches for STIR the moment
    it's locked near poles instead of wasting attention re-confirming a
    dead end.
    """

    def play_turn(self, game: GameSession) -> str:
        active = _active_quest(game)
        if active is None:
            return "VICTORY"
        zone, _target = active

        if game.attention_budget is not None and game.attention_budget < 1.0:
            game.wait(zone=zone)
            return "WAIT"

        state = game.status(self.name, zone=zone)
        entities = state["entities"]

        if _is_locked(entities):
            game.stir()
            return "STIR"

        target_role = min(entities.keys(), key=lambda k: entities[k]["raw_metrics"]["radius"])
        game.look(self.name, target_role, zone=zone)
        return "LOOK"
