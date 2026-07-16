"""Septacrypt's charts onto umwelt's Bloch atlas (src/umwelt/substrate/bloch.py).

Every real chart in umwelt.substrate.bloch.ATLAS maps ONE domain value to ONE
(x, y, z) Bloch vector and back — e.g. SCALAR_Z (a float), DAY_PHASE (a phase),
EARTH_SPHERE (a lat/lon pair). A single Q3 state (0b000-0b111) is a composite
of 3 independent bits (father/son/spirit), so it does not fit as one chart —
it is 3 charts, one per generator axis, each a bit <-> one Bloch vector.

Bit-to-generator mapping matches geometry/counts.py's PRINCIPLES:
  father = 0b100, son = 0b010, spirit = 0b001
"""
from typing import Tuple

from umwelt.substrate.bloch import Chart

GENERATOR_BITS = {
    "father": 0b100,
    "son": 0b010,
    "spirit": 0b001,
}


def _bit_to_bloch(bit_active: bool) -> Tuple[float, float, float]:
    """1 -> north pole (z=+1), 0 -> south pole (z=-1). No x/y component: a
    classical Q3 basis state carries no coherence of its own (that lives in
    the full 8x8 rho, not in any single collapsed bit)."""
    z = 1.0 if bit_active else -1.0
    return (0.0, 0.0, z)


def _bloch_to_bit(x: float, y: float, z: float) -> bool:
    """Nearest-pole read: z > 0 -> bit set. Ignores x/y (same information
    loss the atlas's own LIGHT_PREFERENCE chart documents for its unused axis)."""
    return z > 0.0


FATHER_CHART = Chart("septacrypt_father", _bit_to_bloch, _bloch_to_bit)
SON_CHART = Chart("septacrypt_son", _bit_to_bloch, _bloch_to_bit)
SPIRIT_CHART = Chart("septacrypt_spirit", _bit_to_bloch, _bloch_to_bit)

# Septacrypt's own atlas, in the same shape as umwelt.substrate.bloch.ATLAS —
# NOT spliced into umwelt's ATLAS tuple (that's their module's own constant;
# we don't mutate a third-party repo's data from here).
SEPTACRYPT_ATLAS: Tuple[Chart, ...] = (FATHER_CHART, SON_CHART, SPIRIT_CHART)

# Order matches SEPTACRYPT_ATLAS above: index 0 = father, 1 = son, 2 = spirit.
_AXIS_ORDER = ("father", "son", "spirit")


def septacrypt_to_bloch(state_mask: int):
    """Embeds a discrete Q3 state (0b000-0b111) into 3 Bloch vectors, ordered
    (father, son, spirit) — i.e. vectors[i] corresponds to _AXIS_ORDER[i]."""
    vectors = []
    for axis in _AXIS_ORDER:
        bit = GENERATOR_BITS[axis]
        vectors.append(_bit_to_bloch(bool(state_mask & bit)))
    return vectors


def bloch_to_septacrypt(bloch_vectors) -> int:
    """Reads 3 Bloch vectors (father, son, spirit order — see septacrypt_to_bloch)
    and collapses them into the nearest Q3 basis state mask."""
    state_mask = 0
    for axis, (x, y, z) in zip(_AXIS_ORDER, bloch_vectors):
        if _bloch_to_bit(x, y, z):
            state_mask |= GENERATOR_BITS[axis]
    return state_mask
