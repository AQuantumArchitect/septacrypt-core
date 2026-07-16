"""Tunable scenario parameters — single place for game balance knobs."""
from __future__ import annotations

from typing import Dict, List, Tuple

# ── Reactor (single zone) ──────────────────────────────────────────────
REACTOR_ROLES: List[str] = ["valve_17", "coolant_pump", "temp_sensor"]
REACTOR_GAMMA: float = 0.02
REACTOR_DT: float = 0.1
REACTOR_ZZ: Dict[Tuple[int, int], float] = {
    (0, 1): 0.8,
    (1, 2): 0.5,
}
REACTOR_H_FIELDS: List[List[float]] = [
    [0.2, 0.0, 0.0],
    [0.2, 0.0, 0.0],
    [0.1, 0.0, 0.0],
]

# ── Ship manifold zones ────────────────────────────────────────────────
ZONE_ROLES: Dict[str, List[str]] = {
    "Reactor_Core": ["core_valve", "core_pump", "core_sensor"],
    "Navigation": ["nav_strut", "nav_thruster", "nav_lens"],
    "Life_Support": ["ls_filter", "ls_blower", "ls_monitor"],
}
ZONE_GAMMA: float = 0.03
ZONE_DT: float = 0.1
ZONE_ZZ: Dict[Tuple[int, int], float] = {(0, 1): 0.6, (1, 2): 0.4}
ZONE_H_FIELDS: List[List[float]] = [
    [0.15, 0.0, 0.0],
    [0.15, 0.0, 0.0],
    [0.1, 0.0, 0.0],
]

# Cross-zone soft bridges: (src_zone, src_role, dst_zone, dst_role, alpha)
# Applied after WAIT: partially nudges destination Bloch toward source z on σz.
# This is "society as braid" — not full joint Hamiltonian, but real coupling.
CROSS_ZONE_BRIDGES: List[Tuple[str, str, str, str, float]] = [
    ("Reactor_Core", "core_pump", "Navigation", "nav_thruster", 0.12),
    ("Reactor_Core", "core_pump", "Life_Support", "ls_blower", 0.10),
    ("Life_Support", "ls_monitor", "Reactor_Core", "core_sensor", 0.08),
    ("Navigation", "nav_lens", "Reactor_Core", "core_valve", 0.06),
]

# ── Campaign ───────────────────────────────────────────────────────────
DEFAULT_ATTENTION: float = 50.0
LOOK_ATTENTION_COST: float = 1.0
DEFAULT_QUESTS: List[Tuple[str, int]] = [
    ("Reactor_Core", 0b011),  # Power
    ("Navigation", 0b101),    # Glory
    ("Life_Support", 0b110),  # Honor
]

# Escape hatch when axes lock near poles (absorbing "Cosmic Dance" trap):
# small transverse stir strength applied by GameSession.stir()
STIR_TRANSVERSE: float = 0.25
STIR_DT_SCALE: float = 1.0
STIR_STEPS: int = 1
# Repeated STIRs accumulate on h[0]; uncapped they grow without bound and
# RK4 at dt=0.1 blows up (observed in play: ship seed 52, 58 stirs → h≈11.8,
# e1=inf). 2.0 keeps a wide stability margin while leaving STIR meaningful.
STIR_H_MAX: float = 2.0

# Bot heuristics
GREEDY_TENSION_THRESHOLD: float = 0.01
