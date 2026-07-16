import cmath
from typing import List
from ..dynamics.transition import QuantumState3Qubit
from .lexicon import LoreLexicon

class NarrativeBraid:
    """
    Weaves cold mathematical state changes into subjective story arcs.
    """
    @staticmethod
    def calculate_narrative_tension_from_raw(matrix) -> float:
        """
        Quantum Superposition = Narrative Tension.
        Sum of the magnitudes of all off-diagonal coherences of an NxN density
        matrix. Dimension-agnostic (not hardcoded to 3-qubit/8x8) so it can be
        fed umwelt's Lindblad density matrices directly, not just our own
        QuantumState3Qubit's fixed 8x8 shape. Accepts a nested list or a numpy
        array — both support len()/indexing/abs() the same way here.
        """
        n = len(matrix)
        tension = 0.0
        for i in range(n):
            for j in range(n):
                if i != j:
                    tension += abs(matrix[i][j])
        return round(tension, 3)

    @classmethod
    def calculate_narrative_tension(cls, rho: QuantumState3Qubit) -> float:
        return cls.calculate_narrative_tension_from_raw(rho.matrix)

    @classmethod
    def weave_story(cls, path: List[int], observer_id: str, tension_peaks: List[float] = None) -> str:
        """
        Translates a discrete physical path through Q3 into a subjective Fledgeling myth.
        """
        story = [f"--- The Braid of {observer_id.capitalize()} ---"]

        # Start state
        start_lore = LoreLexicon.get_state_lore(path[0])
        story.append(f"The manifold hummed in the state of {start_lore['emoji']} {start_lore['name']}.")

        for i in range(len(path) - 1):
            source = path[i]
            target = path[i+1]
            diff = source ^ target

            # Determine if a principle was added or removed
            added = target > source
            active_bit = diff

            principle = "father" if active_bit == 0b100 else ("son" if active_bit == 0b010 else "spirit")
            target_lore = LoreLexicon.get_state_lore(target)

            if added:
                verb = LoreLexicon.TRANSITION_VERBS.get((principle, target), "shifted into")
                action_str = f"The thread of the {principle.capitalize()} was woven, and reality {verb} {target_lore['emoji']} {target_lore['name']}."
            else:
                action_str = f"The thread of the {principle.capitalize()} was violently severed. The manifold plummeted into {target_lore['emoji']} {target_lore['name']}."

            story.append(action_str)

            if tension_peaks and i < len(tension_peaks):
                t = tension_peaks[i]
                if t > 0:
                    story.append(f"Tension spiked to {t} as the aether writhed in superposition.")

        story.append("I observed the silence. The timeline was rewritten.")
        return "\n".join(story)
