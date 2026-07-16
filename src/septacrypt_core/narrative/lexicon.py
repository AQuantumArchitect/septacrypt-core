class LoreLexicon:
    """
    Translates quantum states and hypercube edges into diegetic Fledgeling myth.
    """
    # 8 Basis States as Narrative Settings
    STATE_MYTHOS = {
        0b000: {"emoji": "🌌", "name": "The Holy Dark", "desc": "the aetheric substrate where all possibilities sleep"},
        0b001: {"emoji": "📖", "name": "The Open Book", "desc": "a harmonic state of expressed truth and wisdom"},
        0b010: {"emoji": "⚔️", "name": "The Naked Blade", "desc": "a raw expression of unchecked might"},
        0b100: {"emoji": "🪙", "name": "The Vault", "desc": "a quiet accumulation of wealth and latent potential"},
        0b011: {"emoji": "🔥", "name": "The Furnace", "desc": "a dynamic, raging expression of power"},
        0b101: {"emoji": "✨", "name": "The Crown", "desc": "a state of majestic order and glory"},
        0b110: {"emoji": "🛡️", "name": "The Shield", "desc": "a secure, unyielding matrix of honor"},
        0b111: {"emoji": "🌟", "name": "The Cosmic Dance", "desc": "a complete harmony of blessing"},
    }

    # The 12 Pearls (Oriented transitions mapping generator to state)
    # Format: (added_principle, resulting_state) -> Narrative Action
    TRANSITION_VERBS = {
        ("father", 0b100): "forged the foundation of",
        ("father", 0b101): "crowned the aether with",
        ("father", 0b110): "reinforced the structure of",
        ("father", 0b111): "bestowed absolute wealth upon",
        ("son", 0b010): "struck with the raw force of",
        ("son", 0b011): "ignited the engines of",
        ("son", 0b110): "mobilized the defenses of",
        ("son", 0b111): "incarnated the absolute action of",
        ("spirit", 0b001): "whispered the cosmic breath into",
        ("spirit", 0b011): "awakened the dynamic power of",
        ("spirit", 0b101): "illuminated the glory of",
        ("spirit", 0b111): "breathed ultimate harmony into",
    }

    @classmethod
    def get_state_lore(cls, mask: int) -> dict:
        return cls.STATE_MYTHOS.get(mask, {"emoji": "❓", "name": "The Unknown", "desc": "an unmapped anomaly"})
