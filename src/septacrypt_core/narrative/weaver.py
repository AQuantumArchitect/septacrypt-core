from typing import List
from ..dynamics.transition import TransitionVerifier
from .lexicon import LoreLexicon

class EndlessKnotWeaver:
    """
    The Microscope-style retro-insertion solver.
    Allows players to weave new timeline paths between established stamps.
    """
    ALLOWED_STATES = [0b000, 0b001, 0b010, 0b011, 0b100, 0b101, 0b110, 0b111]

    @classmethod
    def find_valid_paths(cls, start_mask: int, end_mask: int, max_steps: int = 3) -> List[List[int]]:
        """DFS pathfinder respecting Q3 Hamming-1 adjacency."""
        if start_mask == end_mask:
            return [[start_mask]]

        valid_paths = []
        def dfs(current: int, target: int, path: List[int]):
            if len(path) - 1 > max_steps:
                return
            if current == target:
                valid_paths.append(list(path))
                return
            for neighbor in cls.ALLOWED_STATES:
                if TransitionVerifier.is_q3_adjacent(current, neighbor) and neighbor not in path:
                    dfs(neighbor, target, path + [neighbor])

        dfs(start_mask, end_mask, [start_mask])
        return valid_paths

    @classmethod
    def weave_insertion(cls, start_mask: int, end_mask: int) -> str:
        """Finds paths and generates the Fledgeling mythos for the intervention."""
        paths = cls.find_valid_paths(start_mask, end_mask)
        if not paths:
            return "[WEAVER] The laws of the manifold reject this insertion. Teleportation is forbidden."

        best_path = paths[0]  # Simplest/shortest path
        story = [f"[WEAVER] Retroactive insertion successful. The timeline flexes:"]

        for i in range(len(best_path) - 1):
            source = best_path[i]
            target = best_path[i+1]
            added = target > source
            principle = "father" if (source ^ target) == 0b100 else ("son" if (source ^ target) == 0b010 else "spirit")
            target_lore = LoreLexicon.get_state_lore(target)

            if added:
                verb = LoreLexicon.TRANSITION_VERBS.get((principle, target), "shifted into")
                story.append(f"  -> The {principle.capitalize()} was woven, anchoring {target_lore['emoji']} {target_lore['name']}.")
            else:
                story.append(f"  -> The {principle.capitalize()} was severed, dropping the manifold to {target_lore['emoji']} {target_lore['name']}.")

        return "\n".join(story)
