from typing import List

from ..geometry.paths import Q3_STATES, find_q3_paths
from .lexicon import LoreLexicon


class EndlessKnotWeaver:
    """
    Symbolic Microscope-style retro-insertion storyteller.
    Paths come from the shared Q3 pathfinder (graph grammar only).
    """

    ALLOWED_STATES = list(Q3_STATES)

    @classmethod
    def find_valid_paths(cls, start_mask: int, end_mask: int, max_steps: int = 3) -> List[List[int]]:
        return find_q3_paths(
            start_mask,
            end_mask,
            max_steps=max_steps,
            allowed_states=cls.ALLOWED_STATES,
        )

    @classmethod
    def weave_insertion(cls, start_mask: int, end_mask: int) -> str:
        """Finds paths and generates the Fledgeling mythos for the intervention."""
        paths = cls.find_valid_paths(start_mask, end_mask)
        if not paths:
            return "[WEAVER] The laws of the manifold reject this insertion. Teleportation is forbidden."

        best_path = min(paths, key=len)
        story = ["[WEAVER] Retroactive insertion successful. The timeline flexes:"]

        for i in range(len(best_path) - 1):
            source = best_path[i]
            target = best_path[i + 1]
            principle = (
                "father"
                if (source ^ target) == 0b100
                else ("son" if (source ^ target) == 0b010 else "spirit")
            )
            target_lore = LoreLexicon.get_state_lore(target)

            if target > source:
                story.append(
                    f"  -> The {principle.capitalize()} was woven, anchoring "
                    f"{target_lore['emoji']} {target_lore['name']}."
                )
            else:
                story.append(
                    f"  -> The {principle.capitalize()} was severed, dropping the manifold to "
                    f"{target_lore['emoji']} {target_lore['name']}."
                )

        return "\n".join(story)
