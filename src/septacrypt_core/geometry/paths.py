"""Shared Q3 symbolic pathfinding (Hamming-1 graph grammar)."""
from __future__ import annotations

from typing import Dict, List

from ..dynamics.transition import TransitionVerifier

Q3_STATES: List[int] = [0b000, 0b001, 0b010, 0b011, 0b100, 0b101, 0b110, 0b111]


def find_q3_paths(
    start_mask: int,
    end_mask: int,
    *,
    max_steps: int = 3,
    allowed_states: List[int] | None = None,
) -> List[List[int]]:
    """All simple Hamming-1 paths from start to end within max_steps (symbolic only)."""
    allowed = allowed_states if allowed_states is not None else Q3_STATES
    if start_mask == end_mask:
        return [[start_mask]]

    paths: List[List[int]] = []

    def dfs(current: int, target: int, path: List[int]) -> None:
        if len(path) - 1 > max_steps:
            return
        if current == target:
            paths.append(list(path))
            return
        for neighbor in allowed:
            if TransitionVerifier.is_q3_adjacent(current, neighbor) and neighbor not in path:
                dfs(neighbor, target, path + [neighbor])

    dfs(start_mask, end_mask, [start_mask])
    return paths


def build_causal_cone(
    start_mask: int,
    max_depth: int,
    *,
    allowed_states: List[int] | None = None,
) -> Dict[int, List[int]]:
    """BFS neighborhood of Q3-adjacent states out to max_depth."""
    allowed = allowed_states if allowed_states is not None else Q3_STATES
    cone: Dict[int, List[int]] = {}
    queue = [(start_mask, 0)]
    visited = {start_mask}

    while queue:
        current, depth = queue.pop(0)
        if depth >= max_depth:
            if current not in cone:
                cone[current] = []
            continue
        neighbors = []
        for candidate in allowed:
            if TransitionVerifier.is_q3_adjacent(current, candidate):
                neighbors.append(candidate)
                if candidate not in visited:
                    visited.add(candidate)
                    queue.append((candidate, depth + 1))
        cone[current] = neighbors
    return cone
