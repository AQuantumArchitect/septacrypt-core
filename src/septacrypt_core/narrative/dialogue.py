from ..spirit.vector import SpiritVector
from .lexicon import LoreLexicon

class IntentGenerator:
    """
    Translates an agent's internal 7D Spirit Vector into expressive SpaceWeave emoji dialogue.
    """
    @staticmethod
    def vocalize_desire(current_state: int, desired_bias: SpiritVector) -> str:
        current_lore = LoreLexicon.get_state_lore(current_state)

        # Determine primary alignment drive
        drive = "restoration"
        target_emoji = "🌟"
        if desired_bias.might > 0.8:
            drive = "destruction"
            target_emoji = "⚔️"
        elif desired_bias.wisdom > 0.8:
            drive = "contemplation"
            target_emoji = "📖"

        dialogue = (
            f"We are trapped in {current_lore['emoji']}. "
            f"The vectors demand {drive}. I must weave the knot toward {target_emoji}."
        )
        return dialogue
