from typing import Dict, Optional

from ..api.surface import FledgelingKernelAPI
from ..geometry.atlas import bloch_to_septacrypt
from ..narrative.lexicon import LoreLexicon
from .manifold_ship import build_ship_manifold


class Quest:
    def __init__(self, zone: str, target_state_mask: int):
        self.zone = zone
        self.target_state = target_state_mask
        self.target_lore = LoreLexicon.get_state_lore(target_state_mask)

    def is_complete(self, api: FledgelingKernelAPI) -> bool:
        cluster = api.get_cluster()
        bloch_vecs = [cluster.role_bloch(r) for r in cluster.qubit_roles]
        current_mask = bloch_to_septacrypt(bloch_vecs)
        return current_mask == self.target_state


class CampaignManager:
    """Manages the SpaceWeave run across the Manifold Ship."""
    def __init__(self, host, zone_clusters: Optional[Dict] = None):
        zone_clusters = zone_clusters if zone_clusters is not None else build_ship_manifold()
        self.api_instances = {
            zone: FledgelingKernelAPI(host, domain_cluster_name=zone, cluster=cluster)
            for zone, cluster in zone_clusters.items()
        }
        self.attention_budget = 50.0
        self.quests = [
            Quest("Reactor_Core", 0b011),  # Power
            Quest("Navigation", 0b101),    # Glory
            Quest("Life_Support", 0b110),  # Honor
        ]

    def check_victory(self) -> bool:
        return all(q.is_complete(self.api_instances[q.zone]) for q in self.quests)

    def get_active_quest(self) -> Optional[Quest]:
        for q in self.quests:
            if not q.is_complete(self.api_instances[q.zone]):
                return q
        return None
