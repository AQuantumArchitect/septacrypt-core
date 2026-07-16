"""Symbolic retro-insertion solver (Q3 graph grammar — not dynamical certificates)."""
from __future__ import annotations

from typing import Dict, List

from ..geometry.paths import build_causal_cone, find_q3_paths


class RetroSolver:
    """
    Microscope-style symbolic timeline weaver.

    Finds Hamming-1 paths on the Q3 cube. Does NOT prove the cumulant substrate
    can realize those paths — use TransitionCertificate / GameSession for that.
    """

    def __init__(self, allowed_states: List[int]):
        self.allowed_states = list(allowed_states)

    def build_causal_cone(self, start_mask: int, max_depth: int) -> Dict[int, List[int]]:
        return build_causal_cone(
            start_mask, max_depth, allowed_states=self.allowed_states
        )

    def solve_insertion(
        self, anchor_a: int, anchor_d: int, max_steps: int = 3
    ) -> List[List[int]]:
        return find_q3_paths(
            anchor_a,
            anchor_d,
            max_steps=max_steps,
            allowed_states=self.allowed_states,
        )
