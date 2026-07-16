from typing import List, Tuple, Dict, Any, Optional
from ..dynamics.transition import TransitionVerifier, QuantumState3Qubit

class RetroSolver:
    """
    Microscope-style timeline weaver. Searches for valid transition paths
    between two anchor states that satisfy strict Q3 graph adjacencies.
    """
    def __init__(self, allowed_states: List[int]):
        self.allowed_states = allowed_states

    def build_causal_cone(self, start_mask: int, max_depth: int) -> Dict[int, List[int]]:
        """
        Constructs the local causal neighborhood by walking valid physical edges of Q3.
        """
        cone = {}
        queue = [(start_mask, 0)]
        visited = {start_mask}

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            cone[current] = []
            for candidate in self.allowed_states:
                if TransitionVerifier.is_q3_adjacent(current, candidate):
                    cone[current].append(candidate)
                    if candidate not in visited:
                        visited.add(candidate)
                        queue.append((candidate, depth + 1))
        return cone

    def solve_insertion(self, anchor_a: int, anchor_d: int, max_steps: int = 3) -> List[List[int]]:
        """
        Finds all physically valid paths connecting anchor_a to anchor_d
        within the step budget, strictly respecting Q3 edge transitions.
        """
        if anchor_a == anchor_d:
            return [[anchor_a]]

        paths = []
        # DFS with depth limit to locate paths
        def dfs(current: int, target: int, current_path: List[int]):
            if len(current_path) - 1 > max_steps:
                return
            if current == target:
                paths.append(list(current_path))
                return

            for neighbor in self.allowed_states:
                if TransitionVerifier.is_q3_adjacent(current, neighbor):
                    if neighbor not in current_path: # Prevent loops in a single path
                        dfs(neighbor, target, current_path + [neighbor])

        dfs(anchor_a, anchor_d, [anchor_a])
        return paths
