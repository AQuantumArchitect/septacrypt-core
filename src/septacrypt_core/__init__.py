"""
septacrypt-core — Fledgeling / Endless Knot quantum-narrative kernel.

Primary handoff for game builders
---------------------------------
    from septacrypt_core import GameSession

    game = GameSession(mode="reactor", seed=42)
    game.wait()
    game.look("player", "valve_17")
    frame = game.status("player")   # JSON-friendly render payload

See GAME_BUILDER.md for the full surface.
"""

from .api.schema import RENDER_SCHEMA_VERSION, validate_render_state
from .api.session import GameSession
from .api.surface import FledgelingKernelAPI
from .dynamics.version import DYNAMICS_VERSION, MAX_STABLE_DT_SCALE
from .geometry.address import ScaleAddress
from .geometry.atlas import bloch_to_septacrypt, septacrypt_to_bloch
from .geometry.counts import PRINCIPLES, STATES, generate_pearls, generate_transitions
from .geometry.emoji import EmojiGrammar
from .geometry.paths import find_q3_paths
from .ledger.dag import KnotLedger
from .narrative.lexicon import LoreLexicon
from .narrative.weaver import EndlessKnotWeaver
from .scenario.campaign import CampaignManager
from .scenario.manifold_ship import build_ship_manifold
from .scenario.reactor import build_entangled_reactor
from .spirit.vector import SpiritVector

__version__ = "0.1.0"

__all__ = [
    "GameSession",
    "FledgelingKernelAPI",
    "CampaignManager",
    "KnotLedger",
    "LoreLexicon",
    "EndlessKnotWeaver",
    "SpiritVector",
    "ScaleAddress",
    "EmojiGrammar",
    "PRINCIPLES",
    "STATES",
    "generate_pearls",
    "generate_transitions",
    "find_q3_paths",
    "bloch_to_septacrypt",
    "septacrypt_to_bloch",
    "build_entangled_reactor",
    "build_ship_manifold",
    "DYNAMICS_VERSION",
    "MAX_STABLE_DT_SCALE",
    "RENDER_SCHEMA_VERSION",
    "validate_render_state",
    "__version__",
]
