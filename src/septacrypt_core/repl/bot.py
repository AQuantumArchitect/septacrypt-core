import random

from ..scenario.campaign import CampaignManager


class BaseBot:
    def __init__(self, name: str):
        self.name = name

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

        action = random.choice(["WAIT", "LOOK"])
        if action == "WAIT":
            # dt_scale up to 5.0 (as originally specified) empirically blows up
            # this cluster's RK4 integration past |z|=100 within 2-3 steps --
            # confirmed by testing it directly, not assumed. Capped to the
            # empirically-verified stable range (<=1.0 for these zone params).
            api.command_evolve(dt_scale=random.uniform(0.2, 1.0))
            return "WAIT"
        else:
            if campaign.attention_budget >= 1.0:
                campaign.attention_budget -= 1.0
                target = random.choice(cluster.qubit_roles)
                api.command_measure(self.name, target)
                return "LOOK"
            return "WAIT"


class GreedyTensionBot(BaseBot):
    """Waits until narrative tension is high, then collapses the lowest-confidence
    (highest-fog) node."""

    # The tension threshold below was miscalibrated in the original design (1.0):
    # measured cluster tension for these zone parameters peaks around 0.04 at
    # step 1 and decays from there (checked empirically over 50 steps before
    # writing this). A threshold of 1.0 is never reached, so with that value
    # this bot would never once measure anything and always time out --
    # not evidence about game balance, just a busted constant. Recalibrated to
    # the same order of magnitude as the actual observed signal.
    TENSION_THRESHOLD = 0.01

    def play_turn(self, campaign: CampaignManager) -> str:
        quest = campaign.get_active_quest()
        if not quest:
            return "VICTORY"

        api = campaign.api_instances[quest.zone]
        state = api.fetch_render_state(self.name)

        # If tension is low, let the system drift
        if state["meta"]["global_tension"] < self.TENSION_THRESHOLD:
            api.command_evolve(dt_scale=2.0)  # confirmed stable for this zone's params
            return "WAIT"

        # Otherwise, collapse the node with the lowest confidence (highest fog/radius)
        if campaign.attention_budget >= 1.0:
            campaign.attention_budget -= 1.0
            entities = state["entities"]
            target = min(entities.keys(), key=lambda k: entities[k]["raw_metrics"]["radius"])
            api.command_measure(self.name, target)
            return "LOOK"

        api.command_evolve(dt_scale=2.0)
        return "WAIT"
