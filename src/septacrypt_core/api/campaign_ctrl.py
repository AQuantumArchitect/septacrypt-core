"""Campaign quest controller — progression data only."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..geometry.atlas import bloch_to_septacrypt
from ..narrative.lexicon import LoreLexicon
from ..scenario.params import DEFAULT_QUESTS
from ..world.snapshot import World


class CampaignController:
    def __init__(self, quests: Optional[List[Tuple[str, int]]] = None):
        self.quests: List[Tuple[str, int]] = list(quests) if quests is not None else list(DEFAULT_QUESTS)

    def status(self, world: World) -> List[Dict[str, Any]]:
        out = []
        for zone, target in self.quests:
            if zone not in world.zones:
                continue
            cluster = world.zones[zone]
            mask = bloch_to_septacrypt([cluster.role_bloch(r) for r in cluster.qubit_roles])
            out.append(
                {
                    "zone": zone,
                    "target_mask": target,
                    "target_lore": LoreLexicon.get_state_lore(target),
                    "current_mask": mask,
                    "complete": mask == target,
                }
            )
        return out

    def victory(self, world: World) -> bool:
        st = self.status(world)
        return bool(st) and all(q["complete"] for q in st)
