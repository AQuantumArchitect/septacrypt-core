from typing import Dict, List, Tuple

# 1. Three named binary generators
PRINCIPLES = {
    "father": 0b100,
    "son": 0b010,
    "spirit": 0b001
}

# 2. Eight basis masks (7 acclimations + 1 void)
STATES = {
    0b000: {"name": "Holy Dark", "class": "void_reference"},
    0b001: {"name": "Wisdom"},
    0b010: {"name": "Might"},
    0b100: {"name": "Wealth"},
    0b011: {"name": "Power"},
    0b101: {"name": "Glory"},
    0b110: {"name": "Honor"},
    0b111: {"name": "Blessing"}
}

NONZERO_STATES = [s for s in STATES.keys() if s != 0b000]

def generate_pearls() -> List[Tuple[str, int]]:
    """
    Generates the 12 Pearls.
    A Pearl is an incidence between an active generator and a composite state.
    """
    pearls = []
    for state in NONZERO_STATES:
        for principle_name, principle_mask in PRINCIPLES.items():
            # If the principle's bit is active in this state
            if state & principle_mask:
                pearls.append((principle_name, state))
    return pearls

def generate_transitions() -> List[Tuple[int, int]]:
    """
    Maps each Pearl to an oriented basis transition (clearing the active bit).
    This establishes the oriented edges of the Q3 hypercube toward 000.
    """
    transitions = []
    pearls = generate_pearls()
    for principle_name, state in pearls:
        principle_mask = PRINCIPLES[principle_name]
        cleared_state = state ^ principle_mask
        transitions.append((state, cleared_state))
    return transitions
