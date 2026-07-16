import cmath
from typing import Dict, List, Tuple

class EmojiGrammar:
    """
    Translates the rigorous math of the Q3 hypercube and Octahedral hubs
    into the expressive, highly readable emoji-noun language of the kernel.
    """
    # 1. The 6 Signed Generator Poles (Octahedron Vertices)
    POLES = {
        "+father": "👑",  # Wealth / Provision / Resource
        "-father": "🧱",  # Raw Structure / Foundation / Earth
        "+son":    "⚡",  # Might / Energy / Action
        "-son":    "🛠️",  # Work / Incarnation / Craft
        "+spirit": "🕊️",  # Wisdom / Breath / Intellect
        "-spirit": "🕯️",  # Focus / Intention / Inward Flame
    }

    # 2. The 8 Basis States (Octahedron Faces)
    # Each state is a specific combination of 3 signed poles (one from each generator axis).
    # Example: 0b111 (Blessing) is (+father, +son, +spirit) -> 👑⚡🕊️
    STATE_COMPOSITES: Dict[int, Tuple[str, str, str]] = {
        0b000: ("-father", "-son", "-spirit"),  # 🧱🛠️🕯️ -> Void
        0b001: ("-father", "-son", "+spirit"),  # 🧱🛠️🕊️ -> Wisdom
        0b010: ("-father", "+son", "-spirit"),  # 🧱⚡🕯️ -> Might
        0b100: ("+father", "-son", "-spirit"),  # 👑🛠️🕯️ -> Wealth
        0b011: ("-father", "+son", "+spirit"),  # 🧱⚡🕊️ -> Power
        0b101: ("+father", "-son", "+spirit"),  # 👑🛠️🕊️ -> Glory
        0b110: ("+father", "+son", "-spirit"),  # 👑⚡🕯️ -> Honor
        0b111: ("+father", "+son", "+spirit"),  # 👑⚡🕊️ -> Blessing
    }

    # Highly-expressive singular emojis representing each of the 8 basis states
    STATE_EMOJIS = {
        0b000: "🌌",  # Holy Dark / Void / Unexpressed Latency
        0b001: "📖",  # Wisdom / Expressed Truth
        0b010: "⚔️",  # Might / Active Force
        0b100: "🪙",  # Wealth / Stored Resource
        0b011: "🔥",  # Power / Dynamic Energy
        0b101: "✨",  # Glory / Majestic Order
        0b110: "🛡️",  # Honor / Secured Integrity
        0b111: "🌟",  # Blessing / Complete Harmony
    }

    @classmethod
    def get_poles_for_state(cls, mask: int) -> str:
        """Returns the 3-pole constituent emoji string for a state."""
        pole_keys = cls.STATE_COMPOSITES.get(mask, ())
        return "".join(cls.POLES[p] for p in pole_keys)

    @classmethod
    def get_state_emoji(cls, mask: int) -> str:
        """Returns the single expressive emoji representing the state."""
        return cls.STATE_EMOJIS.get(mask, "❓")

    @classmethod
    def format_pearl(cls, principle_name: str, state_mask: int) -> str:
        """
        Formats a Pearl (generator-to-state incidence) as an emoji transition.
        """
        principle_emoji = cls.POLES.get(f"+{principle_name}", "❓")
        state_emoji = cls.get_state_emoji(state_mask)
        return f"({principle_emoji} ──> {state_emoji})"

    @classmethod
    def format_density_matrix(cls, rho: List[List[complex]], threshold: float = 0.01) -> str:
        """
        Translates an 8x8 quantum density matrix into a beautifully formatted
        emoji superposition equation, including population probabilities and coherence phases.
        """
        terms = []
        for i in range(8):
            prob = rho[i][i].real
            if prob > threshold:
                state_emo = cls.get_state_emoji(i)
                # Check for off-diagonal phase coherence with other active states
                phase_details = []
                for j in range(8):
                    if i != j and abs(rho[i][j]) > threshold:
                        # Extract the relative phase angle
                        angle = cmath.phase(rho[i][j])
                        deg = round(angle * 180 / cmath.pi)
                        other_emo = cls.get_state_emoji(j)
                        phase_details.append(f"{deg}°~{other_emo}")

                phase_str = f" (cohered: {', '.join(phase_details)})" if phase_details else ""
                terms.append(f"{prob:.2f}|{state_emo}⟩{phase_str}")

        return " + ".join(terms) if terms else "0.00|🌌⟩"
