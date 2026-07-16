import random

from ..dynamics.version import MAX_STABLE_DT_SCALE
from ..scenario.campaign import CampaignManager
from ..scenario.params import GREEDY_TENSION_THRESHOLD


class BaseBot:
    def __init__(self, name: str, seed: int | None = None):
        self.name = name
        self.rng = random.Random(seed)

    def play_turn(self, campaign: CampaignManager) -> str:
        raise NotImplementedError


class RandomBot(BaseBot):
    """Spends attention wildly and waits randomly."""

    def play_turn(self, campaign: CampaignManager) -> str:
        quest = campaign.get_active_quest()
        if not quest:
            return "VICTORY"

        api = campaign.api_instances[quest.zone]
        cluster = api.get_cluster()

        action = self.rng.choice(["WAIT", "LOOK"])
        if action == "WAIT":
            api.command_evolve(dt_scale=self.rng.uniform(0.2, MAX_STABLE_DT_SCALE))
            campaign.apply_bridges()
            return "WAIT"
        if campaign.attention_budget >= 1.0:
            campaign.attention_budget -= 1.0
            target = self.rng.choice(list(cluster.qubit_roles))
            api.command_measure(self.name, target)
            campaign.apply_bridges()
            return "LOOK"
        api.command_evolve(dt_scale=MAX_STABLE_DT_SCALE)
        campaign.apply_bridges()
        return "WAIT"


class GreedyTensionBot(BaseBot):
    """Waits until narrative tension is high, then collapses lowest-confidence node."""

    TENSION_THRESHOLD = GREEDY_TENSION_THRESHOLD

    def play_turn(self, campaign: CampaignManager) -> str:
        quest = campaign.get_active_quest()
        if not quest:
            return "VICTORY"

        api = campaign.api_instances[quest.zone]
        state = api.fetch_render_state(self.name)

        if state["meta"]["global_tension"] < self.TENSION_THRESHOLD:
            api.command_evolve(dt_scale=MAX_STABLE_DT_SCALE)
            campaign.apply_bridges()
            return "WAIT"

        if campaign.attention_budget >= 1.0:
            campaign.attention_budget -= 1.0
            entities = state["entities"]
            target = min(entities.keys(), key=lambda k: entities[k]["raw_metrics"]["radius"])
            api.command_measure(self.name, target)
            campaign.apply_bridges()
            return "LOOK"

        api.command_evolve(dt_scale=MAX_STABLE_DT_SCALE)
        campaign.apply_bridges()
        return "WAIT"


class TargetBitBot(BaseBot):
    """Smarter playtester: measure roles whose pole disagrees with quest target bits."""

    def play_turn(self, campaign: CampaignManager) -> str:
        quest = campaign.get_active_quest()
        if not quest:
            return "VICTORY"

        api = campaign.api_instances[quest.zone]
        cluster = api.get_cluster()
        roles = list(cluster.qubit_roles)
        # roles[0]=father bit 0b100, [1]=son 0b010, [2]=spirit 0b001
        bits = [0b100, 0b010, 0b001]
        target = quest.target_state
        disagree = []
        for role, bit in zip(roles, bits):
            z = float(cluster.role_bloch(role)[2])
            want_plus = bool(target & bit)
            is_plus = z > 0
            if want_plus != is_plus:
                disagree.append((role, abs(z)))

        if disagree and campaign.attention_budget >= 1.0:
            # Flip the most wrong (largest |z| on wrong side)
            disagree.sort(key=lambda x: -x[1])
            campaign.attention_budget -= 1.0
            api.command_measure(self.name, disagree[0][0])
            campaign.apply_bridges()
            return "LOOK"

        api.command_evolve(dt_scale=MAX_STABLE_DT_SCALE)
        campaign.apply_bridges()
        return "WAIT"
